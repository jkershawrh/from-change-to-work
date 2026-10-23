"""Add the approved title announcement and remove the voice footer; preserve reviewed body scenes."""
import argparse,hashlib,json,re,subprocess,wave
from pathlib import Path
import numpy as np
from prepare_story_audio import save_wave
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg',required=True);args=ap.parse_args();out=ROOT/'verification/cinema-09';public=ROOT/'presentation/public/audio/cinema-09';meta=ROOT/'presentation/audio/cinema-09';source=ROOT/'presentation/public/film/from-change-to-work-final.mp4';target=source.with_name('from-change-to-work-announced.mp4');prior=json.loads((ROOT/'verification/cinema-08/encoded-media.json').read_bytes());assert hashlib.sha256(source.read_bytes()).hexdigest()==prior['sha256'];intro=5.;rate=44100
 def run(a):
  p=subprocess.run([args.ffmpeg,'-hide_banner','-y',*map(str,a)],capture_output=True);assert p.returncode==0,p.stderr[-3000:];return p
 def read(p):
  with wave.open(str(p),'rb') as f:assert f.getframerate()==rate and f.getnchannels()==1;return np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float32)
 raw=run(['-i',public/'kersh-raw.mp3','-ac','1','-ar',rate,'-f','s16le','pipe:1']).stdout;voice=np.frombuffer(raw,'<i2').astype(np.float32);alignment=json.loads((meta/'alignment.json').read_bytes());spoken_end=alignment['character_end_times_seconds'][-1];voice=voice[:round((spoken_end+.06)*rate)];lead=round(.2*rate);assert lead+len(voice)<intro*rate,'Do not truncate spoken opener';n=round(intro*rate);v=np.zeros(n,np.float32);v[lead:lead+len(voice)]=voice
 base=ROOT/'presentation/public/audio/cinema-07';main=read(base/'narration.wav');active=np.abs(v)>300;gain=float(np.sqrt(np.mean(main[np.abs(main)>300]**2))/np.sqrt(np.mean(v[active]**2)));v*=gain
 bed=read(base/'ambient.wav')[10*rate:10*rate+n].copy();bed*=float(np.sqrt(np.mean(v[active]**2))*10**(-19/20)/np.sqrt(np.mean(bed[active]**2)));fade=round(.2*rate);bed[:fade]*=np.linspace(0,1,fade);bed[-fade:]*=np.linspace(1,0,fade);mix=.94*v+bed;master=min(1.,32767*.96/float(np.max(np.abs(mix))));v*=master;bed*=master;mix*=master;save_wave(public/'opening-narration.wav',v,rate);save_wave(public/'opening-mix.wav',mix,rate)
 filters=f'[0:v]scale=1920:1080,setsar=1,format=yuv420p,fps=25,trim=duration={intro},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.15[v0];[1:v]trim=start=4,setpts=PTS-STARTPTS,drawbox=x=0:y=1037:w=1390:h=43:color=0x101c25:t=fill[v1];[v0][v1]concat=n=2:v=1:a=0[v];[2:a][3:a]concat=n=2:v=0:a=1[a]'
 expected=prior['duration_seconds']-4+intro
 run(['-loop','1','-framerate','25','-i',ROOT/'presentation/public/film/opening-title.png','-i',source,'-i',public/'opening-mix.wav','-i',base/'film-mix.wav','-filter_complex',filters,'-map','[v]','-map','[a]','-t',expected,'-r','25','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',target])
 decode=run(['-xerror','-i',target,'-f','null','-']);(out/'encoded-decode.log').write_bytes(decode.stderr);m=re.search(rb'Duration: (\d+):(\d+):(\d+\.\d+)',decode.stderr);assert m;duration=int(m[1])*3600+int(m[2])*60+float(m[3]);assert abs(duration-expected)<.05
 report={**prior,'edition':'cinema-09','film_name':target.name,'duration_seconds':duration,'opening_title_seconds':intro,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'voice_footer_overlay':False,'opening_announcement':{'text':''.join(alignment['characters']),'voice_profile':'presentation/audio/voice-profile.json','voice_settings_changed':False,'spoken_start_seconds':.2+alignment['character_start_times_seconds'][0],'spoken_end_seconds':.2+spoken_end,'provider_requests':1,'mix_voice_gain':gain,'master_gain':master},'reviewed_body_source':{'movie':source.name,'sha256':prior['sha256'],'original_intro_removed_seconds':4,'body_visuals_shift_seconds':1,'body_audio_source':'cinema-07 lossless film-mix.wav'},'final_review_evidence':'verification/cinema-09/','subjective_listening_performed':False}
 # The earlier repair record describes source history, not the new edit clock.
 report.pop('decoded_audio_rms',None);report['audio']='AAC / Kersh title announcement and narration with original speech-ducked score'
 report['picture_repair']={**prior['picture_repair'],'scope':'Historical repair in the retained cinema-08 body; add 1 second to prior movie times.'}
 (meta/'opening-production.json').write_text(json.dumps(report['opening_announcement'],indent=2)+'\n');(out/'encoded-media.json').write_text(json.dumps(report,indent=2)+'\n');target.with_name('production.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
