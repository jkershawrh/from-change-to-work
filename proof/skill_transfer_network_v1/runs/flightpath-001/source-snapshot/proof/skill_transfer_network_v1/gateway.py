"""Reference HTTPS durable inbox. Rust owns verification, activation and execution.

Trusted operator configuration only; this transport adapter never approves a
release or installs executable code. Its inbox is not a motion safety controller.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import hmac
import http.server
import json
from pathlib import Path
import re
import sqlite3
import ssl
import subprocess
import threading
import time

ID=re.compile(r'[A-Za-z0-9_.-]{1,80}\Z')
DIGEST=re.compile(r'[a-f0-9]{64}\Z')
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def pairs(values):
 result={}
 for k,v in values:
  if k in result:raise ValueError('DUPLICATE_FIELD')
  result[k]=v
 return result
def parse(raw):
 if len(raw)>4096:raise ValueError('BODY_LIMIT')
 r=json.loads(raw,object_pairs_hook=pairs)
 if type(r)is not dict or set(r)!={'schema','action_id','skill_id','release_digest'}:raise ValueError('ACTION_FIELDS')
 if r['schema']!='evy-aeris.transfer-action.v1':raise ValueError('ACTION_SCHEMA')
 if not all(type(r[k])is str and ID.fullmatch(r[k]) for k in ['action_id','skill_id']):raise ValueError('ACTION_IDENTITY')
 if type(r['release_digest'])is not str or not DIGEST.fullmatch(r['release_digest']):raise ValueError('DIGEST')
 return r
class Inbox:
 def __init__(self,path,edge_id,config_sha):
  self.path=path;self.edge_id=edge_id
  with self.db() as db:
   db.execute('PRAGMA journal_mode=WAL')
   db.execute('CREATE TABLE IF NOT EXISTS authority(id INTEGER PRIMARY KEY,sha TEXT NOT NULL)')
   db.execute('INSERT OR IGNORE INTO authority VALUES(1,?)',(config_sha,))
   if db.execute('SELECT sha FROM authority WHERE id=1').fetchone()[0]!=config_sha:raise ValueError('LOCAL_AUTHORITY_CHANGED')
   db.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,request TEXT NOT NULL,state TEXT NOT NULL,result TEXT,pid INTEGER)')
   db.execute("UPDATE jobs SET state='INTERRUPTED' WHERE state='RUNNING'")
 @contextmanager
 def db(self):
  db=sqlite3.connect(self.path,timeout=5);db.execute('PRAGMA synchronous=FULL')
  try:
   with db:yield db
  finally:db.close()
 def submit(self,request):
  request=parse(encoded(request).encode());raw=encoded(request)
  with self.db() as db:
   db.execute('BEGIN IMMEDIATE')
   old=db.execute('SELECT request FROM jobs WHERE id=?',(request['action_id'],)).fetchone()
   if old and old[0]!=raw:raise ValueError('ACTION_ID_REUSED')
   if not old:
    if db.execute('SELECT count(*) FROM jobs').fetchone()[0]>=128:raise ValueError('INBOX_FULL')
    db.execute("INSERT INTO jobs VALUES(?,?,'QUEUED',NULL,NULL)",(request['action_id'],raw))
  return self.get(request['action_id'])
 def get(self,action_id):
  if not ID.fullmatch(action_id):raise ValueError('ACTION_IDENTITY')
  with self.db() as db:row=db.execute('SELECT request,state,result,pid FROM jobs WHERE id=?',(action_id,)).fetchone()
  if row is None:raise KeyError('NOT_FOUND')
  return dict(schema='evy-aeris.edge-action.v1',edge_id=self.edge_id,action=json.loads(row[0]),state=row[1],result=json.loads(row[2]) if row[2] else None,worker_pid=row[3],simulation_only=True,physical_motion_authorized=False)
 def claim(self):
  with self.db() as db:
   db.execute('BEGIN IMMEDIATE')
   row=db.execute("SELECT id,request FROM jobs WHERE state='QUEUED' ORDER BY rowid LIMIT 1").fetchone()
   if row:db.execute("UPDATE jobs SET state='RUNNING' WHERE id=?",(row[0],))
  return json.loads(row[1]) if row else None
 def pid(self,action_id,pid):
  with self.db() as db:db.execute('UPDATE jobs SET pid=? WHERE id=?',(pid,action_id))
 def finish(self,action_id,state,result):
  with self.db() as db:db.execute('UPDATE jobs SET state=?,result=? WHERE id=?',(state,encoded(result),action_id))

def worker(inbox,cfg):
 root=Path(cfg['work']);root.mkdir(exist_ok=True)
 while True:
  request=inbox.claim()
  if request is None:time.sleep(.02);continue
  action_id=request['action_id'];path=root/(action_id+'.request.json');path.write_text(encoded(request))
  try:
   if hashlib.sha256(Path(cfg['binary']).read_bytes()).hexdigest()!=cfg['binary_sha256']:raise ValueError('BINARY_CHANGED')
   if hashlib.sha256(Path(cfg['rust_config']).read_bytes()).hexdigest()!=cfg['rust_config_sha256']:raise ValueError('RUST_AUTHORITY_CHANGED')
   with (root/(action_id+'.stdout')).open('wb') as out,(root/(action_id+'.stderr')).open('wb') as err:
    p=subprocess.Popen([cfg['binary'],cfg['rust_config'],cfg['rust_database'],'action',str(path)],stdout=out,stderr=err,start_new_session=True)
    inbox.pid(action_id,p.pid)
    try:code=p.wait(timeout=120)
    except subprocess.TimeoutExpired:
     p.kill();p.wait(timeout=5);raise ValueError('EXECUTION_TIMEOUT_EXPLICIT_RECOVERY_REQUIRED')
   with (root/(action_id+'.stdout')).open('rb') as f:raw=f.read(2097153)
   if len(raw)>2097152:raise ValueError('OUTPUT_BOUND')
   result=json.loads(raw.splitlines()[-1])
   complete=(code==0 and type(result)is dict and result.get('schema')=='evy-aeris.transfer-action-result.v1' and result.get('status')=='COMPLETE' and all(result.get(k)==request[k] for k in ['action_id','skill_id','release_digest']) and result.get('physical_motion_authorized')is False)
   inbox.finish(action_id,'COMPLETE' if complete else 'FAILED',result)
  except Exception as e:
   # No remote supplied paths or commands are included in error responses.
   inbox.finish(action_id,'FAILED',{'status':'REJECTED','reason':type(e).__name__,'physical_motion_authorized':False})

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);args=ap.parse_args()
 raw=args.config.read_bytes();cfg=json.loads(raw)
 lock=open(cfg['inbox']+'.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 inbox=Inbox(cfg['inbox'],cfg['edge_id'],hashlib.sha256(raw).hexdigest())
 token=Path(cfg['token_file']).read_text().strip()
 if len(token)<32:raise ValueError('TOKEN_CONFIG')
 class Handler(http.server.BaseHTTPRequestHandler):
  protocol_version='HTTP/1.0'
  def log_message(self,*args):pass
  def reply(self,status,value):
   data=encoded(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  def handle_one_request(self):
   self.connection.settimeout(5)
   super().handle_one_request()
  def authorized(self):
   supplied=self.headers.get('Authorization','').encode()
   return len(supplied)<=300 and hmac.compare_digest(supplied,('Bearer '+token).encode())
  def do_POST(self):
   if not self.authorized():self.reply(403,{'error':'AUTH_REQUIRED'});return
   if self.path!='/v1/actions':self.reply(404,{'error':'NOT_FOUND'});return
   try:
    if self.headers.get('Transfer-Encoding'):raise ValueError('TRANSFER_ENCODING')
    length=int(self.headers.get('Content-Length','-1'))
    if not 0<=length<=4096:raise ValueError('BODY_LIMIT')
    request=parse(self.rfile.read(length))
    if request['skill_id']not in cfg['allowed_skills']:raise ValueError('SKILL_NOT_ENABLED')
    self.reply(202,inbox.submit(request))
   except (ValueError,UnicodeError):self.reply(409,{'error':'ACTION_REJECTED'})
  def do_GET(self):
   if not self.authorized():self.reply(403,{'error':'AUTH_REQUIRED'});return
   try:
    if not self.path.startswith('/v1/actions/'):raise KeyError('NOT_FOUND')
    self.reply(200,inbox.get(self.path.removeprefix('/v1/actions/')))
   except (ValueError,KeyError):self.reply(404,{'error':'NOT_FOUND'})
 context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2;context.load_cert_chain(cfg['certificate'],cfg['private_key'])
 server=http.server.ThreadingHTTPServer(('0.0.0.0',8443),Handler);server.daemon_threads=True
 server.socket=context.wrap_socket(server.socket,server_side=True)
 threading.Thread(target=worker,args=(inbox,cfg),daemon=True).start()
 print(encoded({'event':'EDGE_GATEWAY_READY','simulation_only':True}),flush=True)
 server.serve_forever()
if __name__=='__main__':main()
