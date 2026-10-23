"""Repair reviewed WebGL chapter entries without changing the audio stream or source film."""
import argparse,hashlib,json,subprocess,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg',required=True);args=ap.parse_args();out=ROOT/'verification/cinema-08';out.mkdir(exist_ok=True);source=ROOT/'presentation/public/film/from-change-to-work-music-cut.mp4';target=source.with_name('from-change-to-work-final.mp4');original=json.loads((ROOT/'verification/cinema-07/encoded-media.json').read_bytes());assert original['edition']=='cinema-07';assert hashlib.sha256(source.read_bytes()).hexdigest()==original['sha256'],'Repair requires the retained reviewed cinema-07 source'
 patches=[{'chapter':'architecture','start':85.76,'end':86.60,'source_frame':86.60},{'chapter':'disconnect','start':133.76,'end':137.80,'source_frame':137.80}]
 def run(a):
  p=subprocess.run([args.ffmpeg,'-hide_banner','-y',*map(str,a)],capture_output=True);assert p.returncode==0,p.stderr[-3000:];return p
 for p in patches:run(['-ss',p['source_frame'],'-i',source,'-frames:v','1',out/(p['chapter']+'-entry.png')])
 inputs=['-i',source]
 for p in patches:inputs+=['-loop','1','-framerate','25','-i',out/(p['chapter']+'-entry.png')]
 filters=f"[0:v][1:v]overlay=enable='gte(t,{patches[0]['start']})*lt(t,{patches[0]['end']})'[v1];[v1][2:v]overlay=enable='gte(t,{patches[1]['start']})*lt(t,{patches[1]['end']})'[v]"
 run([*inputs,'-filter_complex',filters,'-map','[v]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','copy','-t',original['duration_seconds'],'-movflags','+faststart',target])
 def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 audio=[]
 for p in [source,target]:audio.append(hashlib.sha256(run(['-i',p,'-map','0:a:0','-c:a','copy','-f','adts','pipe:1']).stdout).hexdigest())
 assert audio[0]==audio[1],'Audio stream changed'
 decode=run(['-xerror','-i',target,'-f','null','-']);(out/'final-decode.log').write_bytes(decode.stderr)
 duration_match=re.search(rb'Duration: (\d+):(\d+):(\d+\.\d+)',decode.stderr);assert duration_match;duration=int(duration_match[1])*3600+int(duration_match[2])*60+float(duration_match[3]);assert abs(duration-original['duration_seconds'])<.05
 report={**original,'duration_seconds':duration,'edition':'cinema-08','audio_edition':'cinema-07','film_name':target.name,'sha256':digest(target),'picture_repair':{'source_film':source.name,'source_sha256':digest(source),'patches':patches,'reason':'Brief stale WebGL scene/camera reset at chapter entries. Stable matching scene entry frames replace only those intervals.','audio_stream_sha256':audio[1],'audio_stream_byte_identical':True},'subjective_listening_performed':False}
 source.with_name('production.json').write_text(json.dumps(report,indent=2)+'\n');(out/'encoded-media.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
