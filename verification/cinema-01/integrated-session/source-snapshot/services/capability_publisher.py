"""Preapproved recipe publisher. Lab selection cannot create or approve releases."""
import argparse,hashlib,hmac,http.server,json,ssl,threading
from pathlib import Path
from services.action_console.contracts import decode,need

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);cfg=json.loads(ap.parse_args().config.read_bytes());token=Path(cfg['token_file']).read_bytes().strip();operator=Path(cfg['selection_token_file']).read_bytes().strip();lock=threading.Lock();selected=cfg['initial_digest'];bank={}
 for digest,path in cfg['bundles'].items():
  data=Path(path).read_bytes();value=json.loads(data);need(hashlib.sha256(value['manifest_json'].encode()).hexdigest()==digest,'BUNDLE_IDENTITY');bank[digest]=data
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def auth(self,secret):return hmac.compare_digest(self.headers.get('Authorization','').encode(),b'Bearer '+secret)
  def reply(self,status,data):
   self.send_response(status);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  def do_GET(self):
   if not self.auth(token):self.reply(403,b'{}');return
   with lock:data=bank[selected];digest=selected
   self.reply(200,data);print(json.dumps({'event':'DELIVERED','release_digest':digest,'tls':self.connection.version(),'bytes':len(data)}),flush=True)
  def do_POST(self):
   nonlocal selected
   if not self.auth(operator):self.reply(403,b'{}');return
   try:
    need(self.path=='/select','NOT_FOUND');n=int(self.headers.get('Content-Length','-1'));need(0<n<=1024 and not self.headers.get('Transfer-Encoding'),'BODY_LIMIT');v=decode(self.rfile.read(n));need(set(v)=={'release_digest'} and v['release_digest']in bank,'UNAPPROVED_RELEASE')
    with lock:selected=v['release_digest']
    self.reply(200,json.dumps({'schema':'aeris.publication.v1','release_digest':selected}).encode())
   except (ValueError,KeyError):self.reply(409,b'{"error":"UNAPPROVED_RELEASE"}')
 ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(cfg['certificate'],cfg['private_key']);server=http.server.ThreadingHTTPServer((cfg.get('bind','127.0.0.1'),cfg['port']),Handler);server.socket=ctx.wrap_socket(server.socket,server_side=True);print('PUBLISHER_READY',flush=True);server.serve_forever()
if __name__=='__main__':main()
