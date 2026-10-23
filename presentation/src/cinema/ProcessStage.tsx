import {useEffect,useRef} from 'react'
import {drawProcess,visuals} from './process'
type Props={chapter:number;progress:number;blueprint:boolean;explode:number;onInspect:(title:string,detail:string)=>void;onReady:()=>void;reduced:boolean}
export default function ProcessStage({chapter,progress,blueprint,explode,onInspect,onReady,reduced}:Props){const canvas=useRef<HTMLCanvasElement>(null)
 useEffect(()=>{let alive=true;const draw=()=>{const c=canvas.current?.getContext('2d');if(c&&alive){c.save();c.scale(2,2);drawProcess(c,chapter,reduced?Math.floor(progress*4)/4:progress,blueprint,explode);c.restore();onReady()}};draw();void document.fonts.ready.then(draw);return()=>{alive=false}},[chapter,progress,blueprint,explode,onReady,reduced])
 return <div className="process-stage" data-visual={visuals[chapter].kind}><canvas ref={canvas} width={2400} height={1800} role="img" aria-label={visuals[chapter].description}/><div className="process-hotspots">{visuals[chapter].hotspots.map(([title,detail])=><button key={title} onMouseEnter={()=>onInspect(title,detail)} onFocus={()=>onInspect(title,detail)} onClick={()=>onInspect(title,detail)}><span>+</span>{title}</button>)}</div></div>
}
