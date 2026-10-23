import {useEffect,useLayoutEffect,useRef,useState} from 'react'
import {plateFor} from './approvedScene'
import {loadPlates,drawPlate,type PlateImages} from './plates'
import {packageLayers} from './narrative'
import {visuals} from './process'
export default function CinematicPlate({chapter,progress,reduced,onInspect,onReady}:{chapter:number;progress:number;reduced:boolean;onInspect:(title:string,text:string)=>void;onReady:()=>void}){
 const canvas=useRef<HTMLCanvasElement>(null),[images,setImages]=useState<PlateImages|null>(null),[failed,setFailed]=useState(false),state=useRef({chapter,progress,reduced});state.current={chapter,progress,reduced}
 const name=plateFor(chapter,progress)
 useEffect(()=>{let alive=true;void loadPlates().then(v=>{if(alive)setImages(v)}).catch(()=>{if(alive)setFailed(true)});return()=>{alive=false}},[])
 useLayoutEffect(()=>{if(!images||!canvas.current)return;const element=canvas.current;const draw=()=>{const rect=element.getBoundingClientRect(),ratio=Math.min(devicePixelRatio,1.5);element.width=Math.max(1,Math.round(rect.width*ratio));element.height=Math.max(1,Math.round(rect.height*ratio));const s=state.current;drawPlate(element.getContext('2d')!,images,s.chapter,s.progress,0,0,element.width,element.height,s.reduced);onReady()};draw();const resize=new ResizeObserver(draw);resize.observe(element);return()=>resize.disconnect()},[images,chapter,progress,reduced,onReady])
 return <div className="cinematic-plate" data-approved-view={name}><canvas ref={canvas} data-cinematic-plate role="img" aria-label={'Approved Blender render: '+name+'; illustrative scenery only.'}/>{failed&&<p className="cine-webgl-fallback">Aircraft picture unavailable.</p>}{chapter===1&&<div className="cine-package-layers" aria-label="Exploded work package">{packageLayers.map(([title,text])=><div key={title}><b>{title}</b><span>{text}</span></div>)}</div>}<div className="process-hotspots">{visuals[chapter].hotspots.map(([title,text])=><button key={title} onMouseEnter={()=>onInspect(title,text)} onFocus={()=>onInspect(title,text)} onClick={()=>onInspect(title,text)}><span>+</span>{title}</button>)}</div></div>
}
