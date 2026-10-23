import {describe,it,expect} from 'vitest'
import {exportFrameReady} from './exportFrame'
describe('export WebGL scene identity',()=>{
 it('holds the previous complete picture until the matching scene has rendered',()=>{expect(exportFrameReady(2,'1')).toBe(false);expect(exportFrameReady(3,'2')).toBe(false);expect(exportFrameReady(2,undefined)).toBe(false);expect(exportFrameReady(2,'2')).toBe(true);expect(exportFrameReady(3,'3')).toBe(true)})
 it('does not gate synchronous images or process drawings on WebGL',()=>{for(const chapter of [0,1,4,5,6])expect(exportFrameReady(chapter,undefined)).toBe(true)})
})
