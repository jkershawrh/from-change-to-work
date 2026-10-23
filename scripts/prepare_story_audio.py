"""Preserve the complete provider waveform, add reading holds, derive real captions."""
import argparse,hashlib,json,re,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'presentation';OUT=BASE/'public/audio'
def save_wave(path,values,rate):
 with wave.open(str(path),'wb') as f:f.setparams((1,2,rate,0,'NONE','not compressed'));f.writeframes(values.astype('<i2').tobytes())
def timestamp(value,comma=False):
 ms=round(value*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02}'+(',' if comma else '.')+f'{ms:03}'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg',default='ffmpeg');ap.add_argument('--edition',default='');args=ap.parse_args();assert not args.edition or args.edition=='cinema-02';global OUT;OUT=OUT/args.edition;meta=BASE/'audio'/args.edition;OUT.mkdir(parents=True,exist_ok=True)
 decoded=meta/'raw-decoded.wav'
 subprocess.run([args.ffmpeg,'-hide_banner','-loglevel','error','-y','-i',str(OUT/'kersh-raw.mp3'),'-ac','1','-ar','44100','-c:a','pcm_s16le',str(decoded)],check=True)
 with wave.open(str(decoded),'rb') as f:rate=f.getframerate();raw=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').copy()
 a=json.loads((meta/'alignment.json').read_bytes());rows=json.loads((meta/'script.json').read_bytes());text=''.join(a['characters']);flat=[];indices=[]
 for i,c in enumerate(text):
  if c.isalnum():flat.append(c.lower());indices.append(i)
 flat=''.join(flat);boundaries=[0.];cursor=0
 for row in rows[1:]:
  plain=re.sub(r'\[[^]]+\]','',row['text']).strip();needle=''.join(c.lower() for c in plain[:65] if c.isalnum());at=flat.find(needle,cursor);assert at>=0,'Chapter text not found in provider alignment: '+row['id'];cursor=at+len(needle);boundaries.append(a['character_start_times_seconds'][indices[at]])
 lead=2.;hold=6.;close=12.;cuts=[round(v*rate) for v in boundaries[1:]];parts=[np.zeros(round(lead*rate),dtype=np.int16)];last=0
 for cut in cuts:parts.extend([raw[last:cut],np.zeros(round(hold*rate),dtype=np.int16)]);last=cut
 parts.extend([raw[last:],np.zeros(round(close*rate),dtype=np.int16)]);voice=np.concatenate(parts)
 # Removing the inserted zero spans must recover every decoded provider sample.
 recovered=np.concatenate([p for p in parts[1:-1] if p.size and np.any(p)])
 assert np.array_equal(recovered,raw),'Entire source waveform must survive chapter holds.'
 save_wave(OUT/'narration.wav',voice,rate);duration=len(voice)/rate
 def shifted(t):return t+lead+sum(t>=b for b in boundaries[1:])*hold
 chapter_starts=[0.]+[shifted(t) for t in boundaries[1:]]
 chapters=[{'id':r['id'],'start':chapter_starts[i],'end':chapter_starts[i+1] if i+1<len(rows) else duration} for i,r in enumerate(rows)]
 # Original quiet tonal bed, fixed seed, never derived from copyrighted media.
 t=np.arange(len(voice))/rate;rng=np.random.default_rng(17);bed=np.zeros(len(voice))
 for hz,amp in [(55,.37),(82.4069,.23),(110,.17),(164.8138,.11)]:bed+=amp*np.sin(2*np.pi*hz*t+.3*np.sin(t*.08))
 voiced=np.abs(voice)>300;voice_rms=float(np.sqrt(np.mean(voice[voiced].astype(float)**2)));bed*=voice_rms*10**(-34/20)/max(np.sqrt(np.mean(bed**2)),1)
 envelope=np.minimum(1,t/3)*np.minimum(1,(duration-t)/5);bed*=envelope
 save_wave(OUT/'ambient.wav',bed,rate);mix=voice.astype(float)*.94+bed;clipped=int(np.sum(np.abs(mix)>32767));assert clipped==0,'Mix must retain headroom.';save_wave(OUT/'film-mix.wav',mix,rate)
 mask=np.ones(len(text),dtype=bool)
 for m in re.finditer(r'\[[^]]+\]',text):mask[m.start():m.end()]=False
 words=[]
 for m in re.finditer(r'\S+',text):
  s=''.join(c for j,c in enumerate(text[m.start():m.end()],m.start()) if mask[j]).strip()
  if s:words.append((s,shifted(a['character_start_times_seconds'][m.start()]),shifted(a['character_end_times_seconds'][m.end()-1])))
 captions=[];group=[]
 for word in words:
  if group and (len(' '.join(w[0] for w in group))+len(word[0])>77 or word[2]-group[0][1]>6):captions.append({'start':group[0][1],'end':group[-1][2],'text':' '.join(w[0] for w in group)});group=[]
  group.append(word)
  if word[0].endswith(('.','?','!')) and len(group)>=5:captions.append({'start':group[0][1],'end':group[-1][2],'text':' '.join(w[0] for w in group)});group=[]
 if group:captions.append({'start':group[0][1],'end':group[-1][2],'text':' '.join(w[0] for w in group)})
 plan={'schema':'aeris.story-audio-plan.v1','duration':duration,'voice_duration':len(raw)/rate,'lead_seconds':lead,'chapter_hold_seconds':hold,'closing_hold_seconds':close,'chapters':chapters,'captions':captions}
 (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(OUT/'captions.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(timestamp(c['start'])+' --> '+timestamp(c['end'])+'\n'+c['text'] for c in captions)+'\n')
 (OUT/'captions.srt').write_text('\n\n'.join(str(i+1)+'\n'+timestamp(c['start'],True)+' --> '+timestamp(c['end'],True)+'\n'+c['text'] for i,c in enumerate(captions))+'\n')
 report={'schema':'aeris.story-audio-production.v1','duration_seconds':duration,'original_voice_seconds':len(raw)/rate,'entire_decoded_source_waveform_retained':True,'provider_requests':1,'time_stretching':False,'chapter_holds':len(cuts),'closing_hold_seconds':close,'original_ambient_bed_db_below_active_voice_rms':34,'clipped_samples':clipped,'voiced_sample_fraction':float(np.mean(voiced)),'voice_settings_source':'audio/voice-profile.json','subjective_listening_performed':False,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (meta/'production-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='files'}))
if __name__=='__main__':main()
