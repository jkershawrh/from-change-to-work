"""Local editorial cut of the saved Kersh take. Never calls a voice provider."""
import argparse,hashlib,json,re,wave
from pathlib import Path
import numpy as np
from prepare_story_audio import save_wave,timestamp
ROOT=Path(__file__).resolve().parents[1]
def check_edits(segments):
 previous=-1.
 for start,end,dest in segments:
  if not(0<=start<end and dest>=0 and start>=previous):raise ValueError('Ordered nonoverlapping source spans required')
  previous=end

def retained_time(t,segments):
 for start,end,dest in segments:
  if start-1/44100<=t<=end+1/44100:return dest+min(end,max(start,t))-start
 raise ValueError('Timestamp belongs to removed audio')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'presentation/public/audio/cinema-06');ap.add_argument('--metadata',type=Path,default=ROOT/'presentation/audio/cinema-06');args=ap.parse_args()
 source=ROOT/'presentation/audio/cinema-02';out=args.out;meta=args.metadata;out.mkdir(parents=True,exist_ok=False);meta.mkdir(parents=True,exist_ok=False)
 a=json.loads((source/'alignment.json').read_bytes());rows=json.loads((source/'script.json').read_bytes());text=''.join(a['characters']);starts=a['character_start_times_seconds'];ends=a['character_end_times_seconds']
 rawpath=source/'raw-decoded.wav'
 if not rawpath.exists():raise RuntimeError('Decode the retained cinema-02 kersh-raw.mp3 to 44.1kHz mono PCM with the documented FFmpeg step first.')
 with wave.open(str(rawpath),'rb') as f:
  rate=f.getframerate();assert rate==44100 and f.getnchannels()==1 and f.getsampwidth()==2;raw=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').copy()
 removal='I am Kersh. I work at Red Hat; these are my personal views.';ri=text.index(removal);rj=ri+len(removal)
 segments=[];chapters=[];parts=[np.zeros(round(.6*rate),dtype=np.int16)];clock=.6;edited=[]
 for row in rows:
  at=text.index(row['text']);last=at+len(row['text'])-1;s=starts[at];e=min(len(raw)/rate,ends[last]+.04);ranges=[(s,e)]
  if at<=ri<=last:ranges=[(s,starts[ri]-.04),(starts[rj+1] if text[rj:rj+1]==' ' else starts[rj],e)]
  chapter_start=0 if not chapters else clock
  for index,(begin,end) in enumerate(ranges):
   begin=round(begin*rate)/rate;end=round(end*rate)/rate;segments.append((begin,end,clock));part=raw[round(begin*rate):round(end*rate)].copy()
   # 3ms edge fades prevent hard-cut clicks without changing speech speed.
   n=min(132,len(part)//2);part[:n]=(part[:n]*np.linspace(0,1,n)).astype(np.int16);part[-n:]=(part[-n:]*np.linspace(1,0,n)).astype(np.int16);parts.append(part);clock+=len(part)/rate
   if index<len(ranges)-1:parts.append(np.zeros(round(.18*rate),dtype=np.int16));clock+=.18
  chapters.append({'id':row['id'],'start':chapter_start,'end':clock});edited.append({'id':row['id'],'text':row['text'].replace(removal+' ','')})
  if row!=rows[-1]:parts.append(np.zeros(round(.55*rate),dtype=np.int16));clock+=.55
 for i in range(len(chapters)-1):chapters[i]['end']=chapters[i+1]['start']
 parts.append(np.zeros(round(2.2*rate),dtype=np.int16));clock+=2.2;chapters[-1]['end']=clock;voice=np.concatenate(parts);check_edits(segments);save_wave(out/'narration.wav',voice,rate)
 words=[]
 for m in re.finditer(r'\S+',text):
  if ri<=m.start()<rj:continue
  words.append((m.group(),retained_time(starts[m.start()],segments),retained_time(ends[m.end()-1],segments)))
 captions=[];group=[]
 def flush():
  if group:captions.append({'start':group[0][1],'end':group[-1][2],'text':' '.join(x[0] for x in group)});group.clear()
 for w in words:
  if group and (w[1]-group[-1][2]>.4 or len(' '.join(x[0] for x in group))+len(w[0])>77 or w[2]-group[0][1]>6):flush()
  group.append(w)
  if w[0].endswith(('.','?','!')) and len(group)>=5:flush()
 flush()
 cues=['An operator chooses','The central dispatcher','The delivery channel','At the receiving boundary','Only an idle executor','Once work starts','and can we account']
 beats=[{'event':i,'time':retained_time(starts[text.index(needle)],segments),'phrase':needle} for i,needle in enumerate(cues)]
 duration=len(voice)/rate;plan={'schema':'aeris.story-audio-plan.v1','duration':duration,'voice_duration':sum(e-s for s,e,_ in segments),'lead_seconds':.6,'chapter_hold_seconds':.55,'closing_hold_seconds':2.2,'chapters':chapters,'captions':captions,'flow_beats':beats}
 (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(out/'captions.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(timestamp(c['start'])+' --> '+timestamp(c['end'])+'\n'+c['text'] for c in captions)+'\n');(out/'captions.srt').write_text('\n\n'.join(str(i+1)+'\n'+timestamp(c['start'],True)+' --> '+timestamp(c['end'],True)+'\n'+c['text'] for i,c in enumerate(captions))+'\n')
 t=np.arange(len(voice))/rate;bed=sum(amp*np.sin(2*np.pi*hz*t+.3*np.sin(t*.08)) for hz,amp in [(55,.37),(82.4069,.23),(110,.17),(164.8138,.11)])
 voiced=np.abs(voice)>300;rms=np.sqrt(np.mean(voice[voiced].astype(float)**2));bed*=rms*10**(-34/20)/max(np.sqrt(np.mean(bed**2)),1);bed*=np.minimum(1,t/1.2)*np.minimum(1,(duration-t)/2);mix=voice.astype(float)*.94+bed;assert np.max(np.abs(mix))<32767;save_wave(out/'ambient.wav',bed,rate);save_wave(out/'film-mix.wav',mix,rate)
 (meta/'script.json').write_text(json.dumps(edited,indent=2)+'\n');report={'schema':'robot-demo.audio-editorial.v1','source':'cinema-02 retained Kersh take','source_decoded_sha256':hashlib.sha256(rawpath.read_bytes()).hexdigest(),'provider_requests':0,'voice_profile_changed':False,'time_stretching':False,'duration_seconds':duration,'chapter_gap_seconds':.55,'closing_hold_seconds':2.2,'removed_text':removal,'source_spans':[{'source_start':s,'source_end':e,'destination_start':d} for s,e,d in segments],'edge_fade_ms':3,'subjective_listening_performed':False,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}}
 (meta/'production-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'duration':duration,'flow_beats':beats,'provider_requests':0}))
if __name__=='__main__':main()
