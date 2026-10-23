import {describe,it,expect} from 'vitest'
import {frameAt,parseObservation,payoff} from './model'
describe('cinematic evidence and clock',()=>{
 it('clamps seeking and refuses non-finite input',()=>{const p={duration:320,chapters:[{id:'cell',start:0,end:50},{id:'recipe',start:50,end:320}]};expect(frameAt(p,-10).index).toBe(0);expect(frameAt(p,999).progress).toBe(1);expect(()=>frameAt(p,NaN)).toThrow()})
 it('never populates live payoff from animation or an unrun proof',()=>{expect(payoff(null)).toEqual({source:'NOT OBSERVED',status:'Run the workbench, then read its observations.',ticks:null});expect(()=>parseObservation({schema:'aeris.action-session-export.v1',physical_motion_authorized:true})).toThrow()})
 it('requires live identity and exact pinned task/release binding',()=>{expect(()=>parseObservation({schema:'aeris.action-session-export.v1',physical_motion_authorized:false,state:{source:'LIVE_SIMULATION'}})).toThrow()})
})
