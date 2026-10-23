import {useMemo,useRef} from 'react'
import {useFrame} from '@react-three/fiber'
import {Billboard,Line} from '@react-three/drei'
import {Vector3,type Mesh} from 'three'
import SceneLabel from './SceneLabel'
const colors=['#83d8ed','#e5bf86','#8ee4b9']
/** Three visible responsibilities. Detailed admission checks stay in the inspector. */
export default function EventFlow({step,progress,reduced,onSelect,onHover,blueprint}:{step:number;progress:number;reduced:boolean;onSelect:(index:number)=>void;onHover:(index:number)=>void;blueprint:boolean}){
 const phase=step<2?0:step===2?1:2,packet=useRef<Mesh>(null),start=useMemo(()=>new Vector3(),[])
 useFrame(()=>{if(packet.current){const p=reduced?.5:(progress*3)%1;packet.current.position.copy(start.set(-3.2+p*6.4,.8+Math.sin(p*Math.PI)*.4,.15));packet.current.rotation.y=reduced?0:progress*8}})
 return <group name="remote-to-robot-overview">
  <mesh position={[0,-.45,0]} receiveShadow><boxGeometry args={[10,.12,3.8]}/><meshStandardMaterial color="#284958" metalness={.3} roughness={.5} wireframe={blueprint}/></mesh>
  {[-3.2,0,3.2].map((x,i)=><group key={i} position={[x,0,0]} onClick={e=>{e.stopPropagation();onSelect([0,2,3][i])}} onPointerOver={e=>{e.stopPropagation();onHover([0,2,3][i])}}>
   <mesh position={[0,-.28,0]}><cylinderGeometry args={[1.25,1.35,.2,48]}/><meshStandardMaterial color={phase===i?'#486c78':'#314f60'} metalness={.45} roughness={.35} wireframe={blueprint}/></mesh>
   <mesh rotation={[-Math.PI/2,0,0]} position={[0,-.17,0]}><torusGeometry args={[1.12,.025,10,64]}/><meshBasicMaterial color={colors[i]}/></mesh>
   {i===0?<group><mesh position={[0,.4,-.12]}><boxGeometry args={[1.14,1.08,.35]}/><meshStandardMaterial color="#88aab8" metalness={.6} roughness={.3} wireframe={blueprint}/></mesh>{[-.03,.25,.53,.81].map(y=><mesh key={y} position={[0,y,.063]}><boxGeometry args={[.91,.1,.02]}/><meshStandardMaterial color="#183746" emissive="#22647a" emissiveIntensity={.25}/></mesh>)}</group>:i===1?<group rotation={[0,.3,0]}>{[0,1,2].map(j=><mesh key={j} position={[0,.12+j*.22,0]}><boxGeometry args={[.9,.12,.75]}/><meshStandardMaterial color={j===1?'#e4c18c':'#92bdca'} metalness={.5} roughness={.28} wireframe={blueprint}/></mesh>)}</group>:<group>
    <mesh position={[0,.04,0]}><cylinderGeometry args={[.34,.46,.4,32]}/><meshStandardMaterial color="#a1c6ce" metalness={.65} roughness={.25}/></mesh><mesh position={[-.15,.53,0]} rotation={[0,0,-.4]}><capsuleGeometry args={[.17,.7,8,20]}/><meshStandardMaterial color="#afd4da" metalness={.65} roughness={.25} wireframe={blueprint}/></mesh><mesh position={[.22,.96,0]} rotation={[0,0,1.15]}><capsuleGeometry args={[.14,.65,8,20]}/><meshStandardMaterial color="#a7cbd2" metalness={.65} roughness={.25} wireframe={blueprint}/></mesh><mesh position={[.65,1.11,0]}><boxGeometry args={[.25,.26,.3]}/><meshStandardMaterial color="#68b598" metalness={.6} roughness={.3}/></mesh>
   </group>}
   <Billboard position={[0,2.05,0]}><SceneLabel title={['ENGINEERING','DELIVERY','RECEIVING CELL'][i]} subtitle={['Approve the task','Carry the package','Accept · execute · report'][i]} width={2.8} titleSize={67} subtitleSize={31} color={phase===i?colors[i]:'#b3cbd4'}/></Billboard>
  </group>)}
  <Line points={[[-2,.7,.2],[-1.4,.7,.2]]} color={colors[1]} lineWidth={4}/><Line points={[[1.4,.7,.2],[2,.7,.2]]} color={colors[2]} lineWidth={4}/>
  <mesh ref={packet}><octahedronGeometry args={[.12]}/><meshStandardMaterial color="#f5deb4" emissive="#b78f4a" emissiveIntensity={.5}/></mesh>
  <Line points={[[3.2,-.1,1.35],[3.2,-.1,1.65],[-3.2,-.1,1.65],[-3.2,-.1,1.35]]} color="#e4c18c" lineWidth={2} dashed dashSize={.15} gapSize={.12}/>
  <Billboard position={[0,.05,2.1]}><SceneLabel title="RESULT RETURNS TO THE OPERATOR" width={3.5} titleSize={42} color="#e4c18c"/></Billboard>
 </group>
}
