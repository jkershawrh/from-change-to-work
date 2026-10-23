import {describe,it,expect} from 'vitest'
import {cameraFor,plateFor,SCENE_ASSET} from './approvedScene'
describe('approved aircraft presentation contract',()=>{
 it('uses the reviewed images and a local prepared scene',()=>{expect(SCENE_ASSET).toContain('approved-aircraft');expect(plateFor(0,.1)).toBe('01-hangar');expect(plateFor(1,.1)).toBe('02-aircraft-detail');expect(plateFor(1,.9)).toBe('03-robot-cell')})
 it('keeps every camera finite and frames the approved cell separately from the whole aircraft',()=>{for(const mode of ['hangar','aircraft','detail','cell'] as const){const p=cameraFor(mode);expect([...p.position,...p.target].every(Number.isFinite)).toBe(true);expect(p.position).not.toEqual(p.target)}expect(cameraFor('cell').target[0]).toBe(9);expect(cameraFor('hangar').target[1]).toBe(6)})
})
