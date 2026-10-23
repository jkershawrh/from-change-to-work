export type Frame={tick:number;q:number[];velocity:number[];simulation_seconds:number;goal_index:number}
export type Recorded={schema:'aeris.recorded-action-proof.v1';source:'RETAINED_FLIGHTPATH_PROOF';recorded_at:string;physical_motion_authorized:false;summary:{metrics:{total_control_ticks:number;total_physics_substeps:number};rubric:Rubric[];hosts:Record<string,string>;cpu:string;openshift_version:string};tasks:{task:string;status:string;release_digest:string;frames:Frame[];receipt:unknown}[];source_identities:Record<string,string>}
export type Rubric={id:string;status:'RED'|'AMBER'|'GREEN';reason?:string;scope?:string}
export type Intent={schema:'evy.capability-action.v1';action_id:string;skill_id:string;edge_id:string;release_digest:string}
export type Live={schema:'aeris.action-console-state.v1';source:'LIVE_SIMULATION';physical_motion_authorized:false;simulation_only:true;session_id:string;phase:string;observed_at_ms:number;separate_host:boolean;action:Intent|null;task:{task:string;status:string;ticks:number;release_digest:string;last_sample:{after:{q:number[];velocity:number[];simulation_seconds:number};tick:number;goal_index:number;observed_at_unix_ms:number}|null;receipt:unknown}|null;edge:{edge_id:string;recovery_required:boolean;active_digest:string|null;releases:{digest:string;skill_id:string;sequence:number}[];host:{system:string;architecture:string;cpu_model:string|null;os_release:string}};central:string;link:{connected:boolean;observer_channel:string};capabilities:string[];rubric:Rubric[]}
const need=(v:unknown,m:string)=>{if(!v)throw Error(m)}
export function parseLive(value:unknown):Live{
 const v=value as Live;need(v?.schema==='aeris.action-console-state.v1'&&v.source==='LIVE_SIMULATION'&&v.physical_motion_authorized===false&&v.simulation_only===true,'Live simulator evidence required.');need(typeof v.session_id==='string'&&Number.isSafeInteger(v.observed_at_ms)&&Array.isArray(v.rubric)&&v.edge&&Array.isArray(v.capabilities)&&v.link&&typeof v.link.connected==='boolean','Incomplete live observation.')
 if(v.task){need(v.action&&v.task.task==='action-'+v.action.action_id&&v.task.release_digest===v.action.release_digest,'Task and release binding mismatch.');need(Number.isSafeInteger(v.task.ticks)&&v.task.ticks>=0,'Invalid control count.');if(v.task.last_sample){const s=v.task.last_sample;need(s.after.q.length===6&&s.after.q.every(Number.isFinite)&&s.after.velocity.length===6&&s.after.velocity.every(Number.isFinite),'Invalid six-joint observation.')}}
 return v
}
export function parseRecorded(value:unknown):Recorded{
 const v=value as Recorded;need(v?.schema==='aeris.recorded-action-proof.v1'&&v.source==='RETAINED_FLIGHTPATH_PROOF'&&v.physical_motion_authorized===false,'Recorded proof identity required.');need(v.summary?.metrics&&Array.isArray(v.summary.rubric)&&Array.isArray(v.tasks)&&v.tasks.every(t=>Array.isArray(t.frames)&&t.frames.length>0&&t.frames.every(f=>f.q.length===6&&f.q.every(Number.isFinite))),'Incomplete retained proof.');return v
}
export function canControl(role:string|null,fresh:boolean,phase:string,ticks:number){return role==='operator'&&fresh&&phase==='RUNNING'&&ticks>=1}
export async function call(path:string,body?:unknown):Promise<unknown>{
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000)
 try{const r=await fetch('/api/action-demo'+path,{method:body===undefined?'GET':'POST',credentials:'same-origin',signal:controller.signal,headers:{'Content-Type':'application/json','x-aeris-action':'v1'},body:body===undefined?undefined:JSON.stringify(body)});const value=await r.json();if(!r.ok)throw Error(String(value.detail??'Action request refused.').replaceAll('_',' '));return value}finally{clearTimeout(timer)}
}

export function failureMessage(receipt:unknown){const r=receipt as {error?:unknown}|null;if(!r||typeof r.error!=='string')return 'The task did not complete. Inspect the execution receipt before starting a new action.';if(r.error==='STALE_OBSERVATION')return 'The controller refused a stale observation. Inspect host load and the receipt; this task did not complete.';return 'Controller refusal: '+r.error.replaceAll('_',' ')+'. No completion is claimed.'}
