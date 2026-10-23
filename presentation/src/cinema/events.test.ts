import {describe,it,expect} from 'vitest'
import {events,eventAt,eventPaths} from './events'
describe('causal 3D event flow',()=>{
 it('requires local acceptance and idle activation before execution',()=>{const ids=events.map(e=>e.id);expect(ids.indexOf('admit')).toBeLessThan(ids.indexOf('activate'));expect(ids.indexOf('activate')).toBeLessThan(ids.indexOf('execute'));expect(events.find(e=>e.id==='admit')!.detail).toContain('local approval');expect(events.find(e=>e.id==='activate')!.detail).toContain('idle')})
 it('keeps delivery, control and evidence as distinct bounded paths',()=>{expect(new Set(eventPaths.map(e=>e.lane))).toEqual(new Set(['delivery','control','evidence']));expect(eventPaths.filter(e=>e.lane==='control').every(e=>e.local)).toBe(true);expect(eventPaths.find(e=>e.from==='receipt')!.to).toBe('observer');expect(events.filter(e=>['admit','activate','execute','receipt'].includes(e.id)).every(e=>e.position[0]>.25)).toBe(true);expect(events.every(e=>e.source.length>0&&e.detail.length>40)).toBe(true)})
 it('supports stable end states and rejects invalid event clocks',()=>{expect(eventAt(0).id).toBe(events[0].id);expect(eventAt(1).id).toBe('receipt');expect(()=>eventAt(NaN)).toThrow();expect(()=>eventAt(Infinity)).toThrow()})
})
