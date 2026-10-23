"""Independent saved-byte/SQLite/kinematic accounting. Imports no producer,
lifecycle runtime, simulator, controller or experiment harness. Shared MuJoCo
physics assumptions remain outside this audit's scope.
"""
import argparse
import hashlib
import json
import math
import sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

HOME = [-1.5708, -1.5708, 1.5708, -1.5708, -1.5708, 0.]
ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()
def load(path): return json.loads(path.read_bytes())
def close(a, b, tolerance=1e-8): return abs(a-b) <= tolerance


def check_task(task, release_digest, status, receipt, samples, bundles):
    require(release_digest in bundles, 'unknown task release')
    bundle, manifest, behavior = bundles[release_digest]
    require(status in ('COMPLETE', 'INTERRUPTED'), 'task failed or running')
    require(bool(samples), 'empty task trace')
    previous = None
    held = 0
    completed = 0
    peak_speed = peak_acceleration = peak_position = 0.
    for tick, sample in enumerate(samples):
        require(sample['tick'] == tick and sample['task'] == task and sample['release_digest'] == release_digest, 'sample identity')
        goal_index = sample['goal_index']
        require(goal_index == completed and goal_index < len(behavior['goals']), 'goal progression')
        target = behavior['goals'][goal_index]
        require(sample['target'] == target and sample['valid'], 'target or valid claim')
        before, after = sample['before'], sample['after']
        expected_q = HOME if previous is None else previous['q']
        expected_v = [0.]*6 if previous is None else previous['velocity']
        expected_time = 0. if previous is None else previous['simulation_seconds']
        require(all(close(x,y) for x,y in zip(before['q'],expected_q)) and all(close(x,y) for x,y in zip(before['velocity'],expected_v)), 'tick state continuity')
        require(close(before['simulation_seconds'],expected_time), 'tick time continuity')
        command = sample['acceleration_command']
        require(len(command)==6 and all(math.isfinite(x) and abs(x)<=.85+1e-9 for x in command), 'command limits')
        steps = sample['physics_substeps']
        require(len(steps)==10, 'substep count')
        for i,step in enumerate(steps):
            require(step['index']==i and close(step['simulation_seconds']-expected_time,.002,1e-9), 'substep time')
            require(step['contacts']==[], 'forbidden contact')
            for j in range(6):
                values=[step[k][j] for k in ('q','velocity','velocity_before','finite_difference_acceleration','native_acceleration','requested_torque_nm','applied_torque_nm','disturbance_nm')]
                require(all(math.isfinite(x) for x in values), 'nonfinite substep')
                require(close(step['velocity_before'][j],expected_v[j]), 'substep velocity continuity')
                acceleration=(step['velocity'][j]-expected_v[j])/.002
                require(close(acceleration,step['finite_difference_acceleration'][j]), 'finite difference acceleration')
                peak_position=max(peak_position,abs(step['q'][j]-HOME[j]))
                peak_speed=max(peak_speed,abs(step['velocity'][j]))
                peak_acceleration=max(peak_acceleration,abs(acceleration),abs(step['native_acceleration'][j]))
            expected_v=step['velocity']; expected_time=step['simulation_seconds']
        require(all(close(x,y) for x,y in zip(after['q'],steps[-1]['q'])) and all(close(x,y) for x,y in zip(after['velocity'],expected_v)), 'tick final state')
        require(close(after['simulation_seconds'],expected_time), 'tick final time')
        near=all(abs(q-t)<.015 for q,t in zip(after['q'],target)) and all(abs(v)<.025 for v in after['velocity'])
        held=held+1 if near else 0
        if held>=10: completed+=1; held=0
        previous=after
    require(peak_position<=.65+1e-6 and peak_speed<=.45+1e-6 and peak_acceleration<=1.2+1e-6,'measured limits')
    if status=='INTERRUPTED':
        require(peak_position>0.005 and peak_speed>0.02,'interruption did not exercise moving simulator')
    require(receipt['status']==status, 'receipt status')
    if status=='COMPLETE':
        require(completed==len(behavior['goals']), 'false completion')
        require(receipt['ticks']==len(samples) and receipt['completed_goals']==completed and receipt['requested_goals']==len(behavior['goals']), 'receipt counts')
        require(receipt['release_digest']==release_digest and receipt['sequence']==manifest['sequence'] and receipt['behavior_sha256']==manifest['behavior_sha256'], 'receipt version binding')
        require(receipt['simulation_only'] and not receipt['physical_motion_authorized'] and not receipt['training_required'], 'receipt scope')
    else:
        require(receipt['simulation_reset_required'] and not receipt['physical_resume_authorized'], 'interruption policy')
    return {'task':task,'status':status,'control_ticks':len(samples),'physics_substeps':len(samples)*10,
            'peak_speed_rad_s':peak_speed,'peak_acceleration_rad_s2':peak_acceleration,'peak_displacement_rad':peak_position}


