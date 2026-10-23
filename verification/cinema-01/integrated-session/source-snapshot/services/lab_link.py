"""A real, bounded TCP data-plane cut. The separate observer path stays available."""
import argparse,hmac,http.server,json,select,socket,socketserver,ssl,threading,time
from pathlib import Path
from services.action_console.contracts import decode,need
class Gate:
 def __init__(self):self.connected=True;self.lock=threading.Lock();self.sockets=set();self.commands={}
 def change(self,command_id,operation):
  need(operation in ['disconnect','reconnect'],'CONTROL_NOT_ALLOWED')
  with self.lock:
   if command_id in self.commands:
    old=self.commands[command_id];need(old['operation']==operation,'COMMAND_ID_REUSED');return old
   self.connected=operation=='reconnect'
   if not self.connected:
    for s in list(self.sockets):
     try:s.shutdown(socket.SHUT_RDWR)
     except OSError:pass
     s.close()
   result=dict(schema='aeris.link-control.v1',command_id=command_id,operation=operation,connected=self.connected,observed_at_ms=time.time_ns()//1000000,scope='SIMULATOR_DATA_PLANE_ONLY',observer_channel='AVAILABLE')
   self.commands[command_id]=result
   if len(self.commands)>256:self.commands.pop(next(iter(self.commands)))
   return result
 def proxy(self,host,port):
  gate=self
  class Handler(socketserver.BaseRequestHandler):
   def handle(self):
    upstream=None
    try:
     with gate.lock:
      if not gate.connected:return
     upstream=socket.create_connection((host,port),timeout=3);peers=[self.request,upstream]
     with gate.lock:
      if not gate.connected:return
      gate.sockets.update(peers)
     for s in peers:s.setblocking(False)
     while gate.connected:
      ready,_,_=select.select(peers,[],[],1)
      for src in ready:
       data=src.recv(65536)
       if not data:return
       dst=upstream if src is self.request else self.request
       dst.settimeout(3);dst.sendall(data);dst.setblocking(False)
    except (OSError,ValueError):pass
    finally:
     with gate.lock:
      gate.sockets.discard(self.request)
      if upstream:gate.sockets.discard(upstream)
     if upstream:upstream.close()
  return Handler

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);cfg=json.loads(ap.parse_args().config.read_bytes());gate=Gate();token=Path(cfg['token_file']).read_bytes().strip();need(len(token)>=32,'TOKEN_CONFIG')
 for link in cfg['links']:
  class Server(socketserver.ThreadingTCPServer):allow_reuse_address=True;daemon_threads=True
  server=Server((cfg.get('bind','127.0.0.1'),link['listen']),gate.proxy(link['host'],link['port']));threading.Thread(target=server.serve_forever,daemon=True).start()
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def reply(self,status,value):
   data=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  def auth(self):return hmac.compare_digest(self.headers.get('Authorization','').encode(),b'Bearer '+token)
  def do_GET(self):
   if not self.auth():self.reply(403,{'error':'AUTH_REQUIRED'});return
   self.reply(200,{'schema':'aeris.link-state.v1','connected':gate.connected,'scope':'SIMULATOR_DATA_PLANE_ONLY','observer_channel':'AVAILABLE'})
  def do_POST(self):
   if not self.auth():self.reply(403,{'error':'AUTH_REQUIRED'});return
   try:
    n=int(self.headers.get('Content-Length','-1'));need(0<n<=1024 and not self.headers.get('Transfer-Encoding'),'BODY_LIMIT');v=decode(self.rfile.read(n));need(type(v)is dict and set(v)=={'command_id','operation'},'CONTROL_FIELDS');need(type(v['command_id'])is str and len(v['command_id'])<=80,'COMMAND_ID')
    self.reply(200,gate.change(v['command_id'],v['operation']))
   except (ValueError,KeyError):self.reply(409,{'error':'LINK_CONTROL_REJECTED'})
 ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(cfg['certificate'],cfg['private_key']);server=http.server.ThreadingHTTPServer((cfg.get('bind','127.0.0.1'),cfg['port']),Handler);server.socket=ctx.wrap_socket(server.socket,server_side=True);print('LAB_LINK_READY',flush=True);server.serve_forever()
if __name__=='__main__':main()
