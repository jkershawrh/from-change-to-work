import {describe,it,expect} from 'vitest'
import {visualContext,flowStepAt} from './narrative'
describe('audience narrative contract',()=>{
 it('names every visual, its input and its outcome in plain language',()=>{expect(visualContext).toHaveLength(7);for(const v of visualContext){expect(v.title.length).toBeGreaterThan(8);expect(v.input.length).toBeGreaterThan(8);expect(v.output.length).toBeGreaterThan(8);expect(JSON.stringify(v)).not.toMatch(/IPC|SQLite|WAL|personal views/)}})
 it('follows spoken event cues instead of dividing the chapter into seven equal intervals',()=>{const beats=[{event:0,time:10},{event:1,time:13},{event:2,time:16},{event:3,time:22},{event:4,time:26},{event:5,time:31},{event:6,time:38}];expect(flowStepAt(beats,12)).toBe(0);expect(flowStepAt(beats,23)).toBe(3);expect(flowStepAt(beats,50)).toBe(6)})
})
