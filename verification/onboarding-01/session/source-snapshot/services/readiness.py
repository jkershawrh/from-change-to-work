"""Read-only local prerequisite inventory. Never probes a network or robot.

Fixed subprocesses are bounded and run without a shell. Reports contain selected
public facts, not environment variables, credentials, machine IDs or hostname.
"""
import hashlib,json,os,platform,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOOLS={'node':['node','--version'],'cargo':['cargo','--version'],'lfs':['git','lfs','version']}

def command(argv,root,timeout=5):
 try:
  r=subprocess.run(argv,cwd=root,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=timeout,check=False)
  return r.stdout.decode(errors='replace')[:32768].strip() if r.returncode==0 else None
 except (OSError,subprocess.TimeoutExpired):return None

def version(text):
 m=re.search(r'(\d+)\.(\d+)\.(\d+)',text or '')
 return tuple(map(int,m.groups())) if m else None

def evaluate(snapshot,observed_at_ms):
 tools=snapshot['tools'];checks=[]
 def check(id,ok,detail,remedy):checks.append(dict(id=id,status='GREEN' if ok else 'RED',detail=detail,next_step=None if ok else remedy))
 for name,minimum,remedy in [('python',(3,12,0),'Install Python 3.12 and rerun scripts/setup.sh.'),('node',(22,12,0),'Use Node 22.12+ or 24, then rerun frontend installation.'),('cargo',(1,90,0),'Install Rust/Cargo 1.90+ using your approved process.'),('lfs',(3,0,0),'Install Git LFS, then run git lfs pull.')]:
  v=version(tools.get(name));valid=v is not None and (v[:2]==(3,12) if name=='python' else v>=minimum)
  check(name,valid,tools.get(name) or 'Not observed',remedy)
 deps=snapshot['dependencies']['status'];check('dependencies',deps=='MATCH','Pinned Python packages: '+deps,'Run scripts/setup.sh, then rerun the preflight.')
 for name,remedy in [('executor','Build the pinned Rust release with scripts/setup.sh.'),('frontend','Build the frontend with scripts/setup.sh.'),('plant_assets','Run git lfs pull and retain the original plant asset closure.')]:
  status=snapshot['artifacts'][name];check(name,status=='PRESENT',name.replace('_',' ')+': '+status,remedy)
 host=snapshot['host'];candidate=host.get('cpu_vendor')=='GenuineIntel' and host.get('os_id')=='rhel'
 return dict(schema='aeris.readiness-report.v1',observed_at_ms=observed_at_ms,measurement_scope='CURRENT_PROCESS_HOST_ONLY',simulation_prerequisites='READY' if all(c['status']=='GREEN' for c in checks) else 'BLOCKED',simulation_only=True,physical_motion_authorized=False,host=host,source=snapshot['source'],checks=checks,alignment={'status':'CANDIDATE_ONLY' if candidate else 'UNVERIFIED','scope':'Observed Intel vendor plus RHEL OS ID is a candidate configuration, not certification. Console host inventory does not identify the edge host or OpenShift nodes.'},qualification=[{'id':id,'status':'RED','reason':reason} for id,reason in [('CURRENT_SESSION','No execution acceptance is inferred from this inventory.'),('TWO_HOST_HARDWARE','Separate central/edge identities and independently reconciled execution evidence are required.'),('PHYSICAL_ROBOT','No reviewed physical adapter, calibration, safeguarding or OEM stop acceptance.'),('HARD_REAL_TIME','No continuous hardware timing or watchdog qualification.')]])

def collect(root=ROOT):
 root=Path(root);system=platform.system();cpu={};os_info={}
 try:
  for line in Path('/proc/cpuinfo').read_text().splitlines():
   if ':' in line:
    k,v=line.split(':',1);cpu.setdefault(k.strip(),v.strip())
 except OSError:pass
 try:
  for line in Path('/etc/os-release').read_text().splitlines():
   if '=' in line:
    k,v=line.split('=',1);os_info[k]=v.strip('"')
 except OSError:pass
 host=dict(system=system,architecture=platform.machine(),kernel=platform.release(),logical_cpus=os.cpu_count(),cpu_vendor=cpu.get('vendor_id'),cpu_model=cpu.get('model name'),os_id=os_info.get('ID','darwin' if system=='Darwin' else None),os_version=os_info.get('VERSION_ID'))
 tools={k:command(v,root) for k,v in TOOLS.items()}
 python=root/'.venv/bin/python';tools['python']=command([str(python),'--version'],root) if python.is_file() else None
 # Only package metadata is queried. No install/import/model or external connection.
 packages={}
 for line in (root/'services/requirements.txt').read_text().splitlines():
  if '==' in line and not line.startswith('#'):
   k,v=line.strip().split('==',1);packages[k]=v
 code='import importlib.metadata,json; names='+repr(list(packages))+'; print(json.dumps({n:importlib.metadata.version(n) for n in names}))'
 raw=command([str(python),'-c',code],root) if python.is_file() else None
 try:deps='MATCH' if json.loads(raw)==packages else 'MISMATCH'
 except (TypeError,ValueError):deps='UNAVAILABLE'
 def artifact(path,executable=False):
  if not path.is_file():return 'MISSING'
  with path.open('rb') as f:head=f.read(100)
  if head.startswith(b'version https://git-lfs.github.com/spec/v1'):return 'LFS_POINTER'
  if executable and not os.access(path,os.X_OK):return 'NOT_EXECUTABLE'
  return 'PRESENT'
 assets=[root/'proof/control/assets/ur5e/ur5e.xml',*list((root/'proof/control/assets/ur5e/assets').glob('*.obj'))]
 states=[artifact(p) for p in assets]
 asset_status='PRESENT' if len(assets)>1 and all(v=='PRESENT' for v in states) else ('LFS_POINTER' if 'LFS_POINTER' in states else 'MISSING')
 commit=command(['git','rev-parse','HEAD'],root);dirty=command(['git','status','--porcelain','--untracked-files=no'],root)
 # Runtime digest is independent of Git's tracked/untracked state, excluding evidence/cache/private material.
 files=[p for base in ['services','frontend/src','crates/aeris-skill-transfer/src'] for p in (root/base).rglob('*') if p.is_file() and p.suffix in ['.py','.ts','.tsx','.css','.rs'] and '__pycache__' not in p.parts]
 digest=hashlib.sha256()
 for p in sorted(files):digest.update(str(p.relative_to(root)).encode()+b'\0'+hashlib.sha256(p.read_bytes()).digest())
 return evaluate(dict(host=host,source={'commit':commit,'dirty':bool(dirty) if dirty is not None else None,'runtime_sha256':digest.hexdigest(),'identity_note':'Dirty reflects tracked edits only; runtime hash includes the selected current source tree.'},tools=tools,dependencies={'status':deps},artifacts={'executor':artifact(root/'crates/aeris-skill-transfer/target/release/aeris-skill-transfer',True),'frontend':artifact(root/'frontend/dist/index.html'),'plant_assets':asset_status}),time.time_ns()//1000000)

def write_report(path,report):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 # Exclusive create: a later run must not silently overwrite an earlier observation.
 with path.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
