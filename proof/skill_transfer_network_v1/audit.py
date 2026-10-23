"""Saved-evidence audit. No gateway, coordinator, producer or executor imports.

Reuses only the prior independent trace-accounting auditor. Physics assumptions
remain shared with MuJoCo; this is not independent physics or device attestation.
"""
import argparse,hashlib,importlib.util,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def require(condition,message):
 if not condition:raise ValueError(message)
def load(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def check_hosts(hosts):
 a,b=hosts['central'],hosts['edge']
 require(a['node_uid']!=b['node_uid'] and a['system_uuid']!=b['system_uuid'],'same host')
 for h in hosts.values():
  require(h['observed']['cpu_vendor']=='GenuineIntel','not observed Intel')
  require('ID="rhel"'in h['observed']['os_release'] and 'Red Hat Enterprise Linux CoreOS'in h['node_info']['osImage'],'not observed Red Hat')
def check_disconnect_progress(scenario):
 before,after,final=[scenario[k] for k in ['disconnection_before','disconnection_after','isolated_completion']]
 require(before['task_status']==after['task_status']=='RUNNING','no running control spanning isolation')
 require(after['ticks']>before['ticks']>=5,'no later control progress')
 require(final['job_state']==final['task_status']=='COMPLETE' and final['ticks']>after['ticks'],'no completion after isolated progress')
def audit(directory):
 from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
 hosts=load(directory/'hosts.json');check_hosts(hosts)
 scenario=load(directory/'scenario.json');check_disconnect_progress(scenario)
 result=load(directory/'result.json');require(result['status']=='PASS_SCENARIOS_PENDING_AUDIT' and not result['physical_motion_authorized'],'scenario not passed')
 freeze=load(directory/'local-source-freeze.json')
 for file,digest in freeze['files'].items():require(sha((directory/'source-snapshot'/file).read_bytes())==digest,'source changed: '+file)
 deployed=load(directory/'deployed-source-freeze.json')
 require(sha((directory/'executor-linux.bin').read_bytes())==deployed['binary_sha256'],'binary changed')
 for role,files in deployed['files'].items():
  for file,digest in files.items():
   base=directory/'source-snapshot'
   if file.startswith('/work/input/repo/'):local=base/file.removeprefix('/work/input/repo/')
   else:local=base/'evy'/file.removeprefix('/work/input/evy/')
   require(sha(local.read_bytes())==digest,'deployed source mismatch: '+file)
 cfg=load(directory/'rust-config-public.json');key=Ed25519PublicKey.from_public_bytes(bytes.fromhex(cfg['publisher_public_hex']));bundles={}
 for path in directory.glob('*.bundle.json'):
  b=load(path);text=b['manifest_json'].encode();digest=sha(text);m=json.loads(text);behavior=json.loads(b['behavior_json'])
  key.verify(bytes.fromhex(b['signature_hex']),b'evy-aeris.transfer-release.v2\0'+text)
  require(digest in cfg['approved_manifests'] and m['target']==cfg['target'],'unapproved/incompatible')
  require(sha(b['behavior_json'].encode())==m['behavior_sha256'] and len(b['behavior_json'].encode())==m['behavior_size'],'behavior mismatch')
  bundles[digest]=(b,m,behavior)
 require(len(bundles)==2 and {v[1]['skill_id'] for v in bundles.values()}=={'inspection-positioning','rework-positioning'},'capability reuse absent')
 spec=importlib.util.spec_from_file_location('independent_trace_accounting',directory/'source-snapshot/proof/skill_transfer_v2/audit.py');trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)
 database=directory/'edge/evidence/rust.snapshot';metrics=[]
 with sqlite3.connect('file:'+str(database.resolve())+'?mode=ro&immutable=1',uri=True) as db:
  require(db.execute('PRAGMA integrity_check').fetchone()==('ok',),'store integrity')
  tasks=db.execute('SELECT id,release_digest,status,receipt FROM tasks ORDER BY id').fetchall()
  expected={'action-inspection-disconnected':'COMPLETE','action-rework-interrupted':'INTERRUPTED','action-rework-recovered':'COMPLETE'}
  require({t[0]:t[2] for t in tasks}==expected,'task inventory or replay')
  for task,digest,status,receipt in tasks:
   samples=[json.loads(r[0]) for r in db.execute('SELECT payload FROM samples WHERE task=? ORDER BY tick',(task,))]
   metrics.append(trace.check_task(task,digest,status,json.loads(receipt),samples,bundles))
  starts=[json.loads(r[0]) for r in db.execute("SELECT payload FROM events WHERE kind='TASK_STARTED'")]
  require(len(starts)==3 and len({s['task'] for s in starts})==3,'duplicate execution')
  rows=db.execute('SELECT digest,sequence,bundle FROM releases ORDER BY sequence').fetchall()
  require(len(rows)==2 and all(json.loads(b)==bundles[d][0] for d,seq,b in rows),'received bytes mismatch')
  floor,active=db.execute('SELECT floor,active FROM meta WHERE id=1').fetchone()
  require(floor==2 and bundles[active][1]['skill_id']=='rework-positioning','active sequence mismatch')
 with sqlite3.connect(directory/'edge/evidence/inbox.snapshot') as db:
  jobs=db.execute('SELECT id,request,state,result FROM jobs').fetchall()
  require({r[0]:r[2] for r in jobs}=={'inspection-disconnected':'COMPLETE','wrong-release':'FAILED','rework-interrupted':'FAILED','rework-recovered':'COMPLETE'},'inbox terminal replay')
  for action,request,state,response in jobs:
   request=json.loads(request)
   if state=='COMPLETE':
    response=json.loads(response)
    require(all(response[k]==request[k] for k in ['action_id','skill_id','release_digest']) and response['status']=='COMPLETE','terminal binding')
 with sqlite3.connect(directory/'central/evidence/evy.snapshot') as db:
  central={i:json.loads(r) for i,r in db.execute('SELECT id,request FROM actions')}
  require(set(central)=={r[0] for r in jobs},'EVY and edge action inventory')
  for action,request,state,response in jobs:
   request=json.loads(request);require(all(central[action][k]==request[k] for k in ['action_id','skill_id','release_digest']),'cross-host request mismatch')
 operations=load(directory/'operations.json')
 def operation(label):
  matches=[o for o in operations if o['label']==label];require(len(matches)==1,'operation missing/duplicate '+label);return matches[0]
 def output(label):return json.loads((directory/operation(label)['stdout']).read_bytes())
 isolation=operation('isolate-central-network');probe=operation('disconnected-publisher-probe');progress=operation('control-after-disconnection');restore=operation('restore-central-network')
 require(isolation['exit_code']==0 and isolation['end_monotonic_ns']<probe['start_monotonic_ns']<probe['end_monotonic_ns']<progress['start_monotonic_ns']<restore['start_monotonic_ns'],'isolation causal order')
 require(output('disconnected-publisher-probe')['reachable']is False,'publisher reachable')
 require(output('central-to-edge-blocked')['status']==502,'central reached edge during isolation')
 completion=[o for o in operations if o['label']=='isolated-edge-progress' and json.loads((directory/o['stdout']).read_bytes()).get('job_state')=='COMPLETE']
 require(len(completion)==1 and completion[0]['end_monotonic_ns']<restore['start_monotonic_ns'],'completion after reconnection')
 for label,status in [('viewer-submit-refused',403),('remote-authority-field-refused',422),('unregistered-edge-refused',422),('changed-action-id-binding-refused',409)]:require(output(label)['status']==status,'missing rejection '+label)
 require(output('kill-moving-rust-executor')['signal']=='SIGKILL' and output('kill-moving-rust-executor')['command_verified'],'death missing')
 require(output('explicit-local-rust-recovery')['lines'][-1]['interrupted_tasks']==1,'recovery missing')
 require(output('new-motion-before-recovery-refused')['exit_code']==2,'automatic recovery allowed')
 requests=[json.loads(s) for s in (directory/'central/evidence/publisher.log').read_text().splitlines() if s.startswith('{')]
 delivered=[r for r in requests if r.get('event')=='BUNDLE_DELIVERED']
 require(len(delivered)>=2 and all(r['tls']in ['TLSv1.2','TLSv1.3'] and r['peer']==hosts['edge']['pod_ip'] for r in delivered),'no cross-host TLS delivery')
 checks=load(directory/'checks.json');require(all(c['pass_'] for c in checks),'failed checks')
 return dict(schema='evy-aeris.network-audit.v1',status='PASS_SEPARATE_HOST_SIMULATION',tasks=metrics,total_control_ticks=sum(m['control_ticks'] for m in metrics),total_physics_substeps=sum(m['physics_substeps'] for m in metrics),cross_host_tls_deliveries=len(delivered),hosts={r:h['node'] for r,h in hosts.items()},evy_action_gateway_exercised=True,simulation_only=True,physical_motion_authorized=False,independent_physics=False,lab_control_plane_trust='AMBER_TOFU')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);args=ap.parse_args();report=audit(args.directory);save=args.directory/'audit-result.json';save.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