def audit(directory, verify_sources=True):
    result=load(directory/'result.json')
    require(result['status']=='PASS_LOCAL_SOFTWARE_LOOP' and result['simulation_only'] and not result['physical_motion_authorized'] and not result['separate_host_qualification'], 'proof scope')
    freeze=load(directory/'source-freeze.json')
    require(freeze['before_execution_unix_ns']<=result['started_unix_ns'], 'source registration order')
    if verify_sources:
        for file,digest in freeze['files'].items(): require(sha((directory/'source-snapshot'/file).read_bytes())==digest,'source identity: '+file)
    require(sha((directory/'executor.bin').read_bytes())==freeze['binary_sha256'],'executor binary identity')
    cfg=load(directory/'local-config-public.json')
    key=Ed25519PublicKey.from_public_bytes(bytes.fromhex(cfg['publisher_public_hex']))
    bundle_by_digest={}
    for name in ('first','second','recovery','module-fourth'):
        bundle=load(directory/(name+'.bundle.json'))
        text=bundle['manifest_json'].encode(); identity=sha(text)
        key.verify(bytes.fromhex(bundle['signature_hex']),b'evy-aeris.transfer-release.v2\0'+text)
        manifest=json.loads(text); behavior=json.loads(bundle['behavior_json'])
        require(identity in cfg['approved_manifests'] and manifest['target']==cfg['target'], 'release approval/target')
        require(sha(bundle['behavior_json'].encode())==manifest['behavior_sha256'] and len(bundle['behavior_json'].encode())==manifest['behavior_size'], 'received behavior bytes')
        require(manifest['origin']=='existing_deterministic_behavior','fabricated training requirement')
        bundle_by_digest[identity]=(bundle,manifest,behavior)
    first,second,recovery,fourth=result['release_digests']
    require(set(bundle_by_digest)==set(result['release_digests']), 'release identities')
    require(bundle_by_digest[first][2]!=bundle_by_digest[second][2], 'candidate changes no behavior')
    require(bundle_by_digest[first][0]['behavior_json']==bundle_by_digest[recovery][0]['behavior_json'] and bundle_by_digest[recovery][1]['recovery_of']==first, 'recovery capability identity')
    conn=sqlite3.connect('file:'+str((directory/'edge-store.snapshot').resolve())+'?mode=ro&immutable=1',uri=True)
    try:
        require(conn.execute('PRAGMA integrity_check').fetchone()==('ok',),'SQLite integrity')
        floor,active=conn.execute('SELECT floor,active FROM meta WHERE id=1').fetchone()
        require(floor==4 and active==fourth,'durable active/floor')
        rows=conn.execute('SELECT digest,sequence,bundle FROM releases ORDER BY sequence').fetchall()
        require(len(rows)==4,'release count')
        for digest,seq,encoded in rows:
            require(json.loads(encoded)==bundle_by_digest[digest][0] and seq==bundle_by_digest[digest][1]['sequence'],'SQLite received byte binding')
        tasks=conn.execute('SELECT id,release_digest,status,receipt FROM tasks ORDER BY id').fetchall()
        require({t[0] for t in tasks}=={'disconnected-first','interrupted-second','restarted-second','recovery-third','action-rework-001'},'unexpected tasks or duplicate execution')
        metrics=[]
        for task,release,status,receipt in tasks:
            samples=[json.loads(row[0]) for row in conn.execute('SELECT payload FROM samples WHERE task=? ORDER BY tick',(task,))]
            metrics.append(check_task(task,release,status,json.loads(receipt),samples,bundle_by_digest))
        require(sum(t[2]=='COMPLETE' for t in tasks)==4 and sum(t[2]=='INTERRUPTED' for t in tasks)==1,'task outcomes')
        starts=[json.loads(r[0]) for r in conn.execute("SELECT payload FROM events WHERE kind='TASK_STARTED'")]
        require(len(starts)==5 and len({s['task'] for s in starts})==5,'lost acknowledgement reexecutes')
        bound=conn.execute("SELECT request FROM actions WHERE id='rework-001'").fetchone()
        require(bound is not None and json.loads(bound[0])==load(directory/'module-action.json'),'action request binding changed')
    finally: conn.close()
    commands=load(directory/'commands.json')
    def command(name):
        matches=[c for c in commands if c['name']==name];require(len(matches)==1,'command missing/duplicated: '+name);return matches[0]
    def output(name):
        c=command(name); lines=(directory/c['stdout']).read_bytes().splitlines();return json.loads(lines[-1]) if lines else None
    for operation in ('stage','activate'):
        for boundary in ('before','after'):
            label=operation+'-'+boundary+'-commit'
            require(command(label+'-crash')['exit_code']==86,'fault not injected')
            state=output(label+'-reopened')
            require(state['sequence_floor']==(2 if operation=='activate' or boundary=='after' else 1),'non-atomic sequence floor')
            require(state['active_digest']==(second if operation=='activate' and boundary=='after' else first),'non-atomic active pointer')
    for point in ('task-after-start','task-after-step'):
        require(command(point+'-crash')['exit_code']==86,'task fault missing')
        state=output(point+'-reopened')
        require(len(state['tasks'])==1 and state['tasks'][0]['status']=='RUNNING','task ownership not durable')
        require(output(point+'-recover')['interrupted_tasks']==1,'task recovery missing')
    for name in ('transport-redirect','transport-truncated','transport-oversize','transport-oversize-stream','transport-unauthorized','transport-untrusted-ca',
                 'busy-activation-refused','busy-recovery-refused','second-executor-refused','disconnected-fetch-refused',
                 'activation-after-crash-refused','new-task-before-recovery-refused','superseded-activation-refused'):
        require(command(name)['exit_code']==2 and output(name)['status']=='REJECTED','missing refusal: '+name)
    negatives=[c for c in commands if c['name'].startswith('reject-')]
    require(len(negatives)==18 and all(c['exit_code']==2 for c in negatives),'contract negative cases')
    require(output('before-rejections')==output('after-rejections'),'rejections changed durable state')
    require(output('before-completion-retry')==output('after-completion-retry'),'completion ACK retry changed state')
    require(output('idempotent-completion-retry')['idempotent'],'completion ACK retry not idempotent')
    request=load(directory/'module-action.json')
    require(request['release_digest']==fourth and request['skill_id']==bundle_by_digest[fourth][1]['skill_id'] and request['skill_id']!=bundle_by_digest[first][1]['skill_id'],'action capability binding')
    action=output('second-capability-via-action')
    require(action['schema']=='evy-aeris.transfer-action-result.v1' and action['status']=='COMPLETE' and action['task']=='action-rework-001' and action['release_digest']==fourth and action['skill_id']==request['skill_id'] and action['action_id']==request['action_id'],'action execution result')
    require(output('action-offline-idempotent-retry')['idempotent'] and output('before-action-retry')==output('after-action-retry'),'action retry reexecuted')
    require(output('before-action')==output('after-wrong-publication'),'unexpected remote capability staged')
    for label in ('action-wrong-publication-refused','action-id-reuse-refused','action-wrong-skill-refused'):
        require(command(label)['exit_code']==2 and output(label)['status']=='REJECTED','action rejection missing: '+label)
    disconnection=load(directory/'disconnection.json')
    process=load(directory/'disconnected-first-process.json')
    failed_fetch=command('disconnected-fetch-refused')
    require(process['progress_unix_ns']<disconnection['before_unix_ns']<=disconnection['after_unix_ns']<failed_fetch['start_unix_ns']<process['end_unix_ns'],'disconnect/task order')
    require(disconnection['exit_code']<0 and process['result']['status']=='COMPLETE','publisher stayed up or task incomplete')
    require(process['result']['completed_at_unix_ms']*1000000>disconnection['after_unix_ns'],'task completed before disconnect')
    with sqlite3.connect('file:'+str((directory/'edge-store.snapshot').resolve())+'?mode=ro&immutable=1',uri=True) as db:
        observed=[json.loads(r[0])['observed_at_unix_ms'] for r in db.execute("SELECT payload FROM samples WHERE task='disconnected-first'")]
    require(any(t*1000000>disconnection['after_unix_ns'] for t in observed),'no local control observation after disconnect')
    tls_requests=[]
    for path in directory.glob('publisher-*.jsonl'):
        tls_requests.extend(json.loads(line) for line in path.read_text().splitlines() if json.loads(line)['event']=='REQUEST')
    require(bool(tls_requests) and all(r['tls'] in ('TLSv1.2','TLSv1.3') for r in tls_requests),'TLS not observed')
    require(any(r['status']==401 and not r['authorized'] for r in tls_requests),'authorization refusal absent')
    require(any(r['mode']=='truncated' for r in tls_requests) and any(r['mode']=='redirect' for r in tls_requests),'transport fault observations absent')
    interrupted=load(directory/'interrupted-second-process.json')
    require(interrupted['killed'] and interrupted['exit_code']==-9,'process death not injected')
    checks=load(directory/'checks.json')
    require(any(c['name']=='orphan-adapter-retires-on-eof' and c['pass'] for c in checks),'orphan cleanup missing')
    return {'schema':'evy-aeris.transfer-audit.v1','status':'PASS_ACCOUNTING','tasks':metrics,
            'total_control_ticks':sum(x['control_ticks'] for x in metrics),'total_physics_substeps':sum(x['physics_substeps'] for x in metrics),
            'tls_requests':len(tls_requests),'contract_negative_cases':len(negatives),'simulation_only':True,'capability_ids':[bundle_by_digest[first][1]['skill_id'],bundle_by_digest[fourth][1]['skill_id']],'action_interface_proved':True,'evy_action_adapter_registered':False,'aeris_catalog_registered':False,
            'independent_physics':False,'separate_host_qualification':False,'physical_motion_authorized':False}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('--out',type=Path);args=ap.parse_args()
    report=audit(args.directory)
    if args.out:
        with args.out.open('x') as f: json.dump(report,f,sort_keys=True,indent=2)
    print(json.dumps(report))
