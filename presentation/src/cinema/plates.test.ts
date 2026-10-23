import {describe,it,expect,vi} from 'vitest'
import {drawPlate} from './plates'
import {frameAt} from './model'
describe('scene-boundary image contract',()=>{
 it('uses the next scene asset on the very first frame after the boundary',()=>{const images=new Map(['01-hangar','02-aircraft-detail','03-robot-cell'].map(name=>[name,{name,width:2560,height:1440} as unknown as HTMLImageElement]));const ctx={save:vi.fn(),beginPath:vi.fn(),rect:vi.fn(),clip:vi.fn(),drawImage:vi.fn(),restore:vi.fn()} as unknown as CanvasRenderingContext2D;const p={duration:82,chapters:[{id:'cell',start:0,end:37.75},{id:'recipe',start:37.75,end:82}]};for(const [time,name] of [[37.74,'03-robot-cell'],[37.75,'02-aircraft-detail'],[37.76,'02-aircraft-detail']] as const){const f=frameAt(p,time);drawPlate(ctx,images,f.index,f.progress,0,0,1280,855);expect(ctx.drawImage).toHaveBeenLastCalledWith(images.get(name),expect.any(Number),expect.any(Number),expect.any(Number),expect.any(Number))}})
 it('refuses a missing decoded image rather than exporting the previous scene',()=>{const ctx={} as CanvasRenderingContext2D;expect(()=>drawPlate(ctx,new Map(),1,0,0,0,100,100)).toThrow('Decoded scene image required')})
})
