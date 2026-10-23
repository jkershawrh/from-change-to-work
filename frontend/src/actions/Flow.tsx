import { useMemo } from 'react'
import { ReactFlow,Background,type Node,type Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
const labels=['Operator','Dispatch / central','Signed release','Rust / edge','Simulator','Receipt']
export default function Flow({phase,disconnected,onInspect}:{phase:string;disconnected:boolean;onInspect:(s:string)=>void}){
 const running=['RUNNING','COMPLETE','RECOVERY_REQUIRED','INTERRUPTED'].includes(phase)
 const nodes:Node[]=useMemo(()=>labels.map((label,i)=>({id:String(i),width:139,height:36,position:{x:i*158,y:25},data:{label},style:{width:139,color:'#d6e4e8',background:'#14252e',border:'1px solid '+(disconnected&&i===1?'#e5a45a':running&&i>=3?'#52bca9':'#38515c'),fontFamily:'RedHatMono',fontSize:11,borderRadius:5}})),[phase,disconnected])
 const edges:Edge[]=useMemo(()=>labels.slice(1).map((_,i)=>({id:String(i),source:String(i),target:String(i+1),animated:running&&!disconnected&&i<3,style:{stroke:disconnected&&i<3?'#715b42':'#409eb3',strokeDasharray:disconnected&&i<3?'5 5':undefined}})),[phase,disconnected])
 return <ReactFlow nodes={nodes} edges={edges} fitView fitViewOptions={{padding:.12}} minZoom={.3} maxZoom={1.4} nodesDraggable={false} panOnDrag={false} zoomOnScroll={false} onNodeClick={(_,node)=>onInspect(labels[Number(node.id)])} proOptions={{hideAttribution:true}}><Background color="#29404a" gap={20}/></ReactFlow>
}
