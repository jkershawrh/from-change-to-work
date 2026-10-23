"""Independent checks for the current musical mix and unchanged saved narration."""
import json,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def read(p):
 with wave.open(str(p),'rb') as f:
  assert f.getframerate()==44100 and f.getnchannels()==1
  return np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)
def main():
 base=ROOT/'presentation/public/audio/cinema-07';voice=read(base/'narration.wav');original=read(ROOT/'presentation/public/audio/cinema-06/narration.wav');assert np.array_equal(voice,original),'Voice take must remain unchanged';music=read(base/'ambient.wav');mix=read(base/'film-mix.wav');assert len(voice)==len(music)==len(mix)
 active=np.abs(voice)>300;rms=lambda x:float(np.sqrt(np.mean(x*x)));ratio=20*np.log10(rms(music[active])/rms(voice[active]));assert -22<=ratio<=-16,ratio;assert np.max(np.abs(mix))<32767
 segment=music[441000:882000];power=np.abs(np.fft.rfft(segment))**2;freq=np.fft.rfftfreq(len(segment),1/44100);mid=float(power[(freq>=180)&(freq<=2000)].sum()/power.sum());assert mid>.5,'Score must contain audible midrange, not only sub-bass'
 meta=json.loads((ROOT/'presentation/audio/cinema-07/music-production.json').read_bytes());assert meta['note_events']>300 and meta['provider_requests']==0;assert meta['caption_burn_in'] is False
 print(json.dumps({'status':'PASS_MUSIC_CONTRACT','music_db_below_active_voice':-ratio,'note_events':meta['note_events'],'midrange_energy_fraction':mid,'unchanged_narration':True,'clipped_samples':0,'scope':'Objective source mix; subjective listening is not asserted.'}))
if __name__=='__main__':main()
