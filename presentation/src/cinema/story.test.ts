import {describe,it,expect} from 'vitest'
import {chapters} from './chapters'
import {visuals} from './process'
describe('business narrative contract',()=>{
 it('earns the technical trial with a business problem and a delivery journey',()=>{expect(chapters[0].title).toContain('waiting');expect(visuals.map(v=>v.kind)).toEqual(['production','engineering','delivery','execution','recovery','modules','decision'])})
 it('gives each chapter a different visual and an inspectable causal explanation',()=>{expect(new Set(visuals.map(v=>v.kind)).size).toBe(7);for(const v of visuals){expect(v.hotspots.length).toBeGreaterThan(1);expect(v.description.length).toBeGreaterThan(40)}})
 it('keeps reused project identities out of audience chapter copy',()=>{expect(JSON.stringify(chapters)).not.toMatch(/EVY|AERIS/);expect(JSON.stringify(visuals)).not.toMatch(/EVY|AERIS/);expect(visuals[0].description).toContain('Illustrative')})
})
