"""Generate the requested saved voice once. Never prints or stores an API key.

Use ELEVENLABS_API_KEY or the owner's existing macOS Keychain entry. An uncertain
request is not automatically retried. Existing raw audio is never regenerated.
"""
import argparse,base64,datetime,hashlib,json,os,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'presentation';PUBLIC=BASE/'public/audio'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--generate',action='store_true');ap.add_argument('--edition',default='');args=ap.parse_args();assert not args.edition or args.edition in ['cinema-02','cinema-09'];meta=BASE/'audio'/args.edition;public=PUBLIC/args.edition
 profile=json.loads((BASE/'audio/voice-profile.json').read_bytes());rows=json.loads((meta/'script.json').read_bytes());speech='\n\n'.join(r['text'] for r in rows)
 assert len(speech)<=5000,'Keep the selected model within its verified request bound.'
 public.mkdir(parents=True,exist_ok=True);audio=public/'kersh-raw.mp3';alignment=meta/'alignment.json';intent=meta/'generation-intent.json'
 if audio.exists():
  assert alignment.exists(),'Existing audio retained; recover alignment instead of regenerating.'
  print('Retained existing narration.');return
 if not args.generate:print('Ready to generate the saved voice with the exact pinned profile. Pass --generate.');return
 assert not intent.exists(),'Previous request may have reached the provider; inspect it before another generation.'
 key=os.environ.get('ELEVENLABS_API_KEY')
 if not key and sys.platform=='darwin':
  r=subprocess.run(['security','find-generic-password','-s','arf-model-gateways','-a','elevenlabs','-w'],capture_output=True,text=True)
  if r.returncode==0:key=r.stdout.strip()
 if not key:raise RuntimeError('ELEVENLABS_API_KEY or the existing owner Keychain entry is required.')
 record={'schema':'aeris.voice-generation.v1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'voice_id':profile['voice_id'],'model_id':profile['model_id'],'voice_settings':profile['voice_settings'],'characters':len(speech),'script_sha256':hashlib.sha256(speech.encode()).hexdigest(),'status':'REQUEST_INTENT_RECORDED','automatic_retries':False}
 intent.write_text(json.dumps(record,indent=2)+'\n')
 payload={'text':speech,'model_id':profile['model_id'],'voice_settings':profile['voice_settings']}
 req=urllib.request.Request('https://api.elevenlabs.io/v1/text-to-speech/'+profile['voice_id']+'/with-timestamps?output_format=mp3_44100_128',headers={'xi-api-key':key,'Content-Type':'application/json'},data=json.dumps(payload).encode())
 try:
  with urllib.request.urlopen(req,timeout=300) as response:data=json.load(response)
 except Exception:
  print('Generation outcome uncertain; intent retained. No automatic retry or credential output.',file=sys.stderr);raise RuntimeError('Narration request did not return verified media.') from None
 raw=base64.b64decode(data['audio_base64']);audio.write_bytes(raw)
 a=data.get('alignment') or data.get('normalized_alignment');assert a,'Audio retained; alignment missing. Do not regenerate.'
 alignment.write_text(json.dumps(a)+'\n');record.update(status='RAW_AUDIO_AND_ALIGNMENT_RETAINED',requests=1,audio_sha256=hashlib.sha256(raw).hexdigest(),voice_end_seconds=a['character_end_times_seconds'][-1]);intent.write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps({'status':record['status'],'characters':len(speech),'voice_end_seconds':record['voice_end_seconds'],'requests':1}))
if __name__=='__main__':main()
