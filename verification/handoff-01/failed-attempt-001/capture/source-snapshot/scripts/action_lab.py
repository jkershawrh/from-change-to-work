"""Self-contained simulator lab: prepare once, start, observe, stop.

No system installs, cluster credentials or physical driver. Private generated
material stays in the explicitly selected state directory, outside Git.
"""
import argparse,datetime,hashlib,importlib.util,json,os,platform,secrets,signal,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def sha(data):return hashlib.sha256(data).hexdigest()
def save(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n');p.chmod(0o600)
def hardware():
 cpu=Path('/proc/cpuinfo').read_text() if Path('/proc/cpuinfo').exists() else ''
 def field(name):return next((line.split(':',1)[1].strip() for line in cpu.splitlines() if line.startswith(name)),None)
 result={'system':platform.system(),'architecture':platform.machine(),'cpu_vendor':field('vendor_id'),'cpu_model':field('model name'),'logical_cpus':os.cpu_count()}
 for name in ['/etc/os-release','/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/memory.max']:
  try:result[name]=Path(name).read_text()
  except OSError:result[name]=None
 return result
def inventory():
 import mujoco
 from proof.skill_transfer_v2 import simulator
 binary=ROOT/'crates/aeris-skill-transfer/target/release/aeris-skill-transfer'
 return dict(schema='aeris.edge-inventory.v1',target=dict(profile='mujoco-six-axis-goals-v1',plant_sha256=simulator.plant_identity()[0],calibration_sha256=sha(b'ideal MuJoCo joints; no physical calibration'),joint_names=simulator.JOINTS,units='rad',frame='world-base',runtime='mujoco-rust-mpc-v1',runtime_version=mujoco.__version__,host_arch='aarch64' if platform.machine()=='arm64' else platform.machine(),host_os='macos' if sys.platform=='darwin' else 'linux',adapter_sha256=sha((ROOT/'proof/skill_transfer_v2/simulator.py').read_bytes())),python_sha256=sha(Path(sys.executable).read_bytes()),binary_sha256=sha(binary.read_bytes()),python=sys.executable,root=str(ROOT),host=platform.platform(),observed_hardware=hardware(),physical_motion_authorized=False)
def prepare(args):
 from cryptography import x509
 from cryptography.hazmat.primitives import hashes,serialization
 from cryptography.hazmat.primitives.asymmetric import ec,ed25519
 from cryptography.x509.oid import NameOID
 import ipaddress
 state=args.state.resolve();state.mkdir(parents=True,exist_ok=False);state.chmod(0o700)
 inv=json.loads(args.inventory.read_bytes()) if args.inventory else inventory();assert inv['schema']=='aeris.edge-inventory.v1' and inv['physical_motion_authorized']is False and inv['target']['profile']=='mujoco-six-axis-goals-v1'
 central=state/'central';edge=state/'edge'
 for role in [central,edge]:
  for sub in ['private','evidence','logs']:(role/sub).mkdir(parents=True,mode=0o700)
 remote=args.edge_host not in ['localhost','127.0.0.1'];edge_base=Path(args.edge_state).resolve() if args.edge_state else edge
 edge_root=Path(args.edge_root or inv['root']);edge_python=args.edge_python or inv['python']
 if remote:assert args.inventory and args.edge_state,'Two-host preparation requires an actual edge inventory and explicit remote edge state path.'
 base=args.base_port;ports=dict(publisher=base+3,evy=base+4,edge=base+5,link=base+6,publisher_relay=base+13,evy_relay=base+14,edge_relay=base+15)
 now=datetime.datetime.now(datetime.timezone.utc);cakey=ec.generate_private_key(ec.SECP256R1());name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'EVY AERIS disposable simulator CA')])
 ca=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(cakey.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True,path_length=0),True).add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),True).sign(cakey,hashes.SHA256())
 for role in [central,edge]:
  (role/'private/ca.pem').write_bytes(ca.public_bytes(serialization.Encoding.PEM));(role/'private/ca.der').write_bytes(ca.public_bytes(serialization.Encoding.DER))
  key=ec.generate_private_key(ec.SECP256R1());sans=[]
  for host in set([args.central_host,args.edge_host,'localhost','127.0.0.1']):
   try:sans.append(x509.IPAddress(ipaddress.ip_address(host)))
   except ValueError:sans.append(x509.DNSName(host))
  leaf=x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,role.name+' simulator endpoint')])).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.SubjectAlternativeName(sans),False).add_extension(x509.BasicConstraints(ca=False,path_length=None),True).sign(cakey,hashes.SHA256())
  (role/'private/server-cert.pem').write_bytes(leaf.public_bytes(serialization.Encoding.PEM));p=role/'private/server-key.pem';p.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));p.chmod(0o600)
 tokens={k:secrets.token_hex(32) for k in ['edge','lab','publisher','publication','link','evy','evy-viewer','operator-code','viewer-code']}
 for role in [central,edge]:
  for key in (tokens if role==central else ['edge','lab','publisher']):
   p=role/'private'/key;p.write_text(tokens[key]);p.chmod(0o600)
 signer=ed25519.Ed25519PrivateKey.generate();public=signer.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex();bank={};releases=[];approved=[];home=[-1.5708,-1.5708,1.5708,-1.5708,-1.5708,0.]
 for seq in range(1,33):
  skill='inspection-positioning' if seq%2 else 'rework-positioning'
  goals=[[home[0]+x,*home[1:]] for x in [.28,-.28,.28,-.28]] if seq%2 else [[h+s*x for h,x in zip(home,[.12,-.08,.06,.03,-.04,.02])] for s in [1,-1,1,-1]]
  behavior=json.dumps({'schema':'aeris.bounded-joint-goals.v1','goals':goals},sort_keys=True,separators=(',',':'));ms=time.time_ns()//1000000
  manifest=dict(schema='evy-aeris.transfer-release.v2',release_id='console-'+str(seq),skill_id=skill,sequence=seq,issued_at_ms=ms-1000,not_before_ms=ms-500,expires_at_ms=ms+23*3600000,origin='existing_deterministic_behavior',target=inv['target'],behavior_sha256=sha(behavior.encode()),behavior_size=len(behavior.encode()),recovery_of=None)
  text=json.dumps(manifest,sort_keys=True,separators=(',',':'));digest=sha(text.encode());bundle=dict(schema='evy-aeris.transfer-bundle.v2',manifest_json=text,signature_hex=signer.sign(b'evy-aeris.transfer-release.v2\0'+text.encode()).hex(),behavior_json=behavior)
  path=central/'private/bundles'/(digest+'.json');save(path,bundle);bank[digest]=str(path);approved.append(digest);releases.append({'skill_id':skill,'sequence':seq,'release_digest':digest})
 # The signing private key is intentionally discarded after this finite bank.
 rust=dict(schema='evy-aeris.edge-config.v2',publisher_url=f'https://{args.central_host}:{ports["publisher_relay"]}/release',ca_der_path=str(edge_base/'private/ca.der'),bearer_file=str(edge_base/'private/publisher'),publisher_public_hex=public,approved_manifests=approved,target=inv['target'],python=edge_python,python_sha256=inv['python_sha256'],adapter=str(edge_root/'proof/skill_transfer_v2/simulator.py'))
 save(edge/'rust.json',rust)
 gateway=dict(edge_id='sim-cell-01',inbox=str(edge_base/'inbox.sqlite'),work=str(edge_base/'evidence'),binary=str(edge_root/'crates/aeris-skill-transfer/target/release/aeris-skill-transfer'),binary_sha256=inv['binary_sha256'],rust_config=str(edge_base/'rust.json'),rust_config_sha256=sha((edge/'rust.json').read_bytes()),rust_database=str(edge_base/'rust.sqlite'),token_file=str(edge_base/'private/edge'),certificate=str(edge_base/'private/server-cert.pem'),private_key=str(edge_base/'private/server-key.pem'),lab_token_file=str(edge_base/'private/lab'),lab_controls=True,simulation_only=True,allowed_skills=['inspection-positioning','rework-positioning'],port=ports['edge'],bind='0.0.0.0' if remote else '127.0.0.1')
 save(edge/'gateway.json',gateway)
 save(central/'publisher.json',dict(port=ports['publisher'],token_file=str(central/'private/publisher'),selection_token_file=str(central/'private/publication'),certificate=str(central/'private/server-cert.pem'),private_key=str(central/'private/server-key.pem'),initial_digest=approved[0],bundles=bank))
 save(central/'evy.json',dict(schema='evy.capability-actions.config.v1',database=str(central/'evy.sqlite'),operator_token_file=str(central/'private/evy'),viewer_token_file=str(central/'private/evy-viewer'),targets=[dict(id='sim-cell-01',base_url=f'https://{args.central_host}:{ports["edge_relay"]}',ca_file=str(central/'private/ca.pem'),token_file=str(central/'private/edge'),profile='mujoco-six-axis-goals-v1',allowed_skills=['inspection-positioning','rework-positioning'],simulation_only=True)]))
 save(central/'link.json',dict(bind='0.0.0.0' if remote else '127.0.0.1',port=ports['link'],token_file=str(central/'private/link'),certificate=str(central/'private/server-cert.pem'),private_key=str(central/'private/server-key.pem'),links=[{'listen':ports['publisher_relay'],'host':'127.0.0.1','port':ports['publisher']},{'listen':ports['evy_relay'],'host':'127.0.0.1','port':ports['evy']},{'listen':ports['edge_relay'],'host':args.edge_host,'port':ports['edge']}]))
 console=dict(schema='aeris.action-console.config.v1',simulation_only=True,lab_controls=True,profile='mujoco-six-axis-goals-v1',session_id=str(uuid.uuid4()),database=str(central/'console.sqlite'),ca_file=str(central/'private/ca.pem'),evy_url=f'https://{args.central_host}:{ports["evy_relay"]}',edge_url=f'https://{args.edge_host}:{ports["edge"]}',publisher_url=f'https://localhost:{ports["publisher"]}',link_url=f'https://localhost:{ports["link"]}',edge_id='sim-cell-01',releases=releases,allowed_origins=[f'http://127.0.0.1:{args.ui_port}',f'http://localhost:{args.ui_port}','http://127.0.0.1:5173','http://localhost:5173'],secure_cookie=False,separate_host=remote,topology={'declared_central':args.central_host,'declared_edge':args.edge_host,'identity_scope':'Operator-provisioned endpoints; physical host qualification requires measured inventory.'})
 for field,key in [('edge_token_file','edge'),('lab_token_file','lab'),('evy_token_file','evy'),('publication_token_file','publication'),('link_token_file','link'),('operator_code_file','operator-code'),('viewer_code_file','viewer-code')]:console[field]=str(central/'private'/key)
 save(central/'console.json',console);save(state/'session.json',{'schema':'aeris.lab-session.v1','ports':ports,'ui_port':args.ui_port,'remote':remote,'root':str(ROOT),'python':sys.executable,'edge_inventory':inv})
 files=[p for base in ['services','integrations/evy/backend','frontend/src','crates/aeris-skill-transfer/src','proof/control_v2/controller/src'] for p in (ROOT/base).rglob('*') if p.is_file() and '__pycache__'not in p.parts and p.suffix in ['.py','.rs','.tsx','.ts','.css']]
 files += [ROOT/'scripts/capture_action_session.py',ROOT/'scripts/audit_action_session.py',ROOT/'scripts/build_action_assets.py',ROOT/'services/requirements.txt',ROOT/'scripts/action_lab.py',ROOT/'proof/skill_transfer_v2/simulator.py',ROOT/'proof/skill_transfer_v2/audit.py',ROOT/'crates/aeris-skill-transfer/Cargo.lock',ROOT/'proof/control_v2/run_control.py',ROOT/'proof/control_v2/preregistration.json',ROOT/'proof/control_v2/scene.xml']
 if (ROOT/'services/requirements.lock').exists():files.append(ROOT/'services/requirements.lock')
 if (ROOT/'frontend/dist/index.html').exists():files += [ROOT/'frontend/dist/index.html',*list((ROOT/'frontend/dist/assets').glob('*.js')),*list((ROOT/'frontend/dist/assets').glob('*.css'))]
 save(state/'source-freeze.json',{'schema':'aeris.action-session-sources.v1','registered_at_ns':time.time_ns(),'files':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(set(files))}})
 print(json.dumps({'status':'PREPARED_SIMULATION_ONLY','state':str(state),'operator_code_file':str(central/'private/operator-code'),'remote_edge':remote}))
