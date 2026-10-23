import {exportFrameReady} from './exportFrame'
import {loadPlates,drawPlate} from './plates'
import {drawProcess} from './process'
import {visualContext,packageLayers,flowStepAt} from './narrative'
import {chapters} from './chapters'
import {frameAt,type Plan} from './model'
type DrawText=(value:string,x:number,y:number,width:number,size?:number,color?:string,font?:string,line?:number)=>number
type DrawPanel=(x:number,y:number,w:number,h:number,stroke?:string)=>void
/** One callout composition per chapter; shared by export and its semantic regression test. */
export function drawChapterCallouts(index:number,progress:number,y:number,text:DrawText,panel:DrawPanel,eventStep?:number){const f={index,progress},chapter=chapters[index]
  if(f.index===0){panel(50,y,490,115);text('THE QUESTION',70,y+29,430,12,'#7eb4c8','RedHatMono');text(chapter.question,70,y+67,445,24,'#cfe7ef')}
  else if(f.index===1){panel(49,y,510,215);text('APPROVED CAPABILITY',72,y+33,450,13,'#8dd2df','RedHatMono');['One bounded task','An approved release','A named receiving cell','A result tied to the request'].forEach((s,i)=>text(s,72,y+74+i*34,450,21,i===3?'#91aebe':'#cae1eb'))}
  else if(f.index===2){const active=eventStep===undefined?Math.min(2,Math.floor(f.progress*3)):eventStep<2?0:eventStep===2?1:2;[['Engineering','Release one approved task.'],['Delivery','Carry the exact package.'],['Local acceptance','Accept it before work begins.']].forEach(([title,detail],i)=>{panel(49,y+i*84,610,72,i===active?'#78d7ed':'#2a475a');text(String(i+1).padStart(2,'0'),70,y+43+i*84,45,14,'#78d7ed','RedHatMono');text(title,121,y+31+i*84,500,24,'#d9eaf2','RedHatDisplay');text(detail,121,y+58+i*84,500,17,'#91b4c6')})}
  else if(chapter.id==='disconnect'){panel(49,y,610,186,'#8b6445');text('CENTRAL DATA PLANE / CUT',72,y+34,550,13,'#e1b27f','RedHatMono');text('Local execution owns the task.',72,y+79,550,28,'#b5decf','RedHatDisplay');text('Separate observer available.\nRetained simulator playback, not a safety stop.',72,y+117,550,19,'#a2bdcd')}
  else if(f.index===4){['INTERRUPTED EXECUTOR','RECOVERY REQUIRED','EXPLICIT RECOVERY','DELIBERATELY NEW ACTION'].forEach((s,i)=>{panel(49,y+i*54,570,43);text(String(i+1).padStart(2,'0')+' / '+s,69,y+29+i*54,530,13,'#c4dce7','RedHatMono')})}
  else if(f.index===5){['Inspection / existing simulator task','Rework / same delivery and recovery','Next task / reviewed adapter still required'].forEach((s,i)=>{panel(49,y+i*68,620,54,i===2?'#7e6a4a':'#3b6178');text(s,70,y+35+i*68,580,20,'#c5e1ec')})}
  else if(f.index===6){panel(49,y,650,224);text('THE NEXT HARDWARE PROOF',72,y+35,590,12,'#d1b280','RedHatMono');text('Named hosts. Bounded task. Acceptance owner.',72,y+80,590,23,'#cfe7ee','RedHatDisplay');text('Dashboard + agent start packet\nTransfer · cut · recovery · independent audit',72,y+125,590,21,'#9fc4d5');text('Physical motion and real time remain separate gates.',72,y+196,590,15,'#c2ab87')}
}
/** Capture the real WebGL cell with export typography; never calls an action API. */
export async function recordStory(plan:Plan,onFrame:(t:number)=>void){
 await document.fonts.ready
 const plates=await loadPlates()
 await Promise.all([document.fonts.load('700 64px RedHatDisplay'),document.fonts.load('24px RedHatText'),document.fonts.load('15px RedHatMono')])
 const logos=[...document.querySelectorAll<HTMLImageElement>('.cine-header .brand-lockup img')];await Promise.all(logos.map(i=>i.decode()))
 const canvas=document.createElement('canvas');canvas.width=1920;canvas.height=1080;const c=canvas.getContext('2d')!
 const stream=canvas.captureStream(25);const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8'].find(t=>MediaRecorder.isTypeSupported(t));if(!mime)throw Error('Film recording requires browser MediaRecorder.')
 const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:10000000});const chunks:Blob[]=[];recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)}
 const stopped=new Promise<void>((resolve,reject)=>{recorder.onstop=()=>resolve();recorder.onerror=()=>reject(Error('Film recording failed.'))})
 function text(value:string,x:number,y:number,width:number,size=25,color='#b9d2df',font='RedHatText',line=size*1.4){c.fillStyle=color;c.font=`${font==='RedHatDisplay'?'700 ':''}${size}px ${font}`;let cy=y;for(const para of value.split('\n')){let row='';for(const word of para.split(/\s+/)){const next=row?row+' '+word:word;if(c.measureText(next).width>width&&row){c.fillText(row,x,cy);cy+=line;row=word}else row=next}if(row)c.fillText(row,x,cy);cy+=line}return cy}
 function logo(img:HTMLImageElement,x:number,y:number,w:number,h:number){const scale=Math.min(w/img.naturalWidth,h/img.naturalHeight);const iw=img.naturalWidth*scale,ih=img.naturalHeight*scale;c.drawImage(img,x+(w-iw)/2,y+(h-ih)/2,iw,ih)}
 function panel(x:number,y:number,w:number,h:number,stroke='#3b6178'){c.fillStyle='#102634ee';c.strokeStyle=stroke;c.lineWidth=1;c.beginPath();c.roundRect(x,y,w,h,8);c.fill();c.stroke()}
 function draw(t:number){const f=frameAt(plan,t),chapter=chapters[f.index];const stage=document.querySelector<HTMLCanvasElement>('.robot-stage canvas');if(!exportFrameReady(f.index,stage?.dataset.cinemaChapter))return;c.fillStyle='#081118';c.fillRect(0,0,1920,1080)
  if(f.index===0||f.index===1){drawPlate(c,plates,f.index,f.progress,440,100,1480,855)}else if(f.index===2||f.index===3){const world=document.querySelector<HTMLCanvasElement>('.robot-stage canvas');if(world){if(f.index===2){const scale=Math.min(1090/world.width,560/world.height);const w=world.width*scale,h=world.height*scale;c.drawImage(world,800+(1090-w)/2,265+(560-h)/2,w,h)}else{const width=855*world.width/world.height;c.drawImage(world,1920-width,100,width,855)}}}else{c.save();c.translate(785,115);c.scale(.91,.91);drawProcess(c,f.index,f.progress);c.restore()}
  const g=c.createLinearGradient(0,0,1290,0);g.addColorStop(0,'#081118');g.addColorStop(.38,'#081118f8');g.addColorStop(.72,'#0811186b');g.addColorStop(1,'#08111800');c.fillStyle=g;c.fillRect(0,95,1360,865)
  c.fillStyle='#10191f';c.fillRect(0,0,1920,77);c.fillStyle='#324b5b';c.fillRect(0,77,1920,1)
  text('FROM CHANGE TO WORK',45,47,500,24,'#dfedf3','RedHatDisplay');text('CAPABILITY DELIVERY',45,65,500,9,'#7fa9bd','RedHatMono');text('AEROSPACE MANUFACTURING / EDGE STORY',435,47,700,12,'#8eaebf','RedHatMono')
  if(logos[0])logo(logos[0],1594,24,139,38);text('×',1749,49,30,22,'#678c9f');if(logos[1])logo(logos[1],1782,26,84,33)
  text('RETAINED STORY / SIMULATOR',46,104,600,11,'#d5b588','RedHatMono');text('Illustrative aerospace cell · physical motion disabled',1310,104,560,10,'#8da9b9','RedHatMono')
  text(`${String(f.index+1).padStart(2,'0')} / ${chapter.act}`,49,165,750,13,'#7eb9cc','RedHatMono')
  let y=text(chapter.title,46,241,785,64,'#e5f0f5','RedHatDisplay',70);y=text(chapter.line,49,y+18,670,24,'#9ebccc','RedHatText',35)+24
  drawChapterCallouts(f.index,f.progress,y,text,panel,flowStepAt(plan.flow_beats??[],t))
  const context=visualContext[f.index];panel(840,124,1020,122);text(context.title,862,154,970,24,'#e1f0f4','RedHatDisplay');text('INPUT',862,183,440,10,'#83d8ed','RedHatMono');text(context.input,862,211,450,17);text('OUTCOME',1345,183,450,10,'#8ee4b9','RedHatMono');text(context.output,1345,211,490,17)
  if(f.index===1){c.fillStyle='#08111899';c.fillRect(830,260,1090,570);packageLayers.forEach(([title,detail],i)=>{panel(1010+i*35,315+i*145,720,115,['#83d8ed','#8ee4b9','#e5bf86'][i]);text(title,1035+i*35,352+i*145,660,14,'#bde8f1','RedHatMono');text(detail,1035+i*35,393+i*145,660,29,'#e2edf1','RedHatDisplay')})}
  // The exported film intentionally has no burned-in captions.
  // Playback belongs to the video player; no decorative transport is baked into the picture.
  c.fillStyle='#101c25';c.fillRect(0,1037,1920,43)
  text('Aircraft: pilotcandle5470 / CC BY 4.0 · adapted',1410,1055,480,9,'#87a6b7','RedHatMono')
 }
 onFrame(0);await new Promise(r=>setTimeout(r,500));draw(0);recorder.start(1000);const began=performance.now();let raf=0
 await new Promise<void>(resolve=>{const tick=()=>{const t=Math.min(plan.duration,(performance.now()-began)/1000);onFrame(t);draw(t);if(t<plan.duration)raf=requestAnimationFrame(tick);else resolve()};raf=requestAnimationFrame(tick)})
 cancelAnimationFrame(raf);draw(plan.duration);recorder.stop();await stopped;stream.getTracks().forEach(t=>t.stop());const blob=new Blob(chunks,{type:mime});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='from-change-to-work-picture.webm';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000)
}
