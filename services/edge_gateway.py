"""Network adapter around the qualified Rust action; lab controls are simulator-only."""
import argparse,fcntl,hashlib,hmac,http.server,json,os,signal,sqlite3,ssl,subprocess,threading,time,urllib.request,urllib.error
from pathlib import Path
from proof.skill_transfer_network_v1.gateway import Inbox,worker,encoded,parse,ID
from services.action_console.contracts import control,lab_authority,need
class Edge:
 def __init__(self,cfg,config_bytes):
  self.cfg=cfg;self.rust=json.loads(Path(cfg['rust_config']).read_bytes());self.inbox=Inbox(cfg['inbox'],cfg['edge_id'],hashlib.sha256(config_bytes).hexdigest());self.lock=threading.Lock()
  if cfg.get('lab_controls'):lab_authority({**cfg,'profile':self.rust['target']['profile']})
  with self.inbox.db() as db:db.execute('CREATE TABLE IF NOT EXISTS lab_commands(id TEXT PRIMARY KEY,request TEXT NOT NULL,result TEXT)')
 def cell(self):
  with self.inbox.db() as db:
   jobs=[dict(action_id=i,state=s,pid=p) for i,s,p in db.execute('SELECT id,state,pid FROM jobs ORDER BY rowid DESC LIMIT 16')]
  path=Path(self.cfg['rust_database']);tasks=[];floor=0;active=None;releases=[];latest=None
  if path.exists():
   with sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True,timeout=3) as db:
    db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
    floor,active=db.execute('SELECT floor,active FROM meta WHERE id=1').fetchone()
    releases=[{'digest':d,'sequence':s,'skill_id':json.loads(json.loads(b)['manifest_json'])['skill_id']} for d,s,b in db.execute('SELECT digest,sequence,bundle FROM releases')]
    for task,digest,status,receipt in db.execute('SELECT id,release_digest,status,receipt FROM tasks ORDER BY rowid DESC LIMIT 16'):
     count=db.execute('SELECT count(*) FROM samples WHERE task=?',(task,)).fetchone()[0];last=db.execute('SELECT payload FROM samples WHERE task=? ORDER BY tick DESC LIMIT 1',(task,)).fetchone()
     tasks.append(dict(task=task,release_digest=digest,status=status,ticks=count,last_sample=json.loads(last[0]) if last else None,receipt=json.loads(receipt) if receipt else None))
  import platform
  cpu=Path('/proc/cpuinfo').read_text() if Path('/proc/cpuinfo').exists() else ''
  def field(name):return next((s.split(':',1)[1].strip() for s in cpu.splitlines() if s.startswith(name)),None)
  orphan=any(t['status']=='RUNNING' and not any(j['action_id']=='{}'.format(t['task'].removeprefix('action-')) and j['state']=='RUNNING' for j in jobs) for t in tasks)
  return dict(schema='aeris.edge-cell.v1',source='SIMULATOR_OBSERVED',edge_id=self.cfg['edge_id'],simulation_only=True,physical_motion_authorized=False,profile=self.rust['target']['profile'],observed_at_ms=time.time_ns()//1000000,sequence_floor=floor,active_digest=active,releases=releases,tasks=tasks,jobs=[{k:v for k,v in j.items() if k!='pid'} for j in jobs],recovery_required=orphan,host={'system':platform.system(),'architecture':platform.machine(),'cpu_vendor':field('vendor_id'),'cpu_model':field('model name'),'os_release':Path('/etc/os-release').read_text() if Path('/etc/os-release').exists() else platform.platform()})
 def command(self,operation,request):
  lab_authority({**self.cfg,'profile':self.rust['target']['profile']});request=control(encoded(request).encode());text=encoded({'operation':operation,**request})
  with self.lock:
   with self.inbox.db() as db:
    db.execute('BEGIN IMMEDIATE');old=db.execute('SELECT request,result FROM lab_commands WHERE id=?',(request['command_id'],)).fetchone()
    if old:
     need(old[0]==text,'COMMAND_ID_REUSED');return json.loads(old[1]) if old[1] else {'status':'UNCERTAIN','reason':'Observe and reconcile; command will not be repeated automatically.'}
    need(operation in ['interrupt','recover'],'CONTROL_NOT_ALLOWED')
    job=self.inbox.get(request['action_id']);cell=self.cell()
    if operation=='interrupt':
     need(job['state']=='RUNNING' and job['worker_pid'],'EXECUTOR_NOT_RUNNING')
     task=next((t for t in cell['tasks'] if t['task']=='action-'+request['action_id']),None);need(task and task['status']=='RUNNING' and task['ticks']>=15,'MOVING_OBSERVATION_REQUIRED')
    else:
     need(cell['recovery_required'],'NO_ORPHANED_TASK')
     need(any(t['task']=='action-'+request['action_id'] and t['status']=='RUNNING' for t in cell['tasks']),'RECOVERY_ACTION_MISMATCH')
    db.execute('INSERT INTO lab_commands VALUES(?,?,NULL)',(request['command_id'],text))
   # The intent is durable before a process-side effect. Unknown acknowledgement
   # never authorizes repeating it or restarting a simulator task.
   need(hashlib.sha256(Path(self.cfg['binary']).read_bytes()).hexdigest()==self.cfg['binary_sha256'],'BINARY_CHANGED')
   need(hashlib.sha256(Path(self.cfg['rust_config']).read_bytes()).hexdigest()==self.cfg['rust_config_sha256'],'RUST_AUTHORITY_CHANGED')
   if operation=='interrupt':
    pid=job['worker_pid']
    if Path('/proc').exists():
     argv=Path('/proc/'+str(pid)+'/cmdline').read_bytes().split(b'\0');need(argv[0].decode()==self.cfg['binary'] and argv[3:4]==[b'action'] and argv[4:5]==[str(Path(self.cfg['work'])/(request['action_id']+'.request.json')).encode()],'PROCESS_IDENTITY_CHANGED')
    else:
     cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True);need(cmd.startswith(self.cfg['binary']+' ') and ' action 'in cmd and str(Path(self.cfg['work'])/(request['action_id']+'.request.json'))in cmd,'PROCESS_IDENTITY_CHANGED')
    os.kill(pid,signal.SIGKILL);result=dict(status='SIGNALLED',signal='SIGKILL',observed_ticks=task['ticks'])
   else:
    p=subprocess.run([self.cfg['binary'],self.cfg['rust_config'],self.cfg['rust_database'],'recover'],capture_output=True,timeout=10)
    value=json.loads(p.stdout.splitlines()[-1]);need(p.returncode==0 and value['status']=='RECOVERED','RUST_RECOVERY_REFUSED');result=value
   result.update(schema='aeris.lab-result.v1',operation=operation,command_id=request['command_id'],action_id=request['action_id'],simulation_only=True,physical_motion_authorized=False)
   with self.inbox.db() as db:db.execute('UPDATE lab_commands SET result=? WHERE id=?',(encoded(result),request['command_id']))
   return result
 def probe(self):
  ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
  from cryptography import x509
  from cryptography.hazmat.primitives import serialization
  ca=x509.load_der_x509_certificate(Path(self.rust['ca_der_path']).read_bytes());ctx.load_verify_locations(cadata=ca.public_bytes(serialization.Encoding.PEM).decode())
  try:
   with urllib.request.urlopen(self.rust['publisher_url'],context=ctx,timeout=2) as r:return {'reachable':True,'status':r.status}
  except urllib.error.HTTPError as e:return {'reachable':True,'status':e.code}
  except (OSError,urllib.error.URLError) as e:return {'reachable':False,'error':type(e).__name__}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);args=ap.parse_args();raw=args.config.read_bytes();cfg=json.loads(raw)
 lock=open(cfg['inbox']+'.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);edge=Edge(cfg,raw)
 token=Path(cfg['token_file']).read_bytes().strip();lab=Path(cfg['lab_token_file']).read_bytes().strip() if cfg.get('lab_controls') else None
 need(len(token)>=32 and (lab is None or len(lab)>=32),'TOKEN_CONFIG')
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def reply(self,status,value):
   data=encoded(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
  def authorized(self,secret):return secret is not None and hmac.compare_digest(self.headers.get('Authorization','').encode(),b'Bearer '+secret)
  def body(self):
   need(not self.headers.get('Transfer-Encoding'),'TRANSFER_ENCODING');n=int(self.headers.get('Content-Length','-1'));need(0<=n<=4096,'BODY_LIMIT');return self.rfile.read(n)
  def do_GET(self):
   self.connection.settimeout(5)
   if not self.authorized(token):self.reply(403,{'error':'AUTH_REQUIRED'});return
   try:
    if self.path=='/v1/cell':self.reply(200,edge.cell())
    elif self.path=='/v1/connectivity':self.reply(200,{'schema':'aeris.connectivity-observation.v1',**edge.probe()})
    elif self.path.startswith('/v1/actions/'):self.reply(200,edge.inbox.get(self.path.removeprefix('/v1/actions/')))
    else:self.reply(404,{'error':'NOT_FOUND'})
   except (ValueError,KeyError):self.reply(404,{'error':'NOT_FOUND'})
  def do_POST(self):
   self.connection.settimeout(5);is_lab=self.path.startswith('/v1/lab/')
   if not self.authorized(lab if is_lab else token):self.reply(403,{'error':'AUTH_REQUIRED'});return
   try:
    if is_lab:
     need(self.path in ['/v1/lab/interrupt','/v1/lab/recover'],'CONTROL_NOT_ALLOWED');request=control(self.body());self.reply(200,edge.command(self.path.rsplit('/',1)[1],request))
    elif self.path=='/v1/actions':
     request=parse(self.body());need(request['skill_id']in cfg['allowed_skills'],'SKILL_NOT_ENABLED');self.reply(202,edge.inbox.submit(request))
    else:self.reply(404,{'error':'NOT_FOUND'})
   except (ValueError,KeyError):self.reply(409,{'error':'CONTROL_OR_ACTION_REJECTED'})
   except (OSError,subprocess.SubprocessError):self.reply(409,{'error':'OBSERVE_AND_RECONCILE'})
 def stop_owned_executor(signum,frame):
  # A service stop must not leave a simulator executor running invisibly.
  # Its durable Rust task remains uncertain until explicit recovery.
  with edge.inbox.db() as db:running=db.execute("SELECT id,pid FROM jobs WHERE state='RUNNING'").fetchall()
  for action_id,pid in running:
   if not pid:continue
   try:
    if Path('/proc').exists():cmd=Path('/proc/'+str(pid)+'/cmdline').read_bytes().replace(bytes([0]),b' ').decode()
    else:cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True)
    if cmd.startswith(cfg['binary']+' ') and str(Path(cfg['work'])/(action_id+'.request.json'))in cmd:os.kill(pid,signal.SIGTERM)
   except (OSError,subprocess.SubprocessError):pass
  raise SystemExit(0)
 signal.signal(signal.SIGTERM,stop_owned_executor);signal.signal(signal.SIGINT,stop_owned_executor)
 ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(cfg['certificate'],cfg['private_key'])
 server=http.server.ThreadingHTTPServer((cfg.get('bind','127.0.0.1'),cfg.get('port',28445)),Handler);server.daemon_threads=True;server.socket=ctx.wrap_socket(server.socket,server_side=True)
 threading.Thread(target=worker,args=(edge.inbox,cfg),daemon=True).start();print(encoded({'event':'EDGE_READY','profile':'mujoco-six-axis-goals-v1','simulation_only':True}),flush=True);server.serve_forever()
if __name__=='__main__':main()
