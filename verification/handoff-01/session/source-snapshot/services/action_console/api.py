"""Same-origin browser bridge. All infrastructure credentials remain server-side."""
import asyncio,hashlib,hmac,json,os,secrets,sqlite3,ssl,time
from contextlib import contextmanager
from pathlib import Path
import httpx
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from services.action_console.contracts import ID,control,decode,lab_authority,need,same_origin
ROOT=Path(__file__).resolve().parents[2]
class Console:
 def __init__(self,path):
  config_bytes=Path(path).read_bytes();self.cfg=json.loads(config_bytes);lab_authority(self.cfg);self.sessions={};self.mutex=asyncio.Lock()
  for name in ['evy_url','edge_url','publisher_url','link_url']:need(self.cfg[name].startswith('https://'),'TLS_REQUIRED')
  with self.db() as db:
   db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE IF NOT EXISTS authority(id INTEGER PRIMARY KEY,sha TEXT NOT NULL)');db.execute('INSERT OR IGNORE INTO authority VALUES(1,?)',(hashlib.sha256(config_bytes).hexdigest(),));need(db.execute('SELECT sha FROM authority WHERE id=1').fetchone()[0]==hashlib.sha256(config_bytes).hexdigest(),'CONSOLE_AUTHORITY_CHANGED');db.execute('CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY,request TEXT NOT NULL)');db.execute('CREATE TABLE IF NOT EXISTS journal(seq INTEGER PRIMARY KEY AUTOINCREMENT,time_ms INTEGER NOT NULL,event TEXT NOT NULL,payload TEXT NOT NULL)')
 def secret(self,name):return Path(self.cfg[name]).read_text().strip()
 @contextmanager
 def db(self):
  db=sqlite3.connect(self.cfg['database'],timeout=3);db.execute('PRAGMA synchronous=FULL')
  try:
   with db:yield db
  finally:db.close()
 def record(self,event,value):
  with self.db() as db:db.execute('INSERT INTO journal(time_ms,event,payload) VALUES(?,?,?)',(time.time_ns()//1000000,event,json.dumps(value,allow_nan=False)))
 def latest(self):
  with self.db() as db:row=db.execute('SELECT request FROM actions ORDER BY rowid DESC LIMIT 1').fetchone()
  return json.loads(row[0]) if row else None
 async def call(self,url,token,body=None):
  ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);ctx.load_verify_locations(self.cfg['ca_file'])
  try:
   async with httpx.AsyncClient(verify=ctx,trust_env=False,follow_redirects=False,timeout=httpx.Timeout(5,connect=2)) as client:
    async with client.stream('GET' if body is None else 'POST',url,headers={'Authorization':'Bearer '+self.secret(token)},json=body) as response:
     data=bytearray()
     async for block in response.aiter_bytes():
      data.extend(block);need(len(data)<=2*1024*1024,'RESPONSE_BOUND')
     value=decode(bytes(data),2*1024*1024)
     if response.status_code not in [200,202]:raise HTTPException(response.status_code if response.status_code in [401,403,409,422] else 502,'REMOTE_REQUEST_REFUSED')
     return value
  except httpx.HTTPError:raise HTTPException(503,'REMOTE_UNREACHABLE') from None
 async def state(self):
  edge,link=await asyncio.gather(self.call(self.cfg['edge_url']+'/v1/cell','edge_token_file'),self.call(self.cfg['link_url'],'link_token_file'))
  need(edge.get('schema')=='aeris.edge-cell.v1' and edge.get('simulation_only')is True and edge.get('physical_motion_authorized')is False and edge.get('edge_id')==self.cfg['edge_id'],'EDGE_SCOPE')
  action=self.latest();job=next((j for j in edge['jobs'] if action and j['action_id']==action['action_id']),None);task=next((t for t in edge['tasks'] if action and t['task']=='action-'+action['action_id']),None)
  evy=None;central='UNKNOWN'
  try:
   if action:evy=await self.call(self.cfg['evy_url']+'/actions/capability-transfer/'+action['action_id'],'evy_token_file')
   else:await self.call(self.cfg['evy_url']+'/actions/catalog','evy_token_file')
   central='REACHABLE'
  except HTTPException:central='UNREACHABLE'
  if task:need(task['release_digest']==action['release_digest'],'EDGE_TASK_BINDING')
  if evy:need(evy.get('action_id')==action['action_id'] and evy.get('physical_motion_authorized')is False,'EVY_BINDING')
  phase='AWAITING_ACTION'
  if job:phase=job['state']
  if edge['recovery_required']:phase='RECOVERY_REQUIRED'
  elif task and task['status']=='INTERRUPTED':phase='INTERRUPTED'
  value=dict(schema='aeris.action-console-state.v1',source='LIVE_SIMULATION',session_id=self.cfg['session_id'],simulation_only=True,physical_motion_authorized=False,separate_host=self.cfg.get('separate_host',False),topology=self.cfg.get('topology',{}),observed_at_ms=time.time_ns()//1000000,phase=phase,action=action,task=task,edge=edge,evy=evy,central=central,link=link,observer_channel='INDEPENDENT_MANAGEMENT_PATH',capabilities=sorted(set(r['skill_id'] for r in self.cfg['releases'])))
  # Current session accounting remains amber until an independent saved-evidence
  # audit. The historical qualification never upgrades this session by itself.
  value['rubric']=[{'id':k,'status':'AMBER','reason':'Current-session acceptance evidence is still required.'} for k in ['TDD','EDD','CDD','BDD','CBT']]
  for row in value['rubric']:
   if row['id']=='CDD' and action and any(r['digest']==action['release_digest'] for r in edge['releases']):row.update(status='GREEN',reason='Rust retained the exact approved, compatible release for this action.')
   if row['id']=='CBT' and evy and task:row.update(status='GREEN',reason='EVY action binding and the independent edge observation agree.')
   if row['id']=='EDD':row['reason']='Live observations are recorded. Export and audit the complete execution trace before qualification.'
  value['rubric'] += [{'id':'PHYSICAL_ROBOT','status':'RED','reason':'No physical motion is authorized.'},{'id':'LAB_TRUST','status':'AMBER','reason':'Ephemeral lab trust; customer PKI and host qualification remain Preston’s gates.'}]
  self.record('OBSERVED',{'action_id':action['action_id'] if action else None,'phase':phase,'ticks':task['ticks'] if task else 0,'central':central,'link_connected':link['connected'],'release_digest':task['release_digest'] if task else None})
  return value
 async def submit(self,request):
  need(type(request)is dict and set(request)=={'action_id','skill_id'} and all(type(v)is str and ID.fullmatch(v) for v in request.values()),'ACTION_FIELDS')
  async with self.mutex:
   with self.db() as db:old=db.execute('SELECT request FROM actions WHERE id=?',(request['action_id'],)).fetchone()
   if old:
    bound=json.loads(old[0]);need(bound['skill_id']==request['skill_id'],'ACTION_ID_REUSED')
   else:
    state=await self.state();edge=state['edge'];need(state['link']['connected'] and state['central']=='REACHABLE','CENTRAL_LINK_REQUIRED');need(not edge['recovery_required'] and not any(j['state']in ['QUEUED','RUNNING'] for j in edge['jobs']),'CELL_BUSY_OR_RECOVERY_REQUIRED')
    active=next((r for r in self.cfg['releases'] if r['release_digest']==edge['active_digest'] and r['skill_id']==request['skill_id']),None)
    candidates=[r for r in self.cfg['releases'] if r['skill_id']==request['skill_id'] and r['sequence']>edge['sequence_floor']]
    release=active or min(candidates,key=lambda r:r['sequence'],default=None);need(release,'NO_APPROVED_RELEASE_AVAILABLE')
    bound=dict(schema='evy.capability-action.v1',action_id=request['action_id'],edge_id=self.cfg['edge_id'],skill_id=request['skill_id'],release_digest=release['release_digest'])
    with self.db() as db:db.execute('INSERT INTO actions VALUES(?,?)',(bound['action_id'],json.dumps(bound,sort_keys=True)))
   await self.call(self.cfg['publisher_url']+'/select','publication_token_file',{'release_digest':bound['release_digest']})
   result=await self.call(self.cfg['evy_url']+'/actions/capability-transfer','evy_token_file',bound);self.record('TRANSFER_REQUESTED',{'action':bound,'observation':result});return result
 async def command(self,operation,request):
  request=control(json.dumps(request).encode());need(operation in ['disconnect','reconnect','interrupt','recover'],'CONTROL_NOT_ALLOWED')
  async with self.mutex:
   state=await self.state();need(state['action'] and state['action']['action_id']==request['action_id'],'CONTROL_ACTION_MISMATCH')
   if operation=='disconnect':
    need(state['task'] and state['task']['status']=='RUNNING' and state['task']['ticks']>=1,'RUNNING_OBSERVATION_REQUIRED')
   if operation in ['disconnect','reconnect']:
    result=await self.call(self.cfg['link_url'],'link_token_file',{'command_id':request['command_id'],'operation':operation})
    probe=await self.call(self.cfg['edge_url']+'/v1/connectivity','edge_token_file');result['publisher_probe']=probe
    need(probe['reachable']==(operation=='reconnect'),'LINK_APPLIED_OBSERVATION_UNCERTAIN')
   else:
    result=await self.call(self.cfg['edge_url']+'/v1/lab/'+operation,'lab_token_file',request)
    need(result.get('schema')=='aeris.lab-result.v1' and result.get('operation')==operation and result.get('command_id')==request['command_id'] and result.get('action_id')==request['action_id'] and result.get('simulation_only')is True and result.get('physical_motion_authorized')is False,'CONTROL_ACK_UNCERTAIN')
    need(result.get('status')==('RECOVERED' if operation=='recover' else 'SIGNALLED'),'CONTROL_NOT_CONFIRMED')
   self.record(operation.upper(),{'request':request,'result':result,'before':{'phase':state['phase'],'ticks':state['task']['ticks'] if state['task'] else None}});return result

def create_app(config_path=None):
 app=FastAPI(title='EVY × AERIS action console');path=config_path or os.environ.get('AERIS_ACTION_CONSOLE_CONFIG');console=Console(path) if path else None
 app.state.console=console
 @app.middleware('http')
 async def no_store(request,call_next):
  response=await call_next(request)
  if request.url.path.startswith('/api/action-demo'):
   response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff'
  return response
 def live():
  if console is None:raise HTTPException(503,'LIVE_CONTROLS_NOT_CONFIGURED')
  return console
 def authorized(request,write=False):
  c=live();cookie=request.cookies.get('aeris_action_session','');session=c.sessions.get(hashlib.sha256(cookie.encode()).hexdigest())
  if not session or session['expires']<time.monotonic():raise HTTPException(401,'SESSION_REQUIRED')
  if write and session['role']!='operator':raise HTTPException(403,'OPERATOR_REQUIRED')
  if write:
   try:same_origin(request.headers.get('origin'),request.headers.get('x-aeris-action'),c.cfg['allowed_origins'])
   except ValueError:raise HTTPException(403,'SAME_ORIGIN_REQUIRED') from None
  return c
 async def body(request,limit=4096):
  data=bytearray()
  async for block in request.stream():
   data.extend(block)
   if len(data)>limit:raise HTTPException(413,'BODY_LIMIT')
  try:return decode(bytes(data),limit)
  except (ValueError,UnicodeError):raise HTTPException(422,'JSON_REQUIRED') from None
 @app.exception_handler(ValueError)
 async def invalid(request,error):return JSONResponse({'detail':str(error) if len(str(error))<100 else 'CONTRACT_REJECTED'},status_code=409)
 @app.get('/api/action-demo/health')
 async def health():return {'status':'ready','live_configured':console is not None,'physical_motion_authorized':False}
 @app.get('/api/action-demo/evidence')
 async def evidence():
  p=Path(os.environ.get('AERIS_ACTION_EVIDENCE',str(ROOT/'frontend/public/action-proof.json')))
  return JSONResponse(json.loads(p.read_bytes()),headers={'Cache-Control':'no-store'})
 @app.post('/api/action-demo/session')
 async def login(request:Request):
  c=live()
  try:same_origin(request.headers.get('origin'),request.headers.get('x-aeris-action'),c.cfg['allowed_origins'])
  except ValueError:raise HTTPException(403,'SAME_ORIGIN_REQUIRED') from None
  value=await body(request,512);need(type(value)is dict and set(value)=={'code'} and type(value['code'])is str and len(value['code'])<=256,'SESSION_FIELDS')
  role=None
  for name,r in [('operator_code_file','operator'),('viewer_code_file','viewer')]:
   if hmac.compare_digest(value['code'].encode(),c.secret(name).encode()):role=r
  if role is None:raise HTTPException(403,'ACCESS_CODE_REFUSED')
  token=secrets.token_urlsafe(32);c.sessions[hashlib.sha256(token.encode()).hexdigest()]={'role':role,'expires':time.monotonic()+1800}
  if len(c.sessions)>64:
   oldest=next(iter(c.sessions));c.sessions.pop(oldest)
  response=JSONResponse({'role':role,'simulation_only':True});response.set_cookie('aeris_action_session',token,max_age=1800,httponly=True,samesite='strict',secure=c.cfg.get('secure_cookie',False));return response
 @app.get('/api/action-demo/state')
 async def state(request:Request):return await authorized(request).state()
 @app.post('/api/action-demo/actions',status_code=202)
 async def submit(request:Request):return await authorized(request,True).submit(await body(request))
 @app.post('/api/action-demo/controls/{operation}')
 async def command(operation:str,request:Request):return await authorized(request,True).command(operation,await body(request))
 @app.get('/api/action-demo/export')
 async def export(request:Request):
  c=authorized(request);state=await c.state()
  with c.db() as db:journal=[{'sequence':i,'recorded_at_ms':t,'event':e,'payload':json.loads(p)} for i,t,e,p in db.execute('SELECT seq,time_ms,event,payload FROM journal')]
  return JSONResponse({'schema':'aeris.action-session-export.v1','scope':'LIVE_SIMULATION_OBSERVATIONS_NOT_AN_INDEPENDENT_AUDIT','physical_motion_authorized':False,'state':state,'journal':journal},headers={'Content-Disposition':'attachment; filename="aeris-action-session.json"','Cache-Control':'no-store'})
 dist=os.environ.get('AERIS_ACTION_DIST')
 if dist and Path(dist).is_dir():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
 return app
app=create_app()
