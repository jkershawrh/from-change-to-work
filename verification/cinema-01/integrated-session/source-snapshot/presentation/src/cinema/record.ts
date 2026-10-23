import {chapters,architectureLayers} from './chapters'
import {frameAt,seconds,type Plan} from './model'
/** Capture the real WebGL cell with export typography; never calls an action API. */
export async function recordStory(plan:Plan,onFrame:(t:number)=>void){
 await document.fonts.ready
 await Promise.all([document.fonts.load('700 64px RedHatDisplay'),document.fonts.load('24px RedHatText'),document.fonts.load('15px RedHatMono')])
 const logos=[...document.querySelectorAll<HTMLImageElement>('.cine-header .brand-lockup img')];await Promise.all(logos.map(i=>i.decode()))
 const canvas=document.createElement('canvas');canvas.width=1920;canvas.height=1080;const c=canvas.getContext('2d')!
 const stream=canvas.captureStream(25);const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8'].find(t=>MediaRecorder.isTypeSupported(t));if(!mime)throw Error('Film recording requires browser MediaRecorder.')
 const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:10000000});const chunks:Blob[]=[];recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)}
 const stopped=new Promise<void>((resolve,reject)=>{recorder.onstop=()=>resolve();recorder.onerror=()=>reject(Error('Film recording failed.'))})
 function text(value:string,x:number,y:number,width:number,size=25,color='#b9d2df',font='RedHatText',line=size*1.4){c.fillStyle=color;c.font=`${font==='RedHatDisplay'?'700 ':''}${size}px ${font}`;let cy=y;for(const para of value.split('\n')){let row='';for(const word of para.split(/\s+/)){const next=row?row+' '+word:word;if(c.measureText(next).width>width&&row){c.fillText(row,x,cy);cy+=line;row=word}else row=next}if(row)c.fillText(row,x,cy);cy+=line}return cy}
 function panel(x:number,y:number,w:number,h:number,stroke='#3b6178'){c.fillStyle='#102634ee';c.strokeStyle=stroke;c.lineWidth=1;c.beginPath();c.roundRect(x,y,w,h,8);c.fill();c.stroke()}
 function draw(t:number){const f=frameAt(plan,t),chapter=chapters[f.index];c.fillStyle='#081118';c.fillRect(0,0,1920,1080)
  const world=document.querySelector<HTMLCanvasElement>('.cine-world canvas');if(world)c.drawImage(world,430,100,1490,855)
  const g=c.createLinearGradient(0,0,1290,0);g.addColorStop(0,'#081118');g.addColorStop(.38,'#081118f8');g.addColorStop(.72,'#0811186b');g.addColorStop(1,'#08111800');c.fillStyle=g;c.fillRect(0,95,1360,865)
  c.fillStyle='#10191f';c.fillRect(0,0,1920,77);c.fillStyle='#324b5b';c.fillRect(0,77,1920,1)
  text('EVY × AERIS',45,47,500,27,'#dfedf3','RedHatDisplay');text('CAPABILITY DELIVERY',45,65,500,9,'#7fa9bd','RedHatMono');text('AEROSPACE MANUFACTURING / EDGE STORY',360,47,700,12,'#8eaebf','RedHatMono')
  if(logos[0])c.drawImage(logos[0],1594,24,139,38);text('×',1749,49,30,22,'#678c9f');if(logos[1])c.drawImage(logos[1],1782,26,84,33)
  text('RETAINED STORY / SIMULATOR',46,104,600,11,'#d5b588','RedHatMono');text('Illustrative aerospace cell · physical motion disabled',1310,104,560,10,'#8da9b9','RedHatMono')
  text(`${String(f.index+1).padStart(2,'0')} / ${chapter.act}`,49,165,750,13,'#7eb9cc','RedHatMono')
  let y=text(chapter.title,46,241,785,64,'#e5f0f5','RedHatDisplay',70);y=text(chapter.line,49,y+18,670,24,'#9ebccc','RedHatText',35)+24
  if(f.index===0){panel(50,y,490,115);text('THE QUESTION',70,y+29,430,12,'#7eb4c8','RedHatMono');text(chapter.question,70,y+67,445,24,'#cfe7ef')}
  if(f.index===1){panel(49,y,510,215);text('APPROVED CAPABILITY',72,y+33,450,13,'#8dd2df','RedHatMono');['Bounded joint goals','Exact signed bytes','Locally approved profile','No driver or trained weights installed'].forEach((s,i)=>text(s,72,y+74+i*34,450,21,i===3?'#91aebe':'#cae1eb'))}
  if(f.index===2){const i=Math.min(3,Math.floor(f.progress*4)),a=architectureLayers[i],answer=(f.progress*8)%2>=1;panel(49,y,670,218);text('ASK → REVEAL → FOLLOW',72,y+31,610,12,'#80b7cd','RedHatMono');text(a.question,72,y+72,610,28,'#deedf3','RedHatDisplay');if(answer){text(a.answer,72,y+115,600,21,'#b6d2df');text(a.component,72,y+160,600,13,'#83d2e4','RedHatMono');text(a.detail,72,y+188,610,15,'#8daebf')}else text('Pause. Let the room reason about the boundary.',72,y+137,610,19,'#8ca9ba')}
  if(f.index===3){panel(49,y,610,186,'#8b6445');text('CENTRAL DATA PLANE / CUT',72,y+34,550,13,'#e1b27f','RedHatMono');text('Local execution owns the task.',72,y+79,550,28,'#b5decf','RedHatDisplay');text('Separate observer available.\nRetained simulator playback, not a safety stop.',72,y+117,550,19,'#a2bdcd')}
  if(f.index===4){['INTERRUPTED EXECUTOR','RECOVERY REQUIRED','EXPLICIT RECOVERY','DELIBERATELY NEW ACTION'].forEach((s,i)=>{panel(49,y+i*54,570,43);text(String(i+1).padStart(2,'0')+' / '+s,69,y+29+i*54,530,13,'#c4dce7','RedHatMono')})}
  if(f.index===5){['Inspection / existing simulator task','Rework / same delivery and recovery','Next task / reviewed adapter still required'].forEach((s,i)=>{panel(49,y+i*68,620,54,i===2?'#7e6a4a':'#3b6178');text(s,70,y+35+i*68,580,20,'#c5e1ec')})}
  if(f.index===6){panel(49,y,650,224);text('THE NEXT HARDWARE PROOF',72,y+35,590,12,'#d1b280','RedHatMono');text('Named hosts. Bounded task. Acceptance owner.',72,y+80,590,23,'#cfe7ee','RedHatDisplay');text('Dashboard + agent start packet\nTransfer · cut · recovery · independent audit',72,y+125,590,21,'#9fc4d5');text('Physical motion and real time remain separate gates.',72,y+196,590,15,'#c2ab87')}
  const caption=plan.captions.find(x=>t>=x.start&&t<x.end);if(caption){const w=Math.min(1540,c.measureText(caption.text).width+100);panel(190,843,1540,80,'#2e4d61');text(caption.text,220,877,1480,25,'#e7f1f5','RedHatText',32)}
  c.fillStyle='#101c25';c.fillRect(0,957,1920,123);c.fillStyle='#304f61';c.fillRect(0,957,1920,1);c.fillStyle='#254557';c.fillRect(49,977,1818,3);c.fillStyle='#84cadd';c.fillRect(49,977,1818*t/plan.duration,3)
  text(seconds(t)+' / '+seconds(plan.duration),49,1011,250,14,'#a6c8d9','RedHatMono');chapters.forEach((x,i)=>text(String(i+1).padStart(2,'0')+'  '+x.label,280+i*225,1011,220,14,i===f.index?'#d5edf5':'#6b90a5'))
  text('Saved synthetic Kersh voice · narration does not control the robot',49,1055,1300,11,'#749aad','RedHatMono');text('Red Hat × Intel / profile-specific acceptance',1430,1055,450,10,'#87a6b7','RedHatMono')
 }
 onFrame(0);await new Promise(r=>setTimeout(r,500));draw(0);recorder.start(1000);const began=performance.now();let raf=0
 await new Promise<void>(resolve=>{const tick=()=>{const t=Math.min(plan.duration,(performance.now()-began)/1000);onFrame(t);draw(t);if(t<plan.duration)raf=requestAnimationFrame(tick);else resolve()};raf=requestAnimationFrame(tick)})
 cancelAnimationFrame(raf);draw(plan.duration);recorder.stop();await stopped;stream.getTracks().forEach(t=>t.stop());const blob=new Blob(chunks,{type:mime});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='evy-aeris-story-picture.webm';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000)
}
