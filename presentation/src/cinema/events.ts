/** Source-derived explanatory topology. These events are illustration, never a live execution stream. */
export type EventId='release'|'dispatch'|'deliver'|'admit'|'activate'|'execute'|'receipt'|'observer'
export const events:{id:EventId;title:string;question:string;detail:string;boundary:string;source:string;position:[number,number,number]}[]=[
 {id:'release',title:'Approved recipe',question:'What is allowed to travel?',detail:'Engineering prepares exact signed bounded joint goals for a configured simulator profile. No arbitrary driver, code or trained weights are installed.',boundary:'CENTRAL / PREPARATION',source:'services/capability_publisher.py',position:[-3.5,.55,-1.45]},
 {id:'dispatch',title:'Bind the request',question:'Where is this task allowed to go?',detail:'The dispatcher binds an immutable action ID to its configured edge destination and exact release. A changed identity cannot silently become another action.',boundary:'CENTRAL / INTENT',source:'integrations/evy/backend/actions/capability_transfer.py',position:[-3.35,.55,1.35]},
 {id:'deliver',title:'Deliver exact bytes',question:'What crosses the network?',detail:'Authenticated HTTPS moves the configured action and fetches the signed recipe. The curved route is illustrative, with no geographical or latency claim.',boundary:'NETWORK / DELIVERY',source:'services/edge_gateway.py',position:[-1,.55,-.25]},
 {id:'admit',title:'Local admission',question:'May this cell accept the change?',detail:'Rust checks signature, local approval, receiving profile, expiry, sequence and bounded content. Failure refuses admission; a signature is not physical safety approval.',boundary:'EDGE / ACCEPTANCE',source:'crates/aeris-skill-transfer/src/lib.rs',position:[1.15,.55,-1.45]},
 {id:'activate',title:'Activate while idle',question:'When can the release become active?',detail:'Activation requires an idle local executor. Starting a task pins the exact release and acquires local execution ownership before movement is requested.',boundary:'EDGE / OWNERSHIP',source:'crates/aeris-skill-transfer/src/action.rs',position:[3.35,.55,-.1]},
 {id:'execute',title:'Local execution',question:'Who owns the next move?',detail:'The local Rust controller advances MuJoCo through stepped IPC. Central traffic is outside this control loop. The diagram is not a servo-rate measurement.',boundary:'EDGE / CONTROL',source:'proof/skill_transfer_v2/simulator.py',position:[3.35,.55,2.35]},
 {id:'receipt',title:'Retain the outcome',question:'What can the operator account for?',detail:'SQLite WAL retains task identity, committed samples and the terminal receipt. A terminal retry returns the result without another movement; independent audit is separate.',boundary:'EDGE / EVIDENCE',source:'crates/aeris-skill-transfer/src/executor.rs',position:[1.05,.55,2.35]},
]
export const observer={id:'observer' as const,title:'Operator observation',position:[-2.25,.55,2.75] as [number,number,number],detail:'The authenticated console reads committed state over a separate management observer. This is not a safety channel or an independent audit.',source:'services/action_console/api.py'}
export function eventNode(id:EventId){const node=id==='observer'?observer:events.find(e=>e.id===id);if(!node)throw Error('Unknown event node');return node}
export const eventPaths:{from:EventId;to:EventId;lane:'delivery'|'control'|'evidence';local:boolean;label:string}[]=[
 {from:'release',to:'dispatch',lane:'delivery',local:false,label:'approved intent'},
 {from:'dispatch',to:'deliver',lane:'delivery',local:false,label:'authenticated HTTPS'},
 {from:'deliver',to:'admit',lane:'delivery',local:false,label:'exact signed bytes'},
 {from:'admit',to:'activate',lane:'control',local:true,label:'idle activation'},
 {from:'activate',to:'execute',lane:'control',local:true,label:'pinned task / local IPC'},
 {from:'execute',to:'receipt',lane:'evidence',local:true,label:'samples + receipt'},
 {from:'receipt',to:'observer',lane:'evidence',local:false,label:'separate management observation'},
]
export function eventAt(progress:number){if(!Number.isFinite(progress))throw Error('Finite event clock required');return events[Math.min(events.length-1,Math.floor(Math.max(0,Math.min(1,progress))*events.length))]}