def start(args):
 state=args.state.resolve();session=json.loads((state/'session.json').read_bytes());p=session['ports'];central=state/'central';edge=state/'edge';need_roles=['edge','central'] if args.role=='all' else [args.role]
 if session['remote'] and args.role=='all':raise ValueError('Use separate --role central and --role edge processes on the declared hosts.')
 env=dict(os.environ,PYTHONPATH=str(ROOT/'integrations/evy')+os.pathsep+str(ROOT),MUJOCO_GL='disable',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');jobs=[]
 python=sys.executable
 save(state/('supervisor-'+args.role+'.json'),{'pid':os.getpid(),'role':args.role,'root':str(ROOT),'state':str(state)})
 def launch(name,argv,extra=None):
  log=(central if name!='edge' else edge)/'logs'/(name+'.log');f=log.open('ab');proc=subprocess.Popen(argv,cwd=ROOT,env={**env,**(extra or {})},stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);jobs.append((name,proc,f))
 try:
  if 'edge'in need_roles:launch('edge',[python,'-m','services.edge_gateway','--config',str(edge/'gateway.json')])
  if 'central'in need_roles:
   launch('publisher',[python,'-m','services.capability_publisher','--config',str(central/'publisher.json')]);launch('link',[python,'-m','services.lab_link','--config',str(central/'link.json')])
   launch('evy',[python,'-m','uvicorn','services.evy_action_gateway:app','--host','127.0.0.1','--port',str(p['evy']),'--ssl-certfile',str(central/'private/server-cert.pem'),'--ssl-keyfile',str(central/'private/server-key.pem')],{'EVY_ACTION_CONFIG':str(central/'evy.json')})
   launch('console',[python,'-m','uvicorn','services.action_console.api:app','--host','127.0.0.1','--port',str(session['ui_port'])],{'AERIS_ACTION_CONSOLE_CONFIG':str(central/'console.json'),'AERIS_ACTION_DIST':str(ROOT/'frontend/dist')})
  print(json.dumps({'status':'STARTING','url':f'http://127.0.0.1:{session["ui_port"]}/?actions=1','operator_code_file':str(central/'private/operator-code'),'scope':'SIMULATION_ONLY'}),flush=True)
  while True:
   for name,proc,_ in jobs:
    if proc.poll()is not None:raise RuntimeError(name+' stopped; inspect its private log file.')
   time.sleep(.5)
 except KeyboardInterrupt:pass
 finally:
  for _,proc,f in jobs:
   if proc.poll()is None:proc.terminate()
  for _,proc,f in jobs:
   try:proc.wait(timeout=5)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
   f.close()
if __name__=='__main__':
 ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True)
 inv=sub.add_parser('inventory');inv.add_argument('--out',type=Path,required=True)
 prep=sub.add_parser('prepare');prep.add_argument('--state',type=Path,required=True);prep.add_argument('--base-port',type=int,default=28440);prep.add_argument('--ui-port',type=int,default=8090);prep.add_argument('--central-host',default='localhost');prep.add_argument('--edge-host',default='127.0.0.1');prep.add_argument('--inventory',type=Path);prep.add_argument('--edge-root');prep.add_argument('--edge-state');prep.add_argument('--edge-python')
 run=sub.add_parser('start');run.add_argument('--state',type=Path,required=True);run.add_argument('--role',choices=['all','central','edge'],default='all');args=ap.parse_args()
 if args.command=='inventory':save(args.out,inventory());print('Observed edge inventory saved; no private keys included.')
 elif args.command=='prepare':prepare(args)
 else:start(args)
