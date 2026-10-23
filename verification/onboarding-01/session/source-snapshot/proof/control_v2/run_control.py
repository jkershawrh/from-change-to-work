"""Offline six-axis simulation experiment. Rust owns planning and dispatch expiry.

Python bridges native MuJoCo plant/inverse dynamics and independent collision checks.
No UI, model worker, network database, or ledger participates in the control loop.
"""
import argparse
import hashlib
import json
import platform
import importlib.metadata
import sys
import subprocess
import time
from pathlib import Path

import mujoco
import numpy as np

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
CFG=json.loads((ROOT/'preregistration.json').read_text())
HOME=np.array([-1.5708,-1.5708,1.5708,-1.5708,-1.5708,0.])
DT=.02; VMAX=.45; AMAX=1.2
PLANNER_VMAX=.40; PLANNER_AMAX=.85; TOL=1e-6
BINARY=ROOT/"controller/target/release/aeris-control-v2"


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False))


def lineage():
    files=[ROOT/'preregistration.json',ROOT/'scene.xml',Path(__file__),ROOT/'audit_control.py',ROOT/'test_audit.py',ROOT/'controller/Cargo.lock',ROOT/'controller/Cargo.toml',ROOT/'controller/src/lib.rs',ROOT/'controller/src/main.rs']
    files+=sorted(p for p in (REPO/'proof/control/assets/ur5e').rglob('*') if p.is_file())
    result={str(p.relative_to(REPO)):sha(p) for p in files}
    result['binary']=sha(BINARY)
    return result


