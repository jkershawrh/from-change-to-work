"""Encode the real browser picture with its active saved-voice mix; verify media."""
import argparse,hashlib,json,re,shutil,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg',default='ffmpeg');ap.add_argument('--source',type=Path,default=ROOT/'.production/film/story-picture.webm');ap.add_argument('--edition',default='');ap.add_argument('--opening-title',type=Path);ap.add_argument('--opening-seconds',type=float,default=4.);args=ap.parse_args();assert not args.edition or args.edition in ['cinema-02','cinema-03','cinema-05','cinema-06','cinema-07'];edition=args.edition;audio_edition='cinema-02' if edition in ['cinema-03','cinema-05'] else edition;checks=ROOT/'verification'/(edition or 'cinema-01');checks.mkdir(parents=True,exist_ok=True)
 plan=json.loads((ROOT/'presentation/public/audio'/audio_edition/'plan.json').read_bytes());out=ROOT/'presentation/public/film';out.mkdir(parents=True,exist_ok=True);movie=out/('from-change-to-work-music-cut.mp4' if edition=='cinema-07' else 'from-change-to-work-story-cut.mp4' if edition=='cinema-06' else 'from-change-to-work-approved-aircraft.mp4' if edition=='cinema-05' else 'from-change-to-work-hangar.mp4' if edition=='cinema-03' else 'from-change-to-work.mp4' if edition else 'evy-aeris.mp4');work=args.source.resolve().parent;work.mkdir(parents=True,exist_ok=True)
 def run(values):
  r=subprocess.run([args.ffmpeg,'-hide_banner','-y',*map(str,values)],capture_output=True,text=True)
  if r.returncode:raise RuntimeError(r.stderr[-2500:])
  return r.stderr
 intro=args.opening_seconds if args.opening_title else 0.;assert not intro or (2<=intro<=6 and args.opening_title.is_file());expected_duration=plan['duration']+intro
 body_cleanup='drawbox=x=0:y=957:w=1920:h=80:color=0x081118:t=fill,' if edition=='cinema-07' else ''
 if intro:
  filters=f'[0:v]scale=1920:1080,setsar=1,format=yuv420p,fps=25,trim=duration={intro},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.2,fade=t=out:st={intro-.2}:d=0.2[v0];[1:v]{body_cleanup}fps=25,setsar=1,format=yuv420p,trim=duration={plan["duration"]},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.2[v1];[v0][v1]concat=n=2:v=1:a=0[v];[3:a]atrim=start=10:duration={intro},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.4,afade=t=out:st={intro-.3}:d=0.3[a0];[2:a]asetpts=PTS-STARTPTS[a1];[a0][a1]concat=n=2:v=0:a=1[a]'
  run(['-loop','1','-framerate','25','-i',args.opening_title,'-i',args.source,'-i',ROOT/'presentation/public/audio'/audio_edition/'film-mix.wav','-i',ROOT/'presentation/public/audio'/audio_edition/'ambient.wav','-filter_complex',filters,'-map','[v]','-map','[a]','-t',expected_duration,'-r','25','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',movie])
 else:
  run(['-i',args.source,'-i',ROOT/'presentation/public/audio'/audio_edition/'film-mix.wav','-map','0:v:0','-map','1:a:0','-vf',body_cleanup+'tpad=stop_mode=clone:stop_duration=1','-t',plan['duration'],'-r','25','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',movie])
 decoded=run(['-xerror','-i',movie,'-f','null','-']);m=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',decoded);assert m,'Missing encoded duration';duration=int(m[1])*3600+int(m[2])*60+float(m[3]);assert abs(duration-expected_duration)<.2,'Encoded timeline drift';assert '1920x1080' in decoded and '25 fps' in decoded and 'Audio: aac' in decoded,'Required video/audio streams absent'
 run(['-i',movie,'-vn','-ac','1','-ar','44100','-c:a','pcm_s16le',work/'decoded-audio.wav'])
 with wave.open(str(work/'decoded-audio.wav'),'rb') as f:rate=f.getframerate();samples=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)
 rms=float(np.sqrt(np.mean(samples**2)));assert rms>100,'Encoded audio is silent'
 frames=checks/'encoded-frames';frames.mkdir(parents=True,exist_ok=True)
 for i,c in enumerate(plan['chapters']):run(['-ss',intro+c['start']+(c['end']-c['start'])*.5,'-i',movie,'-frames:v','1',frames/(c['id']+'.png')])
 if intro:run(['-ss',intro/2,'-i',movie,'-frames:v','1',frames/'opening-title.png'])
 run(['-ss',duration-1,'-i',movie,'-frames:v','1',frames/'closing.png'])
 def digest(path):
  h=hashlib.sha256()
  with path.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  return h.hexdigest()
 browser=json.loads((work/'browser-recording.json').read_bytes());assert not browser['actuation_requests'] and not browser['errors']
 report={'schema':'aeris.encoded-story.v1','status':'PASS_ENCODED_MEDIA','film_name':movie.name,'edition':edition or 'cinema-01','audio_edition':audio_edition or 'cinema-01','duration_seconds':duration,'story_duration_seconds':plan['duration'],'opening_title_seconds':intro,'resolution':'1920x1080','fps':25,'audio':('AAC / saved Kersh narration and original speech-ducked musical score' if edition=='cinema-07' else 'AAC / editorial cut of saved Kersh take and original quiet bed' if edition=='cinema-06' else 'AAC / complete saved Kersh waveform and original quiet bed'),'decoded_audio_rms':rms,'entire_audio_timeline_retained':True,'original_provider_waveform_entirely_retained':edition not in ['cinema-06','cinema-07'],'frame_samples':9 if intro else 8,'full_video_audio_decode':True,'sha256':digest(movie),'voice_profile':'audio/voice-profile.json','browser_actuation_requests':0,'export_transport_overlay':False if edition=='cinema-07' else True,'body_footer_cleanup':('Recorded decorative transport masked at y957–1037; attribution retained' if edition=='cinema-07' else None),'burned_in_captions':False if edition=='cinema-07' else True,'music':('Original pad and piano score, speech-ducked' if edition=='cinema-07' else 'Original quiet bed'),'scope':'Narrated retained-evidence story. Not a new physical, hardware or live execution proof.','subjective_listening_performed':False}
 (out/'production.json').write_text(json.dumps(report,indent=2)+'\n');(checks/'encoded-media.json').write_text(json.dumps(report,indent=2)+'\n');(checks/'encoded-decode.log').write_text(decoded)
 dest=ROOT/'frontend/dist/show/film';dest.mkdir(parents=True,exist_ok=True)
 for name in [movie.name,'production.json']:shutil.copyfile(out/name,dest/name)
 print(json.dumps(report))
if __name__=='__main__':main()
