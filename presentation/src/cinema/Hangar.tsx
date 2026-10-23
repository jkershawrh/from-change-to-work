import {memo,useEffect,useMemo} from 'react'
import {useLoader,useThree} from '@react-three/fiber'
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js'
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js'
import {Mesh,MeshStandardMaterial,PMREMGenerator} from 'three'
import {SCENE_ASSET} from './approvedScene'
const asset=import.meta.env.BASE_URL+SCENE_ASSET
function Hangar({onInspect,blueprint=false}:{onInspect:(title:string,detail:string)=>void;blueprint?:boolean}){
 const loaded=useLoader(GLTFLoader,asset),{gl,scene,invalidate}=useThree()
 const object=useMemo(()=>{const copy=loaded.scene.clone(true);copy.name='approved-aircraft-hangar';copy.traverse(o=>{if(o instanceof Mesh){const materials=(Array.isArray(o.material)?o.material:[o.material]).map(m=>{const c=m.clone();if(c instanceof MeshStandardMaterial)c.wireframe=blueprint;return c});o.material=Array.isArray(o.material)?materials:materials[0];o.castShadow=!materials.some(m=>m.name.toLowerCase().includes('concrete'));o.receiveShadow=true}});return copy},[loaded,blueprint])
 useEffect(()=>()=>{object.traverse(o=>{if(o instanceof Mesh)(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose())})},[object])
 useEffect(()=>{const old=scene.environment,intensity=scene.environmentIntensity;const room=new RoomEnvironment(),pmrem=new PMREMGenerator(gl),target=pmrem.fromScene(room,.04);scene.environment=target.texture;scene.environmentIntensity=.7;room.dispose();pmrem.dispose();invalidate();return()=>{scene.environment=old;scene.environmentIntensity=intensity;target.dispose()}},[gl,scene,invalidate])
 return <primitive object={object} onPointerOver={(e:{stopPropagation:()=>void;object:Mesh})=>{e.stopPropagation();const m=e.object.material;const names=(Array.isArray(m)?m:[m]).map(v=>v?.name??'').join(' ');const aircraft=/C17|topcoat/i.test(names);onInspect(aircraft?'Approved aircraft / C-17':'Approved hangar / illustrative scene',aircraft?'The licensed aircraft geometry and review topcoat come from the approved Blender scene. Adapted from pilotcandle5470, CC BY 4.0. This is visual scenery, not an OEM CAD model or calibrated inspection target.':'The hangar, maintenance supports and fixtures come from the same approved scene. The articulated robot is supplied separately from the simulator geometry; scenery never grants execution authority.')}}/>
}
export default memo(Hangar)
