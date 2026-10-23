"""Export the prepared Blender scene while omitting the static robot pose.
The browser supplies the existing simulator-derived articulated robot instead.
Load the reviewed .blend before invoking this script; it performs no execution.
"""
import bpy,sys,argparse,json,hashlib
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);args.out.parent.mkdir(parents=True,exist_ok=True)
def static_robot(o):
 while o:
  if o.name.startswith('Simulator robot geometry'):return True
  o=o.parent
 return False
bpy.ops.object.select_all(action='DESELECT');selected=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and not o.hide_render and not static_robot(o):o.select_set(True);selected.append(o.name)
assert len(selected)>300,'Prepared scene geometry missing'
bpy.ops.export_scene.gltf(filepath=str(args.out.resolve()),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
args.out.with_suffix('.json').write_text(json.dumps({'schema':'robot-demo.approved-scene-export.v1','scope':'Approved illustrative C17/hangar scenery. Dynamic robot excluded; no execution data.','blender':bpy.app.version_string,'mesh_objects':len(selected),'static_robot_exported':False,'sha256':hashlib.sha256(args.out.read_bytes()).hexdigest()},indent=2)+'\n')
print('APPROVED_SCENE_EXPORTED',len(selected),flush=True)
