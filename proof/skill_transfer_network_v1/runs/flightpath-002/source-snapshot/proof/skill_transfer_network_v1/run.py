"""Flightpath proof coordinator. Credentials stay in private temporary files.

Run with the EVY checkout and lab kubeconfig explicitly supplied. No existing
workloads are changed. Every operation/result is retained in a fresh run folder.
"""
import argparse,datetime,hashlib,io,json,os,secrets,shutil,sqlite3,subprocess,sys,tarfile,time
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec,ed25519
from cryptography.x509.oid import NameOID
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
def raw(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):p.write_bytes(raw(v))
class Proof:
 def __init__(self,args):
  self.args=args;self.out=args.out;self.out.mkdir(parents=True,exist_ok=False)
  self.reg=json.loads((ROOT/'registration.json').read_bytes());self.ns=self.reg['namespace'];self.events=[];self.checks=[]
  self.oc=[args.oc,'--kubeconfig='+str(args.kubeconfig),'--request-timeout=20s']
 def call(self,label,argv,stdin=None,timeout=90,expected=0):
  before=time.monotonic_ns();p=subprocess.run(argv,input=stdin,capture_output=True,timeout=timeout)
  stem=f'{len(self.events)+1:03d}-{label}';(self.out/(stem+'.stdout')).write_bytes(p.stdout);(self.out/(stem+'.stderr')).write_bytes(p.stderr)
  event=dict(label=label,start_monotonic_ns=before,end_monotonic_ns=time.monotonic_ns(),exit_code=p.returncode,stdout=stem+'.stdout',stderr=stem+'.stderr')
  self.events.append(event);save(self.out/'operations.json',self.events)
  if expected is not None and p.returncode!=expected:raise RuntimeError(label+': '+p.stderr.decode(errors='replace')[-500:])
  return p
 def ocall(self,label,args,**kw):return self.call(label,self.oc+args,**kw)
 def py(self,role,label,code,**kw):
  p=self.ocall(label,['-n',self.ns,'exec','-i',role,'--','/work/venv/bin/python','-'],stdin=code.encode(),**kw)
  return json.loads(p.stdout) if p.stdout else None
 def check(self,name,condition,detail=None):
  self.checks.append(dict(name=name,pass_=bool(condition),detail=detail));save(self.out/'checks.json',self.checks)
  if not condition:raise AssertionError(name)
 def upload(self,role,files):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w') as t:
   for name,data in files.items():
    i=tarfile.TarInfo(name);i.size=len(data);i.mode=0o600;t.addfile(i,io.BytesIO(data))
  self.ocall('upload-'+role,['-n',self.ns,'exec','-i',role,'--','tar','-xf','-','-C','/work'],stdin=b.getvalue())
 def rpc(self,label,path,request=None,role='operator',expected=200):
  code=f'''import json,ssl,urllib.request,urllib.error
from pathlib import Path
ctx=ssl.create_default_context(cafile='/work/private/ca.pem')
req=urllib.request.Request('https://localhost:8444'+{path!r},data={raw(request)!r} if {request is not None!r} else None,headers={{'Authorization':'Bearer '+Path('/work/private/{role}').read_text().strip(),'Content-Type':'application/json'}})
try:
 with urllib.request.urlopen(req,context=ctx,timeout=10) as r: value={{'status':r.status,'body':json.loads(r.read())}}
except urllib.error.HTTPError as e:value={{'status':e.code,'body':json.loads(e.read())}}
print(json.dumps(value))
'''
  value=self.py('central',label,code);self.check(label+'-http',value['status']==expected,value);return value['body']
 def rust(self,label,command,arg=None,expected=0):
  code=f'''import subprocess,json
p=subprocess.run(['/work/input/repo/crates/aeris-skill-transfer/target/release/aeris-skill-transfer','/work/private/rust.json','/work/state/rust.sqlite',{command!r}]+{[arg] if arg is not None else []!r},capture_output=True,text=True,timeout=30)
print(json.dumps({{'exit_code':p.returncode,'lines':[json.loads(s) for s in p.stdout.splitlines()],'stderr':p.stderr}}))
'''
  value=self.py('edge',label,code);self.check(label+'-exit',value['exit_code']==expected,value);return value['lines'][-1]
 def edge_progress(self,label,action):
  return self.py('edge',label,f'''import sqlite3,json
with sqlite3.connect('/work/state/rust.sqlite') as db:
 row=db.execute('SELECT status FROM tasks WHERE id=?',('action-'+{action!r},)).fetchone()
 count=db.execute('SELECT count(*) FROM samples WHERE task=?',('action-'+{action!r},)).fetchone()[0]
with sqlite3.connect('/work/state/inbox.sqlite') as db: job=db.execute('SELECT state,pid FROM jobs WHERE id=?',({action!r},)).fetchone()
print(json.dumps({{'task_status':row[0] if row else None,'ticks':count,'job_state':job[0],'pid':job[1]}}))
''')
 def wait_progress(self,action,min_ticks):
  deadline=time.monotonic()+30
  while time.monotonic()<deadline:
   value=self.edge_progress('progress-'+action,action)
   if value['task_status']=='RUNNING' and value['ticks']>=min_ticks:return value
   if value['task_status']in ('COMPLETE','FAILED','INTERRUPTED'):raise AssertionError('Task ended before fault: '+str(value))
   time.sleep(.1)
  raise TimeoutError('No moving progress')
 def wait_terminal(self,action):
  deadline=time.monotonic()+100
  while time.monotonic()<deadline:
   value=self.rpc('poll-'+action,'/actions/capability-transfer/'+action)
   if value['state']in ['COMPLETE','FAILED','INTERRUPTED']:return value
   time.sleep(.2)
  raise TimeoutError('Action terminal')
 def start(self,role,kind):
  settings={
   'publisher':(['/work/venv/bin/python','/work/input/repo/proof/skill_transfer_network_v1/publisher.py','--private','/work/private'],None),
   'evy':(['/work/venv/bin/python','-m','uvicorn','backend.api_gateway.main:app','--host','0.0.0.0','--port','8444','--ssl-certfile','/work/private/central-cert.pem','--ssl-keyfile','/work/private/central-key.pem'],'/work/input/evy'),
   'gateway':(['/work/venv/bin/python','/work/input/repo/proof/skill_transfer_network_v1/gateway.py','--config','/work/private/gateway.json'],None)}
  argv,cwd=settings[kind]
  self.py(role,'start-'+kind,f'''import subprocess,os,json
from pathlib import Path
Path('/work/evidence').mkdir(exist_ok=True)
env=dict(os.environ,EVY_ACTION_CONFIG='/work/private/evy.json',MUJOCO_GL='disable',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
with open('/work/evidence/{kind}.log','ab') as out:
 p=subprocess.Popen({argv!r},cwd={cwd!r},env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
Path('/work/private/{kind}.pid').write_text(str(p.pid));print(json.dumps({{'pid':p.pid}}))
''')
 def prepare(self):
  for role in ['central','edge']:
   self.upload(role,{'input/repo/proof/skill_transfer_network_v1/'+p.name:p.read_bytes() for p in ROOT.iterdir() if p.suffix in ['.py','.sh']})
  source_files=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ['.py','.sh','.json']]
  source_files += [p for base in ['crates/aeris-skill-transfer','proof/control_v2/controller','proof/control/assets/ur5e'] for p in (REPO/base).rglob('*') if p.is_file() and 'target' not in p.parts]
  source_files += [REPO/x for x in ['Cargo.lock','proof/skill_transfer_v2/simulator.py','proof/skill_transfer_v2/audit.py','proof/control_v2/run_control.py','proof/control_v2/preregistration.json','proof/control_v2/scene.xml']]
  for p in source_files:
   destination=self.out/'source-snapshot'/p.relative_to(REPO);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
  for p in (self.args.evy/'backend').rglob('*.py'):
   if '__pycache__'in p.parts:continue
   destination=self.out/'source-snapshot/evy'/p.relative_to(self.args.evy);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
  save(self.out/'local-source-freeze.json',{'before_execution_unix_ns':time.time_ns(),'files':{str(p.relative_to(REPO)):sha(p.read_bytes()) for p in source_files}})
  pods=json.loads(self.ocall('pods',['-n',self.ns,'get','pods','-o','json']).stdout)
  nodes=json.loads(self.ocall('nodes',['get','nodes','-o','json']).stdout)
  self.hosts={}
  for role in ['central','edge']:
   pod=next(p for p in pods['items'] if p['metadata']['name']==role);node=next(n for n in nodes['items'] if n['metadata']['name']==pod['spec']['nodeName'])
   identity=self.py(role,'identity-'+role,"""import json,platform,os,hashlib
from pathlib import Path
cpu=Path('/proc/cpuinfo').read_text();p=Path('/work/venv/bin/python').resolve()
print(json.dumps({'machine':platform.machine(),'os_release':Path('/etc/os-release').read_text(),'cpu_vendor':next(s.split(':',1)[1].strip() for s in cpu.splitlines() if s.startswith('vendor_id')),'cpu_model':next(s.split(':',1)[1].strip() for s in cpu.splitlines() if s.startswith('model name')),'python':str(p),'python_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'uid':os.getuid(),'python_freeze':Path('/work/python-freeze.txt').read_text(),'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text()}))
""")
   self.hosts[role]={'node':node['metadata']['name'],'node_uid':node['metadata']['uid'],'system_uuid':node['status']['nodeInfo']['systemUUID'],'node_info':node['status']['nodeInfo'],'pod_uid':pod['metadata']['uid'],'pod_ip':pod['status']['podIP'],'image_id':pod['status']['containerStatuses'][0]['imageID'],'observed':identity}
  save(self.out/'hosts.json',self.hosts)
  self.check('separate-intel-redhat-hosts',self.hosts['central']['node_uid']!=self.hosts['edge']['node_uid'] and self.hosts['central']['system_uuid']!=self.hosts['edge']['system_uuid'] and all(h['observed']['cpu_vendor']=='GenuineIntel' and 'ID="rhel"'in h['observed']['os_release'] and 'Red Hat Enterprise Linux CoreOS'in h['node_info']['osImage'] for h in self.hosts.values()))
  target=self.py('edge','plant-identity',"""import sys,json,hashlib,mujoco
from pathlib import Path
sys.path.insert(0,'/work/input/repo/proof/skill_transfer_v2');import simulator
print(json.dumps({'plant_sha256':simulator.plant_identity()[0],'inventory':simulator.plant_identity()[1],'joint_names':simulator.JOINTS,'runtime_version':mujoco.__version__,'adapter_sha256':hashlib.sha256(Path(simulator.__file__).read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(Path('/work/input/repo/crates/aeris-skill-transfer/target/release/aeris-skill-transfer').read_bytes()).hexdigest()}))
""")
  save(self.out/'plant-identity.json',target)
  inventory=target.pop('inventory');binary_sha=target.pop('binary_sha256')
  target.update(profile='mujoco-six-axis-goals-v1',calibration_sha256=sha(b'ideal MuJoCo joints; no physical calibration'),units='rad',frame='world-base',runtime='mujoco-rust-mpc-v1',host_arch='x86_64',host_os='linux')
  now=datetime.datetime.now(datetime.timezone.utc);cakey=ec.generate_private_key(ec.SECP256R1());name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'AERIS separate-host ephemeral CA')])
  ca=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(cakey.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True,path_length=0),True).add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),True).sign(cakey,hashes.SHA256())
  common={'private/ca.pem':ca.public_bytes(serialization.Encoding.PEM),'private/ca.der':ca.public_bytes(serialization.Encoding.DER)}
  (self.out/'app-ca.der').write_bytes(common['private/ca.der'])
  import ipaddress
  for role in ['central','edge']:
   key=ec.generate_private_key(ec.SECP256R1())
   leaf=x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,role)])).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address(self.hosts[role]['pod_ip']))]),False).add_extension(x509.BasicConstraints(ca=False,path_length=None),True).sign(cakey,hashes.SHA256())
   common['private/'+role+'-cert.pem']=leaf.public_bytes(serialization.Encoding.PEM);common['private/'+role+'-key.pem']=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
  tokens={k:secrets.token_hex(32).encode() for k in ['operator','viewer','edge-token','publisher-token']}
  signer=ed25519.Ed25519PrivateKey.generate();pub=signer.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()
  home=[-1.5708,-1.5708,1.5708,-1.5708,-1.5708,0.];self.bundles={};approved=[]
  for seq,skill,goals in [(1,'inspection-positioning',[[home[0]+delta,*home[1:]] for delta in [.28,-.28,.28,-.28]]),(2,'rework-positioning',[[h+sign*x for h,x in zip(home,[.12,-.08,.06,.03,-.04,.02])] for sign in [1,-1,1,-1]])]:
   behavior=raw({'schema':'aeris.bounded-joint-goals.v1','goals':goals}).decode();ms=time.time_ns()//1000000
   manifest=dict(schema='evy-aeris.transfer-release.v2',release_id='network-release-'+str(seq),skill_id=skill,sequence=seq,issued_at_ms=ms-1000,not_before_ms=ms-500,expires_at_ms=ms+3600000,origin='existing_deterministic_behavior',target=target,behavior_sha256=sha(behavior.encode()),behavior_size=len(behavior.encode()),recovery_of=None)
   text=raw(manifest);digest=sha(text);approved.append(digest)
   bundle={'schema':'evy-aeris.transfer-bundle.v2','manifest_json':text.decode(),'signature_hex':signer.sign(b'evy-aeris.transfer-release.v2\0'+text).hex(),'behavior_json':behavior}
   self.bundles[skill]={'digest':digest,'bundle':bundle};save(self.out/(skill+'.bundle.json'),bundle)
  central=f"https://{self.hosts['central']['pod_ip']}:9443/release";edge=f"https://{self.hosts['edge']['pod_ip']}:8443"
  rust={'schema':'evy-aeris.edge-config.v2','publisher_url':central,'ca_der_path':'/work/private/ca.der','bearer_file':'/work/private/publisher-token','publisher_public_hex':pub,'approved_manifests':approved,'target':target,'python':'/work/venv/bin/python','python_sha256':self.hosts['edge']['observed']['python_sha256'],'adapter':'/work/input/repo/proof/skill_transfer_v2/simulator.py'}
  save(self.out/'rust-config-public.json',rust)
  gateway=dict(edge_id='flightpath-cell',inbox='/work/state/inbox.sqlite',work='/work/evidence',binary='/work/input/repo/crates/aeris-skill-transfer/target/release/aeris-skill-transfer',binary_sha256=binary_sha,rust_config='/work/private/rust.json',rust_config_sha256=sha(raw(rust)),rust_database='/work/state/rust.sqlite',token_file='/work/private/edge-token',certificate='/work/private/edge-cert.pem',private_key='/work/private/edge-key.pem',allowed_skills=list(self.bundles))
  evy=dict(schema='evy.capability-actions.config.v1',database='/work/state/evy.sqlite',operator_token_file='/work/private/operator',viewer_token_file='/work/private/viewer',targets=[dict(id='flightpath-cell',base_url=edge,ca_file='/work/private/ca.pem',token_file='/work/private/edge-token',profile='mujoco-six-axis-goals-v1',allowed_skills=list(self.bundles),simulation_only=True)])
  for role in ['central','edge']:
   self.py(role,'mkdir-'+role,"from pathlib import Path\nfor d in ['private','state','evidence']:Path('/work/'+d).mkdir(exist_ok=True,mode=0o700)\n")
   files={'private/ca.pem':common['private/ca.pem'],'private/ca.der':common['private/ca.der'],'private/'+role+'-cert.pem':common['private/'+role+'-cert.pem'],'private/'+role+'-key.pem':common['private/'+role+'-key.pem']}
   if role=='central':
    files.update({'private/'+k:v for k,v in tokens.items()});files['private/evy.json']=raw(evy);files['private/publication.json']=raw({'bundle':'inspection-positioning.bundle.json'})
    for skill,b in self.bundles.items():files['private/'+skill+'.bundle.json']=raw(b['bundle'])
   else:
    files.update({'private/'+k:tokens[k] for k in ['edge-token','publisher-token']});files['private/rust.json']=raw(rust);files['private/gateway.json']=raw(gateway)
   self.upload(role,files)
  # Freeze deployed byte identities before any network action execution.
  snapshot={}
  for role in ['central','edge']:
   snapshot[role]=self.py(role,'source-identity-'+role,"""from pathlib import Path
import hashlib,json
files=[p for base in ['/work/input/repo/crates/aeris-skill-transfer/src','/work/input/repo/proof/control_v2/controller/src','/work/input/repo/proof/skill_transfer_network_v1','/work/input/evy/backend/actions'] for p in Path(base).rglob('*.py' if 'controller'not in base and 'crates'not in base else '*.rs')]
files += [Path('/work/input/repo/proof/skill_transfer_v2/simulator.py'),Path('/work/input/repo/crates/aeris-skill-transfer/Cargo.lock'),Path('/work/input/evy/backend/api_gateway/main.py')]
print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}))
""")
  save(self.out/'deployed-source-freeze.json',dict(before_execution_unix_ns=time.time_ns(),files=snapshot,binary_sha256=binary_sha))
  self.start('central','publisher');self.start('edge','gateway');self.start('central','evy');time.sleep(1)
 def intent(self,action,skill='inspection-positioning',**updates):return dict(schema='evy.capability-action.v1',action_id=action,edge_id='flightpath-cell',skill_id=skill,release_digest=self.bundles[skill]['digest'],**updates)
 def exercise(self):
  self.rpc('catalog','/actions/catalog')
  self.rpc('viewer-submit-refused','/actions/capability-transfer',self.intent('viewer-refused'),role='viewer',expected=403)
  self.rpc('remote-authority-field-refused','/actions/capability-transfer',{**self.intent('extra-field'),'command':'sh'},expected=422)
  self.rpc('unregistered-edge-refused','/actions/capability-transfer',{**self.intent('bad-edge'),'edge_id':'unknown'},expected=422)
  first=self.intent('inspection-disconnected')
  self.rpc('submit-inspection','/actions/capability-transfer',first,expected=202)
  before=self.wait_progress(first['action_id'],5)
  partition={'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':{'name':'central-disconnection','namespace':self.ns},'spec':{'podSelector':{'matchLabels':{'aeris-proof-role':'central'}},'policyTypes':['Ingress','Egress'],'ingress':[],'egress':[]}}
  save(self.out/'disconnection-networkpolicy.json',partition)
  self.ocall('isolate-central-network',['create','-f','-','-o','json'],stdin=raw(partition))
  probe=self.py('edge','disconnected-publisher-probe',f'''import urllib.request,ssl,json
try:
 urllib.request.urlopen({self.hosts['central']['pod_ip']!r}.join(['https://',':9443/release']),context=ssl.create_default_context(cafile='/work/private/ca.pem'),timeout=2)
 print(json.dumps({{'reachable':True}}))
except urllib.error.HTTPError as e:print(json.dumps({{'reachable':True,'status':e.code}}))
except Exception as e:print(json.dumps({{'reachable':False,'error':type(e).__name__}}))
''')
  after=self.edge_progress('control-after-disconnection',first['action_id'])
  self.check('central-unreachable-during-edge-control',not probe['reachable'] and after['task_status']=='RUNNING' and after['ticks']>before['ticks'],dict(before=before,after=after,probe=probe))
  # Observe completion locally while central remains isolated; no cross-host clock comparison.
  deadline=time.monotonic()+100
  while time.monotonic()<deadline:
   final=self.edge_progress('isolated-edge-progress',first['action_id'])
   if final['job_state']in ['COMPLETE','FAILED']:break
   time.sleep(.3)
  self.check('isolated-edge-completes',final['job_state']=='COMPLETE',final)
  self.rpc('central-to-edge-blocked','/actions/capability-transfer/'+first['action_id'],expected=502)
  self.ocall('restore-central-network',['-n',self.ns,'delete','networkpolicy','central-disconnection','--wait=true'])
  result=self.wait_terminal(first['action_id']);self.check('evy-observes-completion-after-reconnect',result['state']=='COMPLETE')
  previous=self.rust('before-idempotent-retry','status')
  retry=self.rpc('terminal-action-retry','/actions/capability-transfer',first,expected=202)
  self.check('terminal-retry-complete',retry['state']=='COMPLETE')
  self.check('terminal-retry-does-not-execute',self.rust('after-idempotent-retry','status')==previous)
  self.rpc('changed-action-id-binding-refused','/actions/capability-transfer',{**first,'release_digest':'0'*64},expected=409)
  # Restart only the gateway, keeping Rust state and its terminal inbox durable.
  self.py('edge','stop-gateway',"import os,signal\nfrom pathlib import Path\nos.kill(int(Path('/work/private/gateway.pid').read_text()),signal.SIGTERM)\n")
  time.sleep(.2);self.start('edge','gateway');time.sleep(.3)
  restarted=self.rpc('terminal-after-gateway-restart','/actions/capability-transfer',first,expected=202)
  self.check('gateway-restart-no-replay',restarted['state']=='COMPLETE' and self.rust('after-gateway-restart','status')==previous)
  self.py('central','publish-rework',"from pathlib import Path\nPath('/work/private/publication.json').write_text('{\"bundle\":\"rework-positioning.bundle.json\"}')\n")
  # A mismatched expected release must fail before Rust stages the candidate.
  wrong={**self.intent('wrong-release','rework-positioning'),'release_digest':'0'*64}
  self.rpc('submit-wrong-release','/actions/capability-transfer',wrong,expected=202)
  refusal=self.wait_terminal('wrong-release');self.check('wrong-release-failed',refusal['state']=='FAILED')
  self.check('wrong-release-preserves-rust-state',self.rust('after-wrong-release','status')==previous)
  crash=self.intent('rework-interrupted','rework-positioning')
  self.rpc('submit-interrupted-rework','/actions/capability-transfer',crash,expected=202)
  death=self.py('edge','kill-moving-rust-executor',f'''import os,signal,json,sqlite3,time
from pathlib import Path
deadline=time.monotonic()+20
while time.monotonic()<deadline:
 with sqlite3.connect('/work/state/rust.sqlite') as db:
  row=db.execute('SELECT status FROM tasks WHERE id=?',('action-'+{crash['action_id']!r},)).fetchone()
  ticks=db.execute('SELECT count(*) FROM samples WHERE task=?',('action-'+{crash['action_id']!r},)).fetchone()[0]
 with sqlite3.connect('/work/state/inbox.sqlite') as db:job=db.execute('SELECT state,pid FROM jobs WHERE id=?',({crash['action_id']!r},)).fetchone()
 if row and row[0]=='RUNNING' and ticks>=15:
  pid=job[1];command=Path('/proc/'+str(pid)+'/cmdline').read_bytes().split(bytes([0]))
  assert command[0].decode()=='/work/input/repo/crates/aeris-skill-transfer/target/release/aeris-skill-transfer'
  os.kill(pid,signal.SIGKILL)
  print(json.dumps({{'pid':pid,'signal':'SIGKILL','command_verified':True,'ticks':ticks,'task_status':row[0],'job_state':job[0]}}));break
 if row and row[0]!='RUNNING':raise RuntimeError('Task completed before fault window')
 time.sleep(.02)
else:raise TimeoutError('No moving executor')
''')
  moving=death
  failed=self.wait_terminal(crash['action_id']);self.check('executor-death-never-completes',failed['state']=='FAILED')
  self.rust('new-motion-before-recovery-refused','execute','unsafe-automatic-retry',expected=2)
  recovery=self.rust('explicit-local-rust-recovery','recover');self.check('one-explicitly-interrupted-task',recovery['interrupted_tasks']==1)
  self.rust('interrupted-task-receipt','receipt','action-'+crash['action_id'])
  fresh=self.intent('rework-recovered','rework-positioning')
  self.rpc('submit-fresh-after-recovery','/actions/capability-transfer',fresh,expected=202)
  done=self.wait_terminal(fresh['action_id']);self.check('second-capability-same-remote-process',done['state']=='COMPLETE')
  # The original failed action remains terminal even after recovery.
  retained=self.rpc('interrupted-action-not-replayed','/actions/capability-transfer',crash,expected=202)
  self.check('explicit-new-action-required',retained['state']=='FAILED')
  save(self.out/'scenario.json',{'first_action':first,'interrupted_action':crash,'recovered_action':fresh,'moving_before_kill':moving,'death':death,'disconnection_before':before,'disconnection_after':after,'isolated_completion':final})
 def collect(self):
  for role in ['central','edge']:
   self.py(role,'sqlite-snapshot-'+role,f'''from pathlib import Path
import sqlite3
for name in {['evy'] if role=='central' else ['rust','inbox']!r}:
 source=sqlite3.connect('/work/state/'+name+'.sqlite');target=sqlite3.connect('/work/evidence/'+name+'.snapshot')
 source.backup(target);target.execute('PRAGMA journal_mode=DELETE');target.close();source.close()
''')
   p=self.ocall('export-evidence-'+role,['-n',self.ns,'exec',role,'--','tar','-czf','-','-C','/work','evidence','python-freeze.txt','python-install.log','python-bootstrap.log','offline-python-install.log','offline-python-bootstrap.log']+(['build-log','build-bootstrap.log'] if role=='edge' else []),expected=None)
   # tar returns 2 if a first-attempt log is absent; retain archive and stderr.
   (self.out/(role+'-evidence.tar.gz')).write_bytes(p.stdout)
   with tarfile.open(fileobj=io.BytesIO(p.stdout),mode='r:gz') as tar:
    dest=self.out/role;dest.mkdir(exist_ok=True)
    for member in tar.getmembers():
     path=Path(member.name)
     if path.is_absolute() or '..'in path.parts or not (member.isfile() or member.isdir()):raise ValueError('Unsafe export')
     if member.isfile():
      target=dest/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(tar.extractfile(member).read())
  p=self.ocall('export-linux-binary',['-n',self.ns,'exec','edge','--','cat','/work/input/repo/crates/aeris-skill-transfer/target/release/aeris-skill-transfer'])
  (self.out/'executor-linux.bin').write_bytes(p.stdout)
 def run(self):
  result=dict(schema='evy-aeris.network-proof.v1',status='FAIL',simulation_only=True,physical_motion_authorized=False,started_unix_ns=time.time_ns(),namespace=self.ns)
  try:
   self.prepare();self.exercise();self.collect();result.update(status='PASS_SCENARIOS_PENDING_AUDIT',checks=len(self.checks),passed=sum(c['pass_'] for c in self.checks))
  except Exception as e:
   result['error']=type(e).__name__+': '+str(e)
   try:self.collect()
   except Exception as collection_error:result['collection_error']=str(collection_error)
   raise
  finally:
   result['ended_unix_ns']=time.time_ns();save(self.out/'result.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--oc',default='/Users/jkershaw/bin/oc');ap.add_argument('--kubeconfig',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--evy',type=Path,required=True);args=ap.parse_args();Proof(args).run()
