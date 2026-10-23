"""Compose an original gentle pad/piano score, ducked beneath the saved voice."""
import argparse,hashlib,json,shutil,wave
from pathlib import Path
import numpy as np
from prepare_story_audio import save_wave
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'presentation/public/audio/cinema-07');ap.add_argument('--metadata',type=Path,default=ROOT/'presentation/audio/cinema-07');args=ap.parse_args()
 source=ROOT/'presentation/public/audio/cinema-06';out=args.out;meta=args.metadata;out.mkdir(parents=True,exist_ok=False);meta.mkdir(parents=True,exist_ok=False)
 for name in ['narration.wav','plan.json','captions.vtt','captions.srt']:shutil.copyfile(source/name,out/name)
 with wave.open(str(source/'narration.wav'),'rb') as f:rate=f.getframerate();voice=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').copy()
 n=len(voice);duration=n/rate;music=np.zeros(n,dtype=np.float32);beat=60/78;bar=beat*4;rng=np.random.default_rng(71);events=0
 chords=[[50,57,60,64,69],[46,53,57,62,65],[41,53,57,60,64,67],[48,55,60,62,67]]
 def hz(midi):return 440*2**((midi-69)/12)
 for measure,start in enumerate(np.arange(0,duration,bar)):
  chord=chords[measure%4];a=int(start*rate);b=min(n,a+int((bar+.25)*rate));t=np.arange(b-a,dtype=np.float32)/rate;env=np.minimum(1,t/.18)*np.minimum(1,(len(t)/rate-t)/.3)
  pad=np.zeros(len(t),dtype=np.float32)
  for midi in chord[1:]:
   f=hz(midi);pad+=(np.sin(2*np.pi*f*t)+.22*np.sin(2*np.pi*f*2*t)+.14*np.sin(2*np.pi*f*1.003*t))*.095
  music[a:b]+=pad*env
  for j,k in enumerate([1,3,2,4,1,2,3,4]):
   at=int((start+j*beat/2)*rate);end=min(n,at+int(1.6*rate))
   if at>=n:continue
   nt=np.arange(end-at,dtype=np.float32)/rate;f=hz(chord[min(k,len(chord)-1)]+(12 if j%3==1 else 0));tone=np.sin(2*np.pi*f*nt)+.28*np.sin(2*np.pi*2*f*nt)*np.exp(-nt*3)+.12*np.sin(2*np.pi*3*f*nt)*np.exp(-nt*5)
   envelope=np.minimum(1,nt/.012)*np.exp(-nt*3.3)*np.minimum(1,(len(nt)/rate-nt)/.04);music[at:end]+=tone*envelope*.18;events+=1
 # Speech activity is smoothed at 100Hz; music returns gently between phrases.
 block=441;count=(n+block-1)//block;padded=np.pad(voice.astype(np.float32),(0,count*block-n));energy=np.sqrt(np.mean(padded.reshape(count,block)**2,axis=1));target=np.where(energy>220,.60,1.).astype(np.float32);gain=np.empty(count,dtype=np.float32);state=1.
 for i,v in enumerate(target):state+=(float(v)-state)*(0.22 if v<state else .025);gain[i]=state
 duck=np.interp(np.arange(n),np.arange(count)*block,gain).astype(np.float32);music*=duck
 active=np.abs(voice)>300;voice_rms=float(np.sqrt(np.mean(voice[active].astype(np.float32)**2)));music_rms=float(np.sqrt(np.mean(music[active]**2)));music*=voice_rms*10**(-19/20)/music_rms
 fade=int(rate*1.2);music[:fade]*=np.linspace(0,1,fade,dtype=np.float32);fade=int(rate*2);music[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)
 mix=voice.astype(np.float32)*.94+music;master=min(1.,32767*.96/float(np.max(np.abs(mix))));mix*=master;save_wave(out/'ambient.wav',music,rate);save_wave(out/'film-mix.wav',mix,rate)
 report={'schema':'robot-demo.original-score.v1','composition':'Original D minor / B-flat / F / C pad and soft piano arpeggio','bpm':78,'note_events':events,'music_db_below_active_voice_target':19,'duck_attack_release':'speech envelope, fast reduction and gradual recovery','master_gain':master,'duration_seconds':duration,'source_narration':'cinema-06 unchanged','voice_profile_changed':False,'provider_requests':0,'caption_burn_in':False,'subjective_listening_performed':False,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}}
 (meta/'music-production.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='files'}))
if __name__=='__main__':main()
