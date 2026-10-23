"""Delete only the registered proof namespace, using its creation UID precondition.

Uses the explicit private kubeconfig in memory. Never exports its token or edits
cluster trust. Existing demos and namespaces are outside this cleanup scope.
"""
import argparse,base64,json,ssl,subprocess,time,urllib.error,urllib.request
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kubeconfig',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--oc',default='/Users/jkershaw/bin/oc');args=ap.parse_args()
 root=Path(__file__).resolve().parent;reg=json.loads((root/'registration.json').read_bytes())
 # oc create -o json emits concatenated objects for a List input.
 text=(root/'created-resources.json').read_text().strip();items=[];decoder=json.JSONDecoder()
 while text:
  item,end=decoder.raw_decode(text);items.extend(item['items'] if item.get('kind')=='List' else [item]);text=text[end:].lstrip()
 namespace=next(i for i in items if i['kind']=='Namespace');name=reg['namespace'];uid=namespace['metadata']['uid']
 if namespace['metadata']['name']!=name or namespace['metadata']['labels'].get('aeris-proof-id')!=name:raise ValueError('Creation ownership mismatch')
 p=subprocess.run([args.oc,'--kubeconfig='+str(args.kubeconfig),'config','view','--raw','--minify','-o','json'],capture_output=True,check=True)
 config=json.loads(p.stdout);cluster=config['clusters'][0]['cluster'];user=config['users'][0]['user']
 if cluster.get('insecure-skip-tls-verify'):raise ValueError('Verified cluster TLS required')
 ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
 if 'certificate-authority-data'in cluster:ctx.load_verify_locations(cadata=base64.b64decode(cluster['certificate-authority-data']).decode())
 else:
  ca_path=Path(cluster['certificate-authority'])
  if not ca_path.is_absolute():ca_path=args.kubeconfig.parent/ca_path
  ctx.load_verify_locations(cafile=str(ca_path))
 url=cluster['server'].rstrip('/')+'/api/v1/namespaces/'+name
 def request(method='GET',body=None):
  req=urllib.request.Request(url,method=method,data=json.dumps(body).encode() if body else None,headers={'Authorization':'Bearer '+user['token'],'Content-Type':'application/json'})
  with urllib.request.urlopen(req,context=ctx,timeout=10) as response:return json.load(response)
 current=request()
 if current['metadata']['uid']!=uid or current['metadata']['labels'].get('aeris-proof-id')!=name:raise ValueError('Current ownership mismatch')
 request('DELETE',{'apiVersion':'v1','kind':'DeleteOptions','preconditions':{'uid':uid},'propagationPolicy':'Background'})
 result={'schema':'aeris.owned-proof-cleanup.v1','namespace':name,'namespace_uid':uid,'uid_precondition':True,'status':'PENDING_NAMESPACE_DELETION'}
 deadline=time.monotonic()+120
 while time.monotonic()<deadline:
  try:request()
  except urllib.error.HTTPError as e:
   if e.code==404:result['status']='PASS_NAMESPACE_ABSENT';break
   raise
  time.sleep(2)
 with args.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result))
 if result['status']!='PASS_NAMESPACE_ABSENT':raise RuntimeError('Namespace deletion not observed')
if __name__=='__main__':main()
