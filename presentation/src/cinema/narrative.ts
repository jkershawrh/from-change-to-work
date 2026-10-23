export const AUDIO_EDITION='cinema-07'
export const FILM_NAME='from-change-to-work-announced.mp4'
export const visualContext=[
 {title:'The aerospace work waiting for a change',input:'Engineering has a task change',output:'One cell needs an approved task'},
 {title:'What travels from engineering to the cell',input:'A proposed task and receiving cell',output:'An approved, traceable work package'},
 {title:'Remote-to-robot handoff',input:'One approved task package',output:'A locally accepted task and result'},
 {title:'Local work when the central link is lost',input:'A task already accepted by the cell',output:'Completed work and a retained result'},
 {title:'A deliberate recovery decision',input:'An interrupted task and its history',output:'A recorded interruption; a new decision'},
 {title:'Reuse the handoff for another task',input:'A new use case and receiving profile',output:'The same process; a separately qualified task'},
 {title:'The first customer pilot',input:'One task, named hosts, an acceptance owner',output:'Measured rollout, recovery and task outcome'},
] as const
export type FlowBeat={event:number;time:number;phrase?:string}
export function flowStepAt(beats:FlowBeat[],time:number){let step=0;for(const beat of beats){if(time<beat.time)break;step=beat.event}return step}
export const packageLayers=[['01 / PROPOSED WORK','What the robot should do'],['02 / RECEIVING CELL','Where the task may run'],['03 / EXPECTED RESULT','What comes back to the operator']] as const
