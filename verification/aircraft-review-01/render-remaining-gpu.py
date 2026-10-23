import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path.cwd();out=root/'.production/aircraft-review/gpu';out.mkdir(exist_ok=True);prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s=bpy.context.scene;s.cycles.device='GPU';cam=s.camera
r={'scope':'AUTHORED VISUAL REVIEW / NOT HARDWARE OR EXECUTION EVIDENCE','asset_sha256':hashlib.sha256((root/'.production/aircraft-review/repeatable-decoded.glb').read_bytes()).hexdigest(),'renderer':bpy.app.version_string,'engine':'CYCLES','device':'METAL','samples':s.cycles.samples,'dimensions':[s.render.resolution_x,s.render.resolution_y],'views':[],'physical_motion_authorized':False}
for name,pos,target,lens in [('02-aircraft-detail',(26,-26,7),(12,-4,5.8),46),('03-robot-cell',(12.7,-32,3.0),(9,-26.5,1.45),43)]:
 cam.location=pos;cam.data.lens=lens;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);r['views'].append({'name':name,'position':pos,'target':target,'lens_mm':lens,'sha256':hashlib.sha256(Path(s.render.filepath).read_bytes()).hexdigest(),'device':'METAL'});(out/'render-report.json').write_text(json.dumps(r,indent=2)+'\n')
