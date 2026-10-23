"""Build a labeled historical view and a kinematic visualization from retained bytes."""
from pathlib import Path
import hashlib,json,shutil,sqlite3,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];public=ROOT/'frontend/public';run=ROOT/'proof/skill_transfer_network_v1/runs/flightpath-002';source=ROOT/'proof/control/assets/ur5e'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((ROOT/'verification/evy-action-integration-03/result.json').read_bytes());tasks=[]
with sqlite3.connect('file:'+str((run/'edge/evidence/rust.snapshot').resolve())+'?mode=ro&immutable=1',uri=True) as db:
 for name,digest,status,receipt in db.execute('SELECT id,release_digest,status,receipt FROM tasks ORDER BY rowid'):
  frames=[]
  for raw, in db.execute('SELECT payload FROM samples WHERE task=? ORDER BY tick',(name,)):
   s=json.loads(raw);frames.append({'tick':s['tick'],'q':s['after']['q'],'velocity':s['after']['velocity'],'simulation_seconds':s['after']['simulation_seconds'],'goal_index':s['goal_index']})
  tasks.append({'task':name,'release_digest':digest,'status':status,'receipt':json.loads(receipt),'frames':frames})
(public/'action-proof.json').write_text(json.dumps({'schema':'aeris.recorded-action-proof.v1','source':'RETAINED_FLIGHTPATH_PROOF','recorded_at':summary['observed_utc'],'physical_motion_authorized':False,'summary':summary,'tasks':tasks,'source_identities':{'audit':sha(run/'audit-result.json'),'database':sha(run/'edge/evidence/rust.snapshot')}},separators=(',',':'))+'\n')
xml=ET.parse(source/'ur5e.xml').getroot();materials={m.attrib['name']:[float(x) for x in m.attrib['rgba'].split()] for m in xml.findall('./asset/material')};joint_index=[0]
def vec(node,key,default):return [float(x) for x in node.attrib.get(key,default).split()]
def body(node):
 j=node.find('joint');joint=None
 if j is not None:joint={'name':j.attrib['name'],'index':joint_index[0],'axis':vec(j,'axis','0 1 0')};joint_index[0]+=1
 return {'name':node.attrib['name'],'position':vec(node,'pos','0 0 0'),'quaternion_wxyz':vec(node,'quat','1 0 0 0'),'joint':joint,'geometries':[{'mesh':g.attrib['mesh'],'rgba':materials[g.attrib['material']]} for g in node.findall('geom') if g.attrib.get('class')=='visual' and 'mesh'in g.attrib],'children':[body(b) for b in node.findall('body')]}
model={'schema':'aeris.visual-model.v1','source_sha256':sha(source/'ur5e.xml'),'units':'metres_radians','scope':'Presentation geometry from the simulator MJCF; not physical calibration.','root':body(xml.find('./worldbody/body'))}
modeldir=public/'models/ur5e';modeldir.mkdir(parents=True,exist_ok=True)
(modeldir/'model.json').write_text(json.dumps(model,separators=(',',':'))+'\n')
for p in (source/'assets').glob('*.obj'):shutil.copyfile(p,modeldir/p.name)
shutil.copyfile(source/'LICENSE',modeldir/'LICENSE')
print('Built retained-proof data and MJCF-derived six-joint visual model.')
