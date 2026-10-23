import { Component,Suspense,useMemo,type ReactNode } from 'react'
import { Canvas,useLoader } from '@react-three/fiber'
import { ContactShadows,Grid,OrbitControls,Environment } from '@react-three/drei'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { Quaternion,Vector3,Mesh,MeshStandardMaterial,Color } from 'three'
export type Body={name:string;position:[number,number,number];quaternion_wxyz:[number,number,number,number];joint:{name:string;index:number;axis:[number,number,number]}|null;geometries:{mesh:string;rgba:number[]}[];children:Body[]}
function Geometry({mesh,rgba,blueprint,selected}:{mesh:string;rgba:number[];blueprint:boolean;selected:boolean}){
 const object=useLoader(OBJLoader,'/models/ur5e/'+mesh+'.obj')
 const clone=useMemo(()=>{const x=object.clone(true);x.traverse(o=>{if(o instanceof Mesh){o.material=new MeshStandardMaterial({color:new Color(rgba[0],rgba[1],rgba[2]),metalness:.55,roughness:.28,wireframe:blueprint,emissive:selected?'#0c5e6e':'#000000',emissiveIntensity:selected?.45:0});o.castShadow=true;o.receiveShadow=true}});return x},[object,rgba,blueprint,selected])
 return <primitive object={clone}/>
}
function Link({body,q,explode,blueprint,selected,onSelect,depth=0}:{body:Body;q:number[];explode:number;blueprint:boolean;selected:string;onSelect:(b:Body)=>void;depth?:number}){
 const rotation=useMemo(()=>{const [w,x,y,z]=body.quaternion_wxyz;const quaternion=new Quaternion(x,y,z,w).normalize();if(body.joint)quaternion.multiply(new Quaternion().setFromAxisAngle(new Vector3(...body.joint.axis).normalize(),q[body.joint.index]??0));return quaternion},[body,q])
 const p:[number,number,number]=[body.position[0]+explode*depth*.04,body.position[1],body.position[2]+explode*depth*.035]
 return <group position={p} quaternion={rotation}><group onClick={e=>{e.stopPropagation();onSelect(body)}} onPointerOver={e=>{e.stopPropagation();document.body.style.cursor='pointer';onSelect(body)}} onPointerOut={()=>{document.body.style.cursor=''}}>{body.geometries.map(g=><Geometry key={g.mesh} {...g} blueprint={blueprint} selected={selected===body.name}/>)}</group>{body.children.map(b=><Link key={b.name} body={b} q={q} explode={explode} blueprint={blueprint} selected={selected} onSelect={onSelect} depth={depth+1}/>)}</group>
}
class Boundary extends Component<{children:ReactNode},{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return{failed:true}}render(){return this.state.failed?<div className="action-graphics-fallback">3D is unavailable. Telemetry, controls and evidence remain accessible.</div>:this.props.children}}
export default function ArmScene({model,q,explode,blueprint,selected,onSelect}:{model:Body;q:number[];explode:number;blueprint:boolean;selected:string;onSelect:(b:Body)=>void}){
 return <Boundary><Canvas shadows frameloop="demand" dpr={[1,1.5]} camera={{position:[1.25,.95,1.15],fov:37}} gl={{antialias:true}}><color attach="background" args={['#0b151b']}/><ambientLight intensity={1.4}/><directionalLight position={[2,4,3]} intensity={3.5} castShadow shadow-mapSize={[1024,1024]}/><directionalLight position={[-2,1,-2]} intensity={2} color="#61d5f2"/><Suspense fallback={null}><group position={[0,-.26,0]} rotation={[-Math.PI/2,0,0]}><Link body={model} q={q} explode={explode} blueprint={blueprint} selected={selected} onSelect={onSelect}/></group><ContactShadows position={[0,-.26,0]} opacity={.55} scale={4} blur={2} far={3}/></Suspense><Grid position={[0,-.263,0]} args={[4,4]} cellSize={.1} sectionSize={.5} cellColor="#25414d" sectionColor="#365968" fadeDistance={4}/><OrbitControls makeDefault target={[0,.15,0]} minDistance={.8} maxDistance={3} maxPolarAngle={Math.PI*.49} enablePan={false}/></Canvas></Boundary>
}

// Shared presentation geometry; execution and calibration stay with the runtime.
export { Link as RobotAssembly }
