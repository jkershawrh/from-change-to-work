import { describe,it,expect } from 'vitest'
import { parseLive,parseRecorded,canControl,failureMessage } from './contracts'
describe('action evidence boundaries',()=>{
 it('rejects physical authority and silent recorded substitution',()=>{
  for(const x of [{source:'REHEARSAL'},{source:'RETAINED_FLIGHTPATH_PROOF'},{source:'LIVE_SIMULATION',physical_motion_authorized:true}])expect(()=>parseLive(x)).toThrow()
 })
 it('requires retained proof identity and recorded scope',()=>{
  expect(()=>parseRecorded({schema:'aeris.recorded-action-proof.v1',source:'LIVE_SIMULATION'})).toThrow()
 })
 it('never offers fault controls to a viewer or stale session',()=>{
  expect(canControl('viewer',true,'RUNNING',20)).toBe(false)
  expect(canControl('operator',false,'RUNNING',20)).toBe(false)
  expect(canControl('operator',true,'COMPLETE',20)).toBe(false)
  expect(canControl('operator',true,'RUNNING',20)).toBe(true)
 })
})

it('explains a measured controller refusal without claiming recovery',()=>{expect(failureMessage({error:'STALE_OBSERVATION'})).toContain('did not complete');expect(failureMessage({error:'STALE_OBSERVATION'})).toContain('host load')})