class Worker:
    def __init__(self):
        self.p=subprocess.Popen([str(BINARY)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
        self.sequence=0
    def send(self,obj):
        self.p.stdin.write(json.dumps(obj,allow_nan=False)+'\n');self.p.stdin.flush()
        response=self.p.stdout.readline()
        if not response:raise RuntimeError(f'Controller exited: {self.p.poll()}')
        return json.loads(response)
    def plan(self,q,v,target,age=0.,sequence=None):
        if sequence is None:self.sequence+=1;sequence=self.sequence
        return self.send({'type':'plan','payload':{'sequence':sequence,'observation_age_ms':age,'q':list(q),'velocity':list(v),'target':list(target)}})
    def dispatch(self,plan,clear):return self.send({'type':'dispatch','payload':{'sequence':plan['sequence'],'collision_clear':bool(clear)}})
    def close(self):
        self.p.stdin.close();self.p.wait(timeout=5)
        if self.p.returncode:raise RuntimeError(f'Controller exit {self.p.returncode}')


def load_model():
    model=mujoco.MjModel.from_xml_path(str(ROOT/'scene.xml'))
    model.opt.timestep=.002
    # Explicit simulation adapter: native bounded torque actuators, not the OEM servo.
    model.actuator_gainprm[:]=0.;model.actuator_gainprm[:,0]=1.
    model.actuator_biasprm[:]=0.;model.actuator_ctrlrange[:]=model.actuator_forcerange
    return model


def contacts(model,data):
    return [{'geom1':int(c.geom1),'geom2':int(c.geom2),'distance_m':float(c.dist)} for c in data.contact if c.dist < -1e-6]


def clear_path(model,check,current,positions):
    prev=np.array(current)
    for position in [current]+positions:
        target=np.array(position);steps=max(1,int(np.ceil(np.max(np.abs(target-prev))/.01)))
        for fraction in np.linspace(1/steps,1,steps):
            check.qpos[:]=prev+(target-prev)*fraction;check.qvel[:]=0.
            mujoco.mj_forward(model,check)
            found=contacts(model,check)
            if found:return False,found
        prev=target
    return True,[]


def simulate_interval(plant,data,nominal,inverse,u,disturbance):
    maximum={'speed':0.,'acceleration':0.,'native_acceleration':0.,'position_offset':0.,'torque_ratio':0.};found=[];substeps=[]
    for substep in range(10):
        inverse.qpos[:]=data.qpos;inverse.qvel[:]=data.qvel;inverse.qacc[:]=u
        mujoco.mj_inverse(nominal,inverse)
        requested=inverse.qfrc_inverse.copy()
        data.ctrl[:]=np.clip(requested,plant.actuator_forcerange[:,0],plant.actuator_forcerange[:,1])
        data.qfrc_applied[:]=disturbance
        before=data.qvel.copy();mujoco.mj_step(plant,data)
        acceleration=(data.qvel-before)/.002
        hit=contacts(plant,data);found.extend(hit)
        step={'index':substep,'simulation_seconds':float(data.time),'q':data.qpos.tolist(),'velocity_before':before.tolist(),'velocity':data.qvel.tolist(),'finite_difference_acceleration':acceleration.tolist(),'native_acceleration':data.qacc.tolist(),'requested_torque_nm':requested.tolist(),'applied_torque_nm':data.ctrl.tolist(),'disturbance_nm':disturbance.tolist(),'contacts':hit}
        substeps.append(step)
        maximum['speed']=max(maximum['speed'],float(np.max(np.abs(data.qvel))))
        maximum['acceleration']=max(maximum['acceleration'],float(np.max(np.abs(acceleration))))
        maximum['native_acceleration']=max(maximum['native_acceleration'],float(np.max(np.abs(data.qacc))))
        maximum['position_offset']=max(maximum['position_offset'],float(np.max(np.abs(data.qpos-HOME))))
        maximum['torque_ratio']=max(maximum['torque_ratio'],float(np.max(np.abs(data.ctrl)/plant.actuator_forcerange[:,1])))
    return maximum,found,substeps


def episode(worker,nominal,plant,case,target,perturbed,rng):
    data=mujoco.MjData(plant);check=mujoco.MjData(plant);inverse=mujoco.MjData(nominal)
    mujoco.mj_resetDataKeyframe(plant,data,0);data.ctrl[:]=0.;mujoco.mj_forward(plant,data)
    held=0;trace=[];complete=False;violations=[];latencies=[];dispatch_times=[];rejections={}
    maxima={'speed':0.,'acceleration':0.,'native_acceleration':0.,'position_offset':0.,'torque_ratio':0.}
    amplitude=np.array([.05,.05,.03,.003,.003,.003]) if perturbed else np.zeros(6)
    phase=rng.uniform(0,2*np.pi,6)
    amplitude*=rng.uniform(.5,1.,6)
    for tick in range(int(CFG['max_episode_seconds']/DT)):
        start=time.perf_counter_ns()
        q_before=data.qpos.copy();v_before=data.qvel.copy()
        plan=worker.plan(q_before,v_before,target)
        latencies.append(plan['solve_ms'])
        clear=False;prediction=[];contact_prediction=[]
        if plan['status']=='PLANNED':
            prediction=plan['positions'];clear,contact_prediction=clear_path(plant,check,q_before,prediction)
            response=worker.dispatch(plan,clear)
        else:response=plan
        dispatch_ms=(time.perf_counter_ns()-start)/1e6;dispatch_times.append(dispatch_ms)
        if response['status']=='DISPATCHED':u=np.array(response['acceleration']);outcome='DISPATCHED'
        else:
            outcome=response['reason'];rejections[outcome]=rejections.get(outcome,0)+1
            u=np.clip(-data.qvel/DT,-PLANNER_AMAX,PLANNER_AMAX)
        disturbance=amplitude*np.sin(2*np.pi*data.time+phase)
        maxima_tick,found,substeps=simulate_interval(plant,data,nominal,inverse,u,disturbance)
        for name,value in maxima_tick.items():maxima[name]=max(maxima[name],value)
        error=float(np.max(np.abs(data.qpos-target)))
        current=[]
        if maxima_tick['speed']>VMAX+TOL:current.append('MEASURED_VELOCITY_LIMIT')
        if max(maxima_tick['acceleration'],maxima_tick['native_acceleration'])>AMAX+TOL:current.append('MEASURED_ACCELERATION_LIMIT')
        if maxima_tick['position_offset']>.65+TOL:current.append('MEASURED_POSITION_LIMIT')
        if found:current.append('FORBIDDEN_CONTACT')
        for reason in current:
            if reason not in violations:violations.append(reason)
        held=held+1 if error<.015 and np.max(np.abs(data.qvel))<.025 and not violations else 0
        trace.append({'tick':tick,'simulation_seconds':float(data.time),'q_before':q_before.tolist(),'velocity_before':v_before.tolist(),'q':data.qpos.tolist(),'velocity':data.qvel.tolist(),'target':target.tolist(),'acceleration_command':u.tolist(),'outcome':outcome,'solve_ms':plan['solve_ms'],'roundtrip_and_gate_ms':dispatch_ms,'max_primal_residual':plan['max_primal_residual'],'predicted_first_q':prediction[0] if prediction else None,'first_prediction_error_rad':float(np.max(np.abs(data.qpos-prediction[0]))) if prediction else None,'actual_contacts':len(found),'predicted_contacts':contact_prediction,'measured':maxima_tick,'physics_substeps':substeps})
        if held>=10:complete=True;break
        # Any measured breach stops this episode and remains a failed outcome.
        if current:break
    return {'case':case,'condition':'perturbed' if perturbed else 'nominal','target':target.tolist(),'complete':complete,'simulated_seconds':float(data.time),'final_error_rad':error,'violations':violations,'rejections':rejections,'disturbance_phase':phase.tolist(),'disturbance_amplitude_nm':amplitude.tolist(),'maxima':maxima,'solve_ms':latencies,'dispatch_ms':dispatch_times,'trace':trace}


def faults(worker,nominal):
    results=[]
    def record(name,response,expected):
        results.append({'fault':name,'status':response['status'],'reason':response['reason'],'pass':response['status']=='REJECTED' and response['reason'] in expected})
    record('stale observation',worker.plan(HOME,np.zeros(6),HOME,age=80.),['STALE_OBSERVATION'])
    p=worker.plan(HOME,np.zeros(6),HOME)
    record('replayed sequence',worker.plan(HOME,np.zeros(6),HOME,sequence=p['sequence']),['REPLAYED_SEQUENCE'])
    record('malformed request',worker.send({'type':'plan','payload':{'q':[0]}}),['MALFORMED_REQUEST'])
    record('out-of-recipe target',worker.plan(HOME,np.zeros(6),HOME+1.),['TARGET_OUTSIDE_RECIPE'])
    q=HOME.copy();q[0]+=.629;v=np.zeros(6);v[0]=VMAX
    r=worker.plan(q,v,HOME)
    results.append({'fault':'infeasible braking','status':r['status'],'reason':r['reason'],'pass':r['status']=='REJECTED' and r['acceleration'] is None})
    p=worker.plan(HOME,np.zeros(6),HOME)
    time.sleep(.03)
    record('expired plan',worker.dispatch(p,True),['DEADLINE_EXPIRED'])
    # Find an actual obstacle that leaves the current pose clear but intersects a horizon pose.
    obstacle=nominal.geom('challenge_obstacle').id
    check=mujoco.MjData(nominal);rng=np.random.default_rng(504)
    obstruction=None
    for _ in range(40):
        target=HOME+rng.uniform(-.35,.35,6);p=worker.plan(HOME,np.zeros(6),target)
        if p['status']!='PLANNED':continue
        check.qpos[:]=p['positions'][-1];mujoco.mj_forward(nominal,check)
        point=check.site_xpos[0]+check.site_xmat[0].reshape(3,3)[:,2]*.008
        nominal.geom_pos[obstacle]=point
        current_clear,_=clear_path(nominal,check,HOME,[])
        future_clear,found=clear_path(nominal,check,HOME,p['positions'])
        if current_clear and not future_clear:
            # Re-solve to avoid counting scenario construction as controller gate latency.
            p=worker.plan(HOME,np.zeros(6),target)
            clear,found=clear_path(nominal,check,HOME,p['positions'])
            response=worker.dispatch(p,clear)
            obstruction={'fault':'obstructed trajectory','status':response['status'],'reason':response['reason'],'pass':response['status']=='REJECTED' and response['reason']=='COLLISION_GATE','obstacle_position':point.tolist(),'contacts':found,'current_pose_clear':True,'target':target.tolist(),'horizon':p['positions']}
            break
        nominal.geom_pos[obstacle]=[10,10,10]
    nominal.geom_pos[obstacle]=[10,10,10]
    results.append(obstruction or {'fault':'obstructed trajectory','pass':False,'reason':'FAILED_TO_CONSTRUCT_CLEAR_START_OBSTRUCTION'})
    return results


def run(mode):
    out=ROOT/'runs'/mode;out.mkdir(parents=True,exist_ok=True)
    if any(out.glob('*.json')):raise RuntimeError('Existing evidence retained; choose a new registered run for another evaluation.')
    if mode=='evaluation':
        frozen=json.loads((ROOT/'frozen.json').read_text())
        assert lineage()==frozen['sha256'],'Source/model changed after freeze'
    rng=np.random.default_rng(CFG['development_seed'] if mode=='development' else CFG['evaluation_seed'])
    nominal=load_model();plant=load_model();mass=plant.body_mass.copy();inertia=plant.body_inertia.copy()
    worker=Worker();records=[]
    counts=[(False,CFG['development_nominal_episodes']),(True,CFG['development_perturbed_episodes'])] if mode=='development' else [(False,CFG['nominal_episodes']),(True,CFG['perturbed_episodes'])]
    try:
        for perturbed,count in counts:
            for i in range(count):
                scale=([.85,1.15,float(rng.uniform(.85,1.15))][i%3]) if perturbed else 1.
                plant.body_mass[:]=mass;plant.body_inertia[:]=inertia
                plant.body_mass[-1]*=scale;plant.body_inertia[-1]*=scale
                mujoco.mj_setConst(plant,mujoco.MjData(plant))
                target=HOME+rng.uniform(-.35,.35,6)
                r=episode(worker,nominal,plant,f'{"perturbed" if perturbed else "nominal"}-{i:03d}',target,perturbed,rng)
                r['distal_mass_scale']=scale;records.append(r)
                save(out/f'{r["case"]}.json',r)
                print(f'{r["case"]}: complete={r["complete"]} error={r["final_error_rad"]:.4f} time={r["simulated_seconds"]:.2f} violations={r["violations"]} rejections={r["rejections"]}',flush=True)
        fault_results=faults(worker,nominal)
    finally:worker.close()
    groups={}
    for name in ['nominal','perturbed']:
        rows=[r for r in records if r['condition']==name]
        solve=np.concatenate([r['solve_ms'] for r in rows]);dispatch=np.concatenate([r['dispatch_ms'] for r in rows])
        groups[name]={'episodes':len(rows),'completed':sum(r['complete'] for r in rows),'completion_rate':float(np.mean([r['complete'] for r in rows])),'cycle_seconds_median':float(np.median([r['simulated_seconds'] for r in rows])),'cycle_seconds_max':max(r['simulated_seconds'] for r in rows),'control_ticks':sum(len(r['trace']) for r in rows),'physical_substeps':sum(10*len(r['trace']) for r in rows),'max_final_error_rad':max(r['final_error_rad'] for r in rows),'violating_episodes':sum(bool(r['violations']) for r in rows),'solve_ms_p50':float(np.median(solve)),'solve_ms_p99':float(np.quantile(solve,.99)),'solve_ms_max':float(solve.max()),'roundtrip_gate_ms_p99':float(np.quantile(dispatch,.99)),'maxima':{k:max(r['maxima'][k] for r in rows) for k in rows[0]['maxima']},'rejections':{reason:sum(r['rejections'].get(reason,0) for r in rows) for reason in sorted({reason for r in rows for reason in r['rejections']})}}
    gate=groups['nominal']['completion_rate']>=.95 and groups['nominal']['violating_episodes']==0 and groups['nominal']['solve_ms_p99']<10 and all(f['pass'] for f in fault_results)
    report={'id':CFG['id'],'mode':mode,'data_origin':'SYNTHETIC_PLANT','execution':'EXECUTED','robot':'Menagerie UR5e six-axis model','host':platform.platform(),'machine':platform.machine(),'python':sys.version,'dependencies':{name:importlib.metadata.version(name) for name in ['numpy','mujoco']},'mujoco':mujoco.__version__,'controller':'Rust / Clarabel 0.11.1 / 20-step heuristic-tightened acceleration MPC','physical_limits':CFG['physical_limits'],'planner_limits':CFG['planner_limits'],'formal_robustness_proved':False,'physical_robot':False,'intel_execution':False,'jepa_participated':False,'llm_participated':False,'ledger_participated':False,'groups':groups,'faults':fault_results,'proposed_nominal_gate_pass':gate,'robustness_gate_pass':gate and groups['perturbed']['violating_episodes']==0 and groups['perturbed']['completion_rate']>=.95 and groups['perturbed']['solve_ms_p99']<10,'artifact_sha256':{p.name:sha(p) for p in sorted(out.glob('*.json'))},'limitations':CFG['limitations']}
    save(out/'report.json',report)
    print(json.dumps({k:report[k] for k in ['groups','proposed_nominal_gate_pass','robustness_gate_pass']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['development','freeze','evaluation']);args=parser.parse_args()
    if args.mode=='freeze':
        assert (ROOT/'runs/development/report.json').exists(),'Run development first'
        assert not (ROOT/'frozen.json').exists(),'Already frozen'
        save(ROOT/'frozen.json',{'sha256':lineage(),'frozen_at_unix':time.time(),'source_commit':CFG['source_commit'],'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),'development_report_sha256':sha(ROOT/'runs/development/report.json'),'scope':'Empirical heuristic-tightening validation only; no formal robustness or safety claim'})
    else:run(args.mode)
