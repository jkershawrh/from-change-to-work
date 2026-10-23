"""Signed-bundle HTTPS fixture; no approval or training authority."""
import argparse,http.server,json,ssl,hmac
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--private',type=Path,required=True);args=ap.parse_args();root=args.private
token=(root/'publisher-token').read_bytes().strip()
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.connection.settimeout(5)
  authorized=hmac.compare_digest(self.headers.get('Authorization','').encode(),b'Bearer '+token)
  if not authorized:self.send_response(403);self.end_headers();return
  selection=json.loads((root/'publication.json').read_text())
  data=(root/selection['bundle']).read_bytes()
  self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  print(json.dumps({'event':'BUNDLE_DELIVERED','bundle':selection['bundle'],'bytes':len(data),'peer':self.client_address[0],'tls':self.connection.version()}),flush=True)
context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2;context.load_cert_chain(root/'central-cert.pem',root/'central-key.pem')
server=http.server.ThreadingHTTPServer(('0.0.0.0',9443),Handler);server.socket=context.wrap_socket(server.socket,server_side=True)
print(json.dumps({'event':'PUBLISHER_READY'}),flush=True);server.serve_forever()
