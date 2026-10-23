"""Review every encoded frame, chapter timing and five-second audio window. Requires FFmpeg and NumPy."""
import subprocess,json,hashlib,wave,math,argparse,re
from pathlib import Path
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg',type=Path,required=True);ap.add_argument('--movie',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--opening-seconds',type=float,default=4.);args=ap.parse_args();intro=args.opening_seconds;R=Path(__file__).resolve().parents[1];O=args.out.resolve();O.mkdir(parents=True,exist_ok=False);F=args.ffmpeg.resolve();M=args.movie.resolve();P=json.loads((R/'presentation/public/audio/cinema-07/plan.json').read_bytes());report={'movie_sha256':hashlib.sha256(M.read_bytes()).hexdigest(),'scope':'Encoded final MP4; full-frame integrity and objective audio/timing review. No subjective listening claimed.'}
def run(a):
 p=subprocess.run([str(F),'-hide_banner','-y',*map(str,a)],capture_output=True);assert p.returncode==0,p.stderr[-2000:];return p
for start in range(0,math.ceil(P['duration']+intro),40):
 end=min(P['duration']+intro,start+40);label="%{pts\\:hms\\:"+str(start)+"}"
 run(['-ss',start,'-i',M,'-t',end-start,'-vf',f"fps=1,scale=384:216,drawtext=fontfile=/System/Library/Fonts/Menlo.ttc:text='{label}':x=8:y=192:fontsize=17:fontcolor=white:box=1:boxcolor=black,tile=5x8",'-frames:v','1',O/f'timeline-{start:03d}.png'])
 print('timeline',start,flush=True)
for ch in P['chapters'][1:]:
 start=intro+ch['start']-1.5;label="%{pts\\:hms\\:"+str(start)+"}"
 run(['-ss',start,'-i',M,'-t',3,'-vf',f"fps=8,scale=384:216,drawtext=fontfile=/System/Library/Fonts/Menlo.ttc:text='{label}':x=8:y=192:fontsize=17:fontcolor=white:box=1:boxcolor=black,tile=6x4",'-frames:v','1',O/f'transition-{ch["id"]}.png'])
 print('transition',ch['id'],flush=True)
p=subprocess.Popen([str(F),'-hide_banner','-loglevel','error','-xerror','-i',str(M),'-an','-vf','scale=160:90','-pix_fmt','gray','-f','rawvideo','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE);frames=0;dark=[];jumps=[];prev=None;footer=[];voice_footer=[]
while True:
 raw=p.stdout.read(160*90)
 if not raw:break
 assert len(raw)==160*90
 a=np.frombuffer(raw,np.uint8).reshape(90,160).astype(np.int16);t=frames/25
 if a.mean()<5 and a.std()<4:dark.append(round(t,2))
 if prev is not None:
  d=float(np.mean(np.abs(a-prev)))
  if d>12:jumps.append({'time':round(t,2),'mean_pixel_change':round(d,2)})
 if t>intro+.4 and np.ptp(a[81:85,5:155])>8:footer.append(round(t,2))
 if intro>=5 and t>intro+.4 and np.ptp(a[87:89,:114])>8:voice_footer.append(round(t,2))
 prev=a;frames+=1
assert p.wait()==0,p.stderr.read();assert frames>=8250,frames
report.update(frame_count=frames,full_frame_decode=True,near_black_times=dark,large_frame_changes=jumps,transport_region_anomalies=footer)
assert not [t for t in dark if t>intro+.4],dark;assert not footer,footer;assert not voice_footer,voice_footer
# Independently decode the current movie, retaining floating-point audio to detect clipping.
# Float PCM is inspected directly; no duplicate audio asset is added to the handoff.
raw=run(['-i',M,'-vn','-ac','1','-ar','44100','-f','f32le','pipe:1']).stdout;x=np.frombuffer(raw,'<f4');rate=44100
with wave.open(str(R/'presentation/public/audio/cinema-07/film-mix.wav'),'rb') as f:mix=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float32)/32768
with wave.open(str(R/'presentation/public/audio/cinema-07/narration.wav'),'rb') as f:voice=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float32)/32768
with wave.open(str(R/'presentation/public/audio/cinema-07/ambient.wav'),'rb') as f:music=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float32)/32768
offset=round(intro*rate);body=x[offset:offset+len(mix)];assert len(body)==len(mix)
windows=[]
for start in range(0,len(mix),rate*5):
 a=body[start:start+rate*5:10];b=mix[start:start+rate*5:10];corr=float(np.corrcoef(a,b)[0,1]);assert corr>.98,(start/rate,corr);windows.append({'movie_start':intro+start/rate,'mix_correlation':round(corr,6)})
assert np.max(np.abs(x))<1,'AAC sample clipping'
if intro>=5:
 with wave.open(str(R/'presentation/public/audio/cinema-09/opening-mix.wav'),'rb') as f:opening=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float32)/32768
 corr=float(np.corrcoef(x[:len(opening):10],opening[::10])[0,1]);assert corr>.99,corr;report['opening_mix_correlation']=corr
scripts=json.loads((R/'presentation/audio/cinema-06/script.json').read_bytes());chapters=[]
for ch in P['chapters']:
 a=int(ch['start']*rate);b=min(len(mix),int(ch['end']*rate));active=np.abs(voice[a:b])>.01;v=voice[a:b][active];m=music[a:b][active];db=float(20*np.log10(np.sqrt(np.mean(m*m))/np.sqrt(np.mean(v*v))));assert -24<db<-14,(ch['id'],db)
 captions=[c for c in P['captions'] if c['start']>=ch['start']-.001 and c['start']<ch['end']-.001];assert captions and captions[-1]['end']<=ch['end']+.001
 script=next(s for s in scripts if s['id']==ch['id']);assert re.findall('[a-z0-9]+',' '.join(c['text'] for c in captions).lower())==re.findall('[a-z0-9]+',script['text'].lower())
 chapters.append({'id':ch['id'],'movie_start':intro+ch['start'],'movie_end':intro+ch['end'],'music_below_voice_db':round(-db,2),'last_spoken_end':intro+captions[-1]['end'],'hold_after_speech':round(ch['end']-captions[-1]['end'],3)})
report.update(voice_footer_region_anomalies=voice_footer,audio_peak_dbfs=round(float(20*np.log10(np.max(np.abs(x)))),3),audio_windows=windows,chapters=chapters,subjective_listening_performed=False,status='PASS_FULL_TIMELINE_OBJECTIVE_CHECKS')
(O/'full-timeline-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['audio_windows','chapters']}),flush=True)
