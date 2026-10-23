import {describe,it,expect} from 'vitest'
import {drawChapterCallouts} from './record'
function labels(index:number){const values:string[]=[];drawChapterCallouts(index,.55,400,value=>{values.push(value);return 0},()=>{});return values.join('\n')}
describe('export chapter isolation',()=>{
 it('shows the delivery journey without importing the later connection-cut claim',()=>{const text=labels(2);expect(text).toContain('Engineering');expect(text).toContain('Local acceptance');expect(text).not.toContain('CENTRAL DATA PLANE / CUT');expect(text).not.toContain('Local execution owns the task.')})
 it('reserves the cut claim for the execution trial',()=>{expect(labels(3)).toContain('CENTRAL DATA PLANE / CUT');for(const i of [0,1,4,5,6])expect(labels(i)).not.toContain('CENTRAL DATA PLANE / CUT')})
})
