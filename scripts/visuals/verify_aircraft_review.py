"""Independent file/identity checks for the three Blender review stills.
These checks do not approve visual quality or qualify robot hardware.
"""
import hashlib,json,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EXPECTED=['01-hangar','02-aircraft-detail','03-robot-cell']
def need(condition,message):
 if not condition:raise ValueError(message)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def png_dimensions(p):
 b=p.read_bytes();need(b[:8]==b'\x89PNG\r\n\x1a\n','PNG signature');offset=8;compressed=[];dimensions=None;ended=False
 while offset<len(b):
  n=struct.unpack('>I',b[offset:offset+4])[0];kind=b[offset+4:offset+8];data=b[offset+8:offset+8+n];crc=struct.unpack('>I',b[offset+8+n:offset+12+n])[0];need(zlib.crc32(kind+data)&0xffffffff==crc,'PNG CRC mismatch')
  if kind==b'IHDR':dimensions=struct.unpack('>II',data[:8])
  elif kind==b'IDAT':compressed.append(data)
  elif kind==b'IEND':ended=True;break
  offset+=n+12
 need(ended and compressed and dimensions,'Incomplete PNG');need(len(zlib.decompress(b''.join(compressed)))>dimensions[0]*dimensions[1],'Incomplete pixel data');return dimensions
def verify(folder,asset_manifest=ROOT/'presentation/assets/aircraft-review/manifest.json',asset=ROOT/'presentation/assets/aircraft-review/c17.glb'):
 manifest=json.loads(asset_manifest.read_text());need(manifest['sha256']==digest(asset),'Source asset identity changed');need(manifest['license']=='CC-BY-4.0' and manifest['creator'] and manifest['license_url'],'Asset attribution missing')
 b=asset.read_bytes();need(b[:4]==b'glTF' and struct.unpack('<I',b[8:12])[0]==len(b),'Invalid GLB');n=struct.unpack('<I',b[12:16])[0];gltf=json.loads(b[20:20+n]);need(all('uri' not in v for v in gltf.get('buffers',[])+gltf.get('images',[])),'External asset dependency')
 report=json.loads((folder/'render-report.json').read_text());need(report['engine']=='CYCLES','Cycles render required');need(report['physical_motion_authorized'] is False,'Visual review cannot authorize motion');need([v['name'] for v in report['views']]==EXPECTED,'Three named views required');need(report['dimensions'][0]>=1920 and report['dimensions'][0]*9==report['dimensions'][1]*16,'Full-resolution 16:9 required')
 hashes=[]
 for view in report['views']:
  p=folder/(view['name']+'.png');need(list(png_dimensions(p))==report['dimensions'],'PNG dimensions mismatch');need(digest(p)==view['sha256'],'Rendered image identity changed');hashes.append(view['sha256'])
 need(len(set(hashes))==3,'Views must be distinct images')
 return {'status':'PASS_ARTIFACT_INTEGRITY','scope':'Three visual review images only; visual acceptance is pending the user. No execution, hardware or real-time qualification.','source_asset_sha256':manifest['sha256'],'decoded_asset_sha256':report['asset_sha256'],'dimensions':report['dimensions'],'views':EXPECTED,'physical_motion_authorized':False}
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path);args=ap.parse_args();print(json.dumps(verify(args.folder),indent=2))
