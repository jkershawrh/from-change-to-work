"""Check the actual AAC export for music under speech and no caption overlay."""
import argparse,json,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def wave_data(p):
 with wave.open(str(p),'rb') as f:
  assert f.getframerate()==44100 and f.getnchannels()==1
  return np.frombuffer(f.readframes(f.getnframes()),dtype='<i2')[::10].astype(np.float32)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg',required=True);ap.add_argument('--work',type=Path,required=True);args=ap.parse_args();base=ROOT/'presentation/public/audio/cinema-07';m=json.loads((ROOT/'presentation/public/film/production.json').read_bytes());assert m['edition']=='cinema-07' and m['burned_in_captions'] is False
 # Decode is independently retained by the encoder. Inspect actual decoded output.
 with wave.open(str(args.work/'decoded-audio.wav'),'rb') as f:
  offset=round(m['opening_title_seconds']*44100);f.setpos(offset);decoded=np.frombuffer(f.readframes(f.getnframes()-offset),dtype='<i2')[::10].astype(np.float32)
 voice=wave_data(base/'narration.wav');music=wave_data(base/'ambient.wav');mix=wave_data(base/'film-mix.wav');n=min(len(decoded),len(mix));decoded=decoded[:n];voice=voice[:n];music=music[:n];mix=mix[:n]
 gain=json.loads((ROOT/'presentation/audio/cinema-07/music-production.json').read_bytes())['master_gain'];active=np.abs(voice)>300;residual=decoded-gain*.94*voice;music_correlation=float(np.corrcoef(residual[active],music[active])[0,1]);mix_correlation=float(np.corrcoef(decoded,mix)[0,1]);assert music_correlation>.80,music_correlation;assert mix_correlation>.98,mix_correlation
 assert m['export_transport_overlay'] is False
 plan=json.loads((base/'plan.json').read_bytes());ch=plan['chapters'][2];t=m['opening_title_seconds']+(ch['start']+ch['end'])/2;movie=ROOT/'presentation/public/film'/m['film_name'];r=subprocess.run([args.ffmpeg,'-hide_banner','-loglevel','error','-ss',str(t),'-i',str(movie),'-frames:v','1','-vf','crop=1480:70:220:850','-pix_fmt','rgb24','-f','rawvideo','pipe:1'],capture_output=True,check=True);pixels=np.frombuffer(r.stdout,dtype=np.uint8).reshape(-1,3);bright=float(np.mean(pixels.max(axis=1)>110));assert bright<.001,'Unexpected caption/text pixels in caption-free architecture region'
 r=subprocess.run([args.ffmpeg,'-hide_banner','-loglevel','error','-ss',str(t),'-i',str(movie),'-frames:v','1','-vf','crop=1920:66:0:964','-pix_fmt','rgb24','-f','rawvideo','pipe:1'],capture_output=True,check=True);footer=np.frombuffer(r.stdout,dtype=np.uint8).reshape(-1,3);footer_range=int(np.max(np.ptp(footer.astype(np.int16),axis=0)));assert footer_range<8,'Unexpected transport marks in exported footer'
 print(json.dumps({'status':'PASS_ENCODED_SCORE_AND_CAPTION_CHECK','music_correlation_under_voice':music_correlation,'decoded_mix_correlation':mix_correlation,'bright_pixel_fraction_in_former_caption_region':bright,'transport_region_channel_range':footer_range,'opening_seconds':m['opening_title_seconds'],'scope':'Objective AAC mix preservation and sampled caption absence; not subjective listening.'}))
if __name__=='__main__':main()
