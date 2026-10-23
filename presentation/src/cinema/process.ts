/** Authored business illustrations. Never telemetry, geography, deployment or robot commands. */
export const visuals=[
 {kind:'production',description:'Illustrative aerospace production floor: engineering has a change, but the panel is waiting for an approved cell task. No production delay or cost has been measured.',hotspots:[['Waiting work','The buyer problem is the handoff between an approved engineering change and a task the receiving cell can accept. This airframe and work order are illustrative.'],['Engineering change','A candidate task is prepared centrally. The demo transfers a bounded positioning recipe; it does not perform defect detection or qualify an aircraft part.']]},
 {kind:'engineering',description:'An exploded work package separates the intended task, approved target and expected receipt. The illustration represents a signed bounded recipe, not a new robot driver.',hotspots:[['Task package','Bounded goals identify what the local simulator may execute. The package does not install a driver, arbitrary code or trained model.'],['Cell acceptance','Engineering release and local approval are distinct responsibilities. The receiving profile and local operating envelope must match.']]},
 {kind:'delivery',description:'A delivery journey crosses central preparation, a remote channel and local admission. The local acceptance boundary is explicit; no geographic or deployed fleet claim.',hotspots:[['Delivery channel','The central dispatcher binds an immutable action and configured destination. Delivery can retry without granting a new execution.'],['Acceptance boundary','Rust checks signature, local approval, profile, expiry, sequence and bounded content. Activation waits for an idle executor.']]},
 {kind:'execution',description:'Detailed 3D aerospace cell with retained simulator joint samples. The central data-plane cut leaves the separate management observer available.',hotspots:[['Local control','The local Rust executor pins the release and owns the task. The central data plane sits outside the controller loop.'],['Connection trial','The workbench cuts a real lab relay. This story replays retained evidence; it does not run a robot or simulate a safety stop.']]},
 {kind:'recovery',description:'A forked work-history timeline distinguishes completed work, interrupted work and a deliberately new task. Recovery never silently resumes uncertain motion.',hotspots:[['Interrupted work','Executor loss leaves uncertain work visible. Explicit recovery records the orphaned task as interrupted.'],['New decision','Retrying a terminal action returns its receipt. Another execution requires a deliberately new action identity.']]},
 {kind:'modules',description:'A reusable delivery spine connects qualified task modules. Inspection and rework positioning exist in simulation; machine tending and other profiles remain future concepts.',hotspots:[['Reusable spine','Repeat action binding, admission, pinned execution, retained receipt and recovery. Each module uses the same acceptance process.'],['Profile-specific work','New device interfaces, tooling, calibration and safeguards require reviewed adapters and independent acceptance. Reuse does not make every robot interchangeable.']]},
 {kind:'decision',description:'A pilot acceptance dossier connects business measurements with software and hardware gates. Value is an unmeasured hypothesis; physical and real-time qualification remain pending.',hotspots:[['Pilot decision','Choose one bounded task, named central and edge hosts, and an acceptance owner. Measure rollout effort, recovery effort and verified task outcome.'],['Evidence gates','TDD, EDD, CDD, BDD and CBT structure the tests. Local simulator evidence does not qualify new Intel and Red Hat hardware or physical motion.']]},
] as const
const cyan='#78d7ed',white='#e2eef2',muted='#85a5b4',amber='#e9b777',green='#85d6b7'
export function drawProcess(c:CanvasRenderingContext2D,chapter:number,progress:number,blueprint=false,explode=0){
 c.save();c.clearRect(0,0,1200,900);c.fillStyle='#081118';c.fillRect(0,0,1200,900)
 const glow=c.createRadialGradient(640,390,20,640,390,600);glow.addColorStop(0,'#153344');glow.addColorStop(1,'#081118');c.fillStyle=glow;c.fillRect(0,0,1200,900)
 const text=(s:string,x:number,y:number,size=18,color=muted,font='RedHatMono')=>{c.font=`${font==='RedHatDisplay'?'700 ':''}${size}px ${font}`;c.fillStyle=color;c.fillText(s,x,y)}
 const line=(pts:number[][],color=muted,width=1,dash:number[]=[])=>{c.beginPath();c.strokeStyle=color;c.lineWidth=width;c.setLineDash(dash);pts.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.stroke();c.setLineDash([])}
 const poly=(pts:number[][],fill:string,stroke='#51778b')=>{c.beginPath();pts.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fillStyle=fill;c.fill();c.strokeStyle=stroke;c.lineWidth=1;c.stroke()}
 const card=(x:number,y:number,w:number,h:number,color='#254c62')=>{c.fillStyle='#0b1c28';c.strokeStyle=color;c.lineWidth=1;c.beginPath();c.roundRect(x,y,w,h,9);c.fill();c.stroke()}
 const tag=(s:string,x:number,y:number,color=cyan)=>{c.font='13px RedHatMono';const w=c.measureText(s).width+24;card(x,y-21,w,31,color);text(s,x+12,y,13,color)}
 const iso=(x:number,y:number,z=0)=>[600+(x-y)*.72,510+(x+y)*.3-z]
 const box=(x:number,y:number,w:number,d:number,h:number,fill='#233f50')=>{const a=iso(x,y),b=iso(x+w,y),cc=iso(x+w,y+d),dd=iso(x,y+d),up=(v:number[])=>[v[0],v[1]-h];poly([a,b,up(b),up(a)],'#142c3c');poly([b,cc,up(cc),up(b)],'#1b3747');poly([up(a),up(b),up(cc),up(dd)],blueprint?'#0b2334':fill,blueprint?cyan:'#587587')}
 const ring=(x:number,y:number,r:number,color=cyan)=>{c.strokeStyle=color;c.lineWidth=1.5;c.beginPath();c.arc(x,y,r,0,Math.PI*2);c.stroke();c.fillStyle=color;c.beginPath();c.arc(x,y,3,0,Math.PI*2);c.fill()}
 const arrow=(x:number,y:number,color=cyan)=>{line([[x-12,y-8],[x,y],[x-12,y+8]],color,2)}
 // The shared visual context supplies the title, input and outcome.
 if(chapter===0){
  // Wide manufacturing-floor establishing shot, with an unmistakable airframe fixture.
  for(let i=-4;i<6;i++){line([iso(-480,i*110),iso(500,i*110)],'#1b3545');line([iso(i*110,-480),iso(i*110,500)],'#1b3545')}
  box(-290,-150,560,300,28);[-230,210].forEach(x=>[-100,100].forEach(y=>box(x,y,25,25,145)))
  const skin=[iso(-300,-130,130),iso(280,-130,145),iso(280,145,125),iso(-300,145,110)];poly(skin,blueprint?'#112b3b':'#608091',cyan)
  for(let i=0;i<13;i++){const x=-275+i*43;const a=iso(x,-125,128),b=iso(x,140,108);line([a,[a[0]+13,a[1]-34],[b[0]+13,b[1]-34],b],i%3===0?cyan:'#a6bdc6',1.3);for(let j=0;j<5;j++){const v=iso(x,-105+j*53,126-j*4);c.fillStyle='#d2e1e7';c.beginPath();c.arc(v[0],v[1],2,0,7);c.fill()}}
  line([[300,354],[180,260],[90,260]],amber);tag('PANEL / AWAITING APPROVED TASK',78,243,amber)
  card(755,150,325,164,'#556474');text('ENGINEERING',780,187,13,cyan);text('Change ready.',780,226,29,white,'RedHatDisplay');text('Release → receiving cell',780,264,15)
  line([[910,315],[910,440],[830,440]],amber,2,[5,7]);ring(910,366,19,amber);text('THE HANDOFF GAP',760,485,14,amber)
  tag('WORK ORDER / ILLUSTRATIVE',380,680);text('The part is here. The change is elsewhere.',222,738,26,white,'RedHatDisplay')
  if(progress>.64){line([[830,440],[785,440],[785,585],[690,585]],amber,2,[6,6]);tag('CAN THE CELL ACCEPT THIS CHANGE?',650,640,amber)}
  // An amber sweep exposes the release-to-work gap rather than pretending to measure waiting time.
  const pulse=progress;line([[240+pulse*470,570],[270+pulse*470,590]],amber,3)
 }else if(chapter===1){
  const lift=35+explode*90+Math.sin(progress*Math.PI)*35
  for(let i=0;i<3;i++){const y=470-i*(90+lift);poly([[280,y],[690,y-140],[1035,y+20],[620,y+160]],i===2?'#163d50':'#122a3a',i===2?cyan:'#42677e');for(let k=0;k<6;k++)line([[330+k*60,y-10-k*20],[640+k*60,y+124-k*20]],'#33586e');line([[1020,y+35],[1090,y+35]],i===2?cyan:muted);text(['EXPECTED RECEIPT','RECEIVING PROFILE','APPROVED TASK'][i],750,y+100,15,i===2?cyan:white)}
  // Engineering marks are illustrative task/profile/receipt symbols, never measured trajectories.
  const mid=470-2*(90+lift);line([[535,mid+15],[595,mid-30],[670,mid+5],[724,mid-28]],cyan,5);[[535,mid+15],[595,mid-30],[670,mid+5],[724,mid-28]].forEach(([x,y])=>ring(x,y,9,white));
  const prof=470-(90+lift);poly([[555,prof-7],[630,prof-32],[700,prof+2],[625,prof+27]],'#20465b',cyan);text('PROFILE',592,prof+4,12,cyan);
  for(let i=0;i<3;i++){line([[560,505+i*17],[700,460+i*17]],'#6b9aad');ring(548,509+i*17,4,green)}
  tag('ONE RELEASE / EXACT IDENTITY',338,168);tag('LOCAL ACCEPTANCE REMAINS LOCAL',350,760,green)
  text('Task intent',110,320,22,white,'RedHatDisplay');text('Target + limits',110,348,14);text('Result identity',110,376,14)
 }else if(chapter===2){
  // Deliberately different: a long-distance delivery diagram with a receiving boundary.
  for(let i=0;i<12;i++)line([[100,210+i*35],[1100,210+i*35]],'#102d3d')
  c.strokeStyle='#23536c';for(let i=0;i<7;i++){c.beginPath();c.ellipse(600,410,490-i*28,205,0,0,Math.PI*2);c.stroke()}
  const xs=[200,580,1000];xs.forEach((x,i)=>{ring(x,410,55,i===2?green:cyan);text(['ENGINEERING','DELIVERY','LOCAL CELL'][i],x-80,520,16,white);text(['Approve the task','Move exact bytes','Accept before work'][i],x-90,550,13)})
  c.strokeStyle=cyan;c.lineWidth=3;c.beginPath();c.moveTo(200,410);c.bezierCurveTo(380,200,790,200,1000,410);c.stroke();const t=progress*.9+.05,u=1-t,px=u*u*u*200+3*u*u*t*380+3*u*t*t*790+t*t*t*1000,py=u*u*u*410+3*u*u*t*200+3*u*t*t*200+t*t*t*410;poly([[px,py-14],[px+14,py],[px,py+14],[px-14,py]],white,cyan)
  line([[862,170],[862,650]],green,2,[7,8]);tag('LOCAL ACCEPTANCE BOUNDARY',746,158,green);tag('RECEIPT RETURNS / NOT REMOTE SERVO CONTROL',290,700)
 }else if(chapter===4){
  text('WHAT HAPPENED TO THE WORK?',110,188,30,white,'RedHatDisplay');line([[140,375],[1060,375]],'#487287',3)
  const items=[['STARTED',160,cyan],['INTERRUPTED',445,amber],['RECOVERED',730,amber],['NEW TASK',1030,green]];items.forEach(([s,x,col])=>{ring(Number(x),375,23,String(col));text(String(s),Number(x)-62,432,14,String(col))})
  line([[445,400],[445,570],[700,570]],amber,2);arrow(700,570,amber);card(710,525,365,101,'#8d6544');text('OLD TASK: INTERRUPTED',734,566,18,amber);text('No silent continuation.',734,598,15)
  line([[730,350],[730,270],[1030,270],[1030,350]],green,2);arrow(1030,323,green);text('Explicit new decision',744,240,18,green,'RedHatDisplay');tag('HISTORY SURVIVES / MOTION DOES NOT RESTART',216,732,amber)
  const p=140+920*progress;ring(p,375,6,white)
 }else if(chapter===5){
  text('ONE DELIVERY SPINE. DIFFERENT WORK.',100,180,29,white,'RedHatDisplay');line([[145,540],[1060,540]],cyan,3)
  const labels=['INSPECTION','REWORK','MACHINE TENDING'];labels.forEach((s,i)=>{const x=110+i*360;card(x,270,290,215,i===2?'#76654c':'#376882');text(i===2?'CONCEPT / NEW PROFILE':'SIMULATOR POSITIONING',x+20,303,11,i===2?amber:cyan);if(i===0){ring(x+145,370,34);line([[x+145,322],[x+145,420]],cyan);line([[x+96,370],[x+194,370]],cyan)}else if(i===1){poly([[x+104,351],[x+173,333],[x+190,390],[x+121,409]],'#244e62',cyan);line([[x+95,415],[x+204,326]],white,4)}else {poly([[x+100,345],[x+145,325],[x+190,345],[x+190,400],[x+145,420],[x+100,400]],'#263a46',amber)}text(s,x+20,457,19,white,'RedHatDisplay');line([[x+145,485],[x+145,540]],cyan,2);ring(x+145,540,8)})
  text('ADMIT  →  PIN  →  EXECUTE  →  RECEIPT  →  RECOVER',160,616,18,cyan);tag('REUSE THE PROCESS / QUALIFY EACH ADAPTER',270,730,amber)
 }else if(chapter===6){
  card(160,170,880,530,'#45667a');text('THE FIRST PILOT',200,225,14,cyan);text('One task. One cell. A decision.',200,275,35,white,'RedHatDisplay');line([[200,305],[1000,305]],'#31536a')
  const rows=[['BUSINESS','Rollout effort · handoffs · recovery effort','MEASURE'],['SOFTWARE','Transfer · disconnect · explicit recovery','SIMULATOR'],['COMPUTE','Named Intel + Red Hat hosts','QUALIFY'],['PHYSICAL','Reviewed adapter · cell acceptance','PENDING']];rows.forEach((r,i)=>{const y=354+i*80;text(r[0],200,y,12,i<2?cyan:amber);text(r[1],200,y+27,19,white,'RedHatText');tag(r[2],840,y+14,i===1?cyan:amber);if(i<3)line([[200,y+44],[1000,y+44]],'#254452')});tag('DECIDE FROM EVIDENCE / NO ASSUMED ROI',310,764)
 }
 c.restore()
}
