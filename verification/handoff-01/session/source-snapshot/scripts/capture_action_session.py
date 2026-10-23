"""Export public execution evidence using SQLite snapshots, never live WAL copies."""
import argparse,hashlib,json,shutil,sqlite3,time,platform,sys,importlib.metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n')
def snapshot(source,destination):
 if not source.is_file():raise ValueError('Missing evidence database: '+source.name)
 a=sqlite3.connect('file:'+str(source.resolve())+'?mode=ro',uri=True);b=sqlite3.connect(destination)
 try:a.backup(b);b.execute('PRAGMA journal_mode=DELETE')
 finally:b.close();a.close()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--state',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--role',choices=['all','edge','central'],default='all');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
 state=args.state.resolve();freeze=json.loads((state/'source-freeze.json').read_bytes());changed=[name for name,h in freeze['files'].items() if not (ROOT/name).is_file() or sha(ROOT/name)!=h]
 save(args.out/'runtime.json',{'python':sys.version,'platform':platform.platform(),'packages':{k:importlib.metadata.version(k) for k in ['mujoco','numpy','cryptography','fastapi','httpx']}})
 save(args.out/'source-freeze.json',freeze);save(args.out/'capture.json',{'schema':'aeris.action-capture.v1','captured_at_ns':time.time_ns(),'role':args.role,'source_status':'MATCH' if not changed else 'CHANGED','changed':changed,'simulation_only':True,'physical_motion_authorized':False})
 for name in freeze['files']:
  dest=args.out/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
 if args.role in ['all','edge']:
  edge=state/'edge';snapshot(edge/'rust.sqlite',args.out/'rust.snapshot');snapshot(edge/'inbox.sqlite',args.out/'inbox.snapshot');cfg=json.loads((edge/'rust.json').read_bytes());save(args.out/'rust-public.json',cfg)
  gateway=json.loads((edge/'gateway.json').read_bytes());save(args.out/'executor-identity.json',{'binary_sha256':gateway['binary_sha256'],'actual_binary_sha256':sha(Path(gateway['binary'])),'python_sha256':cfg['python_sha256'],'actual_python_sha256':sha(Path(cfg['python']))})
 if args.role in ['all','central']:
  central=state/'central';snapshot(central/'console.sqlite',args.out/'console.snapshot');snapshot(central/'evy.sqlite',args.out/'evy.snapshot')
  with sqlite3.connect(args.out/'console.snapshot') as db:journal=[{'sequence':i,'observed_at_ms':t,'event':e,'payload':json.loads(p)} for i,t,e,p in db.execute('SELECT seq,time_ms,event,payload FROM journal')]
  save(args.out/'journal.json',journal);publisher=json.loads((central/'publisher.json').read_bytes())
  bundles=args.out/'bundles';bundles.mkdir()
  for digest,path in publisher['bundles'].items():shutil.copyfile(path,bundles/(digest+'.json'))
  for service in ['publisher','evy','link','console']:
   src=central/'logs'/(service+'.log')
   if src.exists():shutil.copyfile(src,args.out/(service+'.log'))
 files={str(p.relative_to(args.out)):sha(p) for p in args.out.rglob('*') if p.is_file()};save(args.out/'file-identities.json',files)
 print(json.dumps({'status':'CAPTURED','source_status':'MATCH' if not changed else 'CHANGED','files':len(files),'physical_motion_authorized':False}))
if __name__=='__main__':main()
