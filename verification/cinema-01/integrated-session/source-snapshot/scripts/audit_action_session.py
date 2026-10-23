"""Independent session accounting. Never imports console/gateway/executor code."""
import argparse,hashlib,importlib.util,json,sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def need(value,message):
 if not value:raise ValueError(message)
def load(p):return json.loads(p.read_bytes())
def audit(root):
 files=load(root/'file-identities.json')
 for name,h in files.items():need(hashlib.sha256((root/name).read_bytes()).hexdigest()==h,'Saved evidence changed: '+name)
 capture=load(root/'capture.json');need(capture['source_status']=='MATCH' and not capture['physical_motion_authorized'],'Unsealed or physical scope')
 freeze=load(root/'source-freeze.json')
 for name,h in freeze['files'].items():need(hashlib.sha256((root/'source-snapshot'/name).read_bytes()).hexdigest()==h,'Source freeze changed')
 identities=load(root/'executor-identity.json');need(identities['binary_sha256']==identities['actual_binary_sha256'] and identities['python_sha256']==identities['actual_python_sha256'],'Executor identity mismatch')
 cfg=load(root/'rust-public.json');key=Ed25519PublicKey.from_public_bytes(bytes.fromhex(cfg['publisher_public_hex']));bundles={}
 for p in (root/'bundles').glob('*.json'):
  b=load(p);text=b['manifest_json'].encode();digest=hashlib.sha256(text).hexdigest();m=json.loads(text);behavior=json.loads(b['behavior_json']);key.verify(bytes.fromhex(b['signature_hex']),b'evy-aeris.transfer-release.v2\0'+text)
  need(digest in cfg['approved_manifests'] and m['target']==cfg['target'],'Unapproved or incompatible artifact');need(hashlib.sha256(b['behavior_json'].encode()).hexdigest()==m['behavior_sha256'] and len(b['behavior_json'].encode())==m['behavior_size'],'Behavior byte mismatch');bundles[digest]=(b,m,behavior)
 spec=importlib.util.spec_from_file_location('saved_independent_trace_auditor',root/'source-snapshot/proof/skill_transfer_v2/audit.py');trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)
 metrics=[]
 with sqlite3.connect('file:'+str((root/'rust.snapshot').resolve())+'?mode=ro&immutable=1',uri=True) as db:
  need(db.execute('PRAGMA integrity_check').fetchone()==('ok',),'SQLite integrity')
  tasks=db.execute('SELECT id,release_digest,status,receipt FROM tasks').fetchall();need(tasks,'No execution evidence')
  for task,digest,status,receipt in tasks:
   need(status in ['COMPLETE','INTERRUPTED'] and receipt,'Unreconciled execution')
   samples=[json.loads(r[0]) for r in db.execute('SELECT payload FROM samples WHERE task=? ORDER BY tick',(task,))];metrics.append(trace.check_task(task,digest,status,json.loads(receipt),samples,bundles))
  starts=[json.loads(r[0]) for r in db.execute("SELECT payload FROM events WHERE kind='TASK_STARTED'")];need(len(starts)==len(tasks) and len({r['task'] for r in starts})==len(tasks),'Repeated task execution')
 journal=load(root/'journal.json');need([e['sequence'] for e in journal]==list(range(1,len(journal)+1)),'Journal gap')
 disconnect=False;recovery=False
 for i,event in enumerate(journal):
  if event['event']=='DISCONNECT':
   p=event['payload'];need(p['before']['phase']=='RUNNING' and p['result']['publisher_probe']['reachable']is False,'False network cut')
   aid=p['request']['action_id'];observations=[]
   for later in journal[i+1:]:
    if later['event']=='RECONNECT':break
    if later['event']=='OBSERVED' and later['payload']['action_id']==aid:observations.append(later['payload'])
   disconnect |= any(o['ticks']>p['before']['ticks'] and o['central']=='UNREACHABLE' and o['phase']=='COMPLETE' and o['link_connected']is False for o in observations)
  if event['event']=='RECOVER':
   p=event['payload'];need(p['result']['status']=='RECOVERED' and p['result']['interrupted_tasks']>=1,'False recovery')
   aid=p['request']['action_id'];need(any(m['task']=='action-'+aid and m['status']=='INTERRUPTED' for m in metrics),'Recovery has no interrupted task')
   later_actions=[l['payload']['action']['action_id'] for l in journal[i+1:] if l['event']=='TRANSFER_REQUESTED'];recovery |= any(m['task'].removeprefix('action-')in later_actions and m['status']=='COMPLETE' and m['task']!='action-'+aid for m in metrics)
 need(disconnect and recovery,'Disconnect/continued execution/recovery journey not fully observed')
 return {'schema':'aeris.action-session-audit.v1','status':'PASS_LOCAL_SIMULATION_ACCOUNTING','scope':'No separate-host, physical-robot or real-time qualification inferred.','tasks':metrics,'total_control_ticks':sum(m['control_ticks'] for m in metrics),'total_physics_substeps':sum(m['physics_substeps'] for m in metrics),'disconnect_and_local_completion':disconnect,'explicit_recovery_and_new_action':recovery,'physical_motion_authorized':False}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);args=ap.parse_args();report=audit(args.directory);(args.directory/'audit-result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
