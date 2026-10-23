"""Three authored review stills from one licensed GLB and the existing robot geometry.
Run with Blender 4.5+: blender -b --python this_file -- --asset model.glb --out folder.
No simulator, robot or network connection is opened by this renderer.
"""
import argparse,json,math,sys,hashlib
from pathlib import Path
import bpy
from mathutils import Vector,Quaternion
ap=argparse.ArgumentParser();ap.add_argument('--asset',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--width',type=int,default=2560);ap.add_argument('--samples',type=int,default=96);ap.add_argument('--views',nargs='*');ap.add_argument('--device',choices=['CPU','METAL'],default='CPU');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);args.out.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
def material(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
steel=material('Powder-coated structural steel',(.065,.083,.1),.65,.38);silver=material('Machined stainless',(.38,.44,.49),.9,.25);yellow=material('Safety ochre paint',(.6,.33,.045),.2,.5);dark=material('Equipment graphite',(.026,.038,.048),.6,.3);blue=material('Tooling enamel',(.08,.2,.27),.5,.28)
def cube(name,loc,scale,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  m=o.modifiers.new('Machined edge radii','BEVEL');m.width=bevel;m.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
def cyl(name,loc,r,depth,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o
def beam(a,b,r=.08,mat=steel):
 d=Vector(b)-Vector(a);o=cyl('Structural brace',(Vector(a)+Vector(b))*.5,r,d.length,mat);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,target,power,size,color=(1,1,1),size_y=None):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='RECTANGLE';o.data.size=size;o.data.size_y=size_y or size;o.data.color=color;aim(o,target);return o
# Preserve the imported aircraft's geometry/materials. Catalogue dimensions are normalized
# to an illustrative 53 m overall length, not engineering-calibrated dimensions.
bpy.ops.import_scene.gltf(filepath=str(args.asset.resolve()));parts=list(bpy.context.scene.objects);coords=[o.matrix_world@Vector(c) for o in parts if o.type=='MESH' for c in o.bound_box];lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)]);scale=53/(hi.y-lo.y)
aircraft=bpy.data.objects.new('LICENSED C17 / illustrative maintenance configuration',None);bpy.context.collection.objects.link(aircraft)
for o in parts:
 if o.parent is None:o.parent=aircraft
 for m in o.material_slots:
  if m.material and m.material.use_nodes:
   p=m.material.node_tree.nodes.get('Principled BSDF')
   if p and not p.inputs['Roughness'].is_linked:p.inputs['Roughness'].default_value=max(.32,p.inputs['Roughness'].default_value)
aircraft.scale=(scale,)*3;aircraft.location=(-(lo.x+hi.x)*scale/2,-(lo.y+hi.y)*scale/2,-lo.z*scale)
bpy.context.view_layer.update()
# Catalogue conversion left two topcoat surfaces black. Replace only these
# named control-surface materials; retain mesh geometry and the remaining textures.
topcoat=material('Review control-surface topcoat',(.23,.27,.30),.25,.42)
for o in parts:
 if o.name in ['C17_Globemaster_With_Animation_Part260','C17_Globemaster_With_Animation_Part174','C17_Globemaster_With_Animation_Part272','C17_Globemaster_With_Animation_Part176']:
  o.hide_render=True
 if o.name in ['C17_Globemaster_With_Animation_Part266','C17_Globemaster_With_Animation_Part175']:
  o.data.materials.clear();o.data.materials.append(topcoat)
# The optimized viewer stores wing topcoat/texture layers as overlapping meshes.
# Use one neutral topcoat and suppress duplicate layer shadows for these wide skins.
for o in parts:
 if o.type!='MESH':continue
 points=[o.matrix_world@Vector(v) for v in o.bound_box]
 span=max(v.x for v in points)-min(v.x for v in points)
 names=[m.name for m in o.data.materials if m]
 if span>9 and any(n.endswith(('Material03','Material09')) for n in names):
  o.data.materials.clear();o.data.materials.append(topcoat);o.visible_shadow=False
jack_contacts={}
for x,y in [(-3,3),(3,3),(-2,-12),(2,-12)]:
 hit,loc,*_=bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((x,y,.04)),Vector((0,0,1)),distance=20)
 jack_contacts[(x,y)]=loc.z if hit else 2.5
# Large, physically lit assembly hall with concrete texture, structural depth and fixtures.
floor=material('Cast concrete with fine aggregate',(.17,.19,.2),.12,.48);nodes=floor.node_tree.nodes;links=floor.node_tree.links;p=nodes.get('Principled BSDF');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=145;noise.inputs['Detail'].default_value=3;bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19;bump.inputs['Distance'].default_value=.045;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
cube('Concrete slab',(0,0,-.18),(110,130,.3),floor)
for x in range(-45,46,9):cube('Concrete expansion joint',(x,0,-.022),(.018,110,.012),dark)
for y in range(-45,61,9):cube('Concrete expansion joint',(0,y,-.022),(90,.018,.012),dark)
for x in [-28,28]:cube('Aircraft clearance stripe',(x,0,-.011),(.15,75,.018),yellow)
for y in [-32,35]:cube('Aircraft clearance stripe',(0,y,-.011),(56,.15,.018),yellow)
wall=material('Insulated wall panels',(.22,.25,.27),.35,.52)
cube('Rear hangar wall',(0,42,11),(84,.35,22),wall)
for x in [-40,40]:
 cube('Side wall',(x,7,11),(.35,72,22),wall)
 for y in range(-26,43,8):
  cube('Steel column',(x,y,10),(.42,.6,20),steel);cube('Column base plate',(x,y,.14),(.95,1.1,.28),silver)
  for sx in [-.32,.32]:
   for sy in [-.4,.4]:cyl('Anchor bolt',(x+sx,y+sy,.31),.055,.1,silver)
for y in range(-26,43,8):
 beam((-40,y,19),(40,y,19),.15);beam((-40,y,22),(40,y,22),.15)
 for x in range(-40,40,5):beam((x,y,19),(x+2.5,y,22),.085);beam((x+2.5,y,22),(x+5,y,19),.085)
 for x in [-24,0,24]:
  cube('Ceiling light housing',(x,y,18.8),(7,.6,.1),steel)
  area('Overhead broad softbox',(x,y,18.7),(x,y,0),1500,7,(.86,.93,1),1.6)
for x in [-36,36]:cube('Crane runway',(x,5,16),(.4,66,.65),yellow)
cube('Overhead crane bridge',(0,22,16),(73,.8,.9),yellow)
# Back door segmentation and lower service doors.
for i in range(25):cube('Hangar door slat',(0,41.7,.4+i*.67),(59,.12,.6),steel)
for x in [-35,35]:cube('Personnel service door',(x,41.65,1.25),(1.6,.15,2.5),blue)
# Maintenance jacks visibly support this illustrative aircraft configuration.
for x,y in [(-3,3),(3,3),(-2,-12),(2,-12)]:
 top=jack_contacts[(x,y)];cube('Aircraft jack footing',(x,y,.12),(1.3,1.3,.24),yellow);cyl('Hydraulic maintenance jack',(x,y,(top+.24)/2),.16,top-.24,silver);cube('Jack contact pad',(x,y,top-.015),(.42,.42,.045),dark,.015);beam((x-.5,y,0),(x,y,2),.055,yellow);beam((x+.5,y,0),(x,y,2),.055,yellow)
# Real simulator-derived UR5e visual hierarchy; positioning scene only.
q=[-1.5708,-1.5708,1.5708,-1.5708,-1.5708,0];cell=(9,-27,0)
robot_anchor=bpy.data.objects.new('Simulator robot geometry / no physical calibration',None);bpy.context.collection.objects.link(robot_anchor);robot_anchor.location=(cell[0],cell[1],.85)
def robot(body,parent):
 o=bpy.data.objects.new(body['name'],None);bpy.context.collection.objects.link(o);o.parent=parent;o.location=body['position'];o.rotation_mode='QUATERNION';rot=Quaternion(body['quaternion_wxyz']).normalized()
 if body['joint']:rot=rot@Quaternion(Vector(body['joint']['axis']),q[body['joint']['index']])
 o.rotation_quaternion=rot
 for g in body['geometries']:
  vertices=[];faces=[]
  for line in (root/'frontend/public/models/ur5e'/(g['mesh']+'.obj')).read_text().splitlines():
   tokens=line.split()
   if not tokens:continue
   if tokens[0]=='v':vertices.append(tuple(map(float,tokens[1:4])))
   elif tokens[0]=='f':faces.append(tuple(int(t.split('/')[0])-1 for t in tokens[1:]))
  data=bpy.data.meshes.new(g['mesh']);data.from_pydata(vertices,[],faces);data.update();data.polygons.foreach_set('use_smooth',[True]*len(data.polygons));mesh=bpy.data.objects.new(g['mesh'],data);bpy.context.collection.objects.link(mesh);mesh.parent=o;mesh.data.materials.append(material('Robot '+g['mesh'],tuple(g['rgba'][:3]),.55,.24))
 for child in body['children']:robot(child,o)
robot(json.loads((root/'frontend/public/models/ur5e/model.json').read_text())['root'],robot_anchor)
cube('Robot plinth',(cell[0],cell[1],.4),(.85,.8,.8),dark,.025);cube('Robot mounting plate',(cell[0],cell[1],.82),(.95,.9,.045),silver,.012)
# Curved workpiece and fixture; no inspection accuracy or physical process claim.
verts=[];faces=[];nx=40;ny=18
for i in range(nx+1):
 x=i/nx*1.35-.675
 for j in range(ny+1):verts.append((cell[0]-.1+x,cell[1]+.7+j/ny*.75,1.6+.22*x*x))
for i in range(nx):
 for j in range(ny):a=i*(ny+1)+j;faces.append((a,a+1,a+ny+2,a+ny+1))
mesh=bpy.data.meshes.new('Curved skin mesh');mesh.from_pydata(verts,[],faces);mesh.update();panel=bpy.data.objects.new('Illustrative aircraft skin in fixture',mesh);bpy.context.collection.objects.link(panel);panel.data.materials.append(silver);sol=panel.modifiers.new('Skin thickness','SOLIDIFY');sol.thickness=.012
for dx in [-.5,.5]:
 for dy in [.78,1.32]:cube('Workpiece support pad',(cell[0]-.1+dx,cell[1]+dy,1.46),(.09,.09,.32),dark,.008)
cube('Inspection fixture base',(cell[0],cell[1]+1.05,1.25),(1.65,1.15,.08),blue,.015)
for x in [-.65,.65]:
 for y in [.65,1.4]:cube('Fixture leg',(cell[0]+x,cell[1]+y,.63),(.07,.07,1.23),steel,.006)
for x in [-1.5,1.5]:cube('Cell boundary stripe',(cell[0]+x,cell[1]+.5,-.009),(.06,4,.02),yellow)
for y in [-1.5,2.5]:cube('Cell boundary stripe',(cell[0],cell[1]+y,-.009),(3,.06,.02),yellow)
# Workbench/edge chassis with layered fins and cable route.
cube('Edge equipment trolley',(cell[0]+1.2,cell[1]+.6,.72),(.5,.6,1.4),dark,.025)
for i in range(20):cube('Cooling fin',(cell[0]+1.46,cell[1]+.6,.35+i*.035),(.025,.5,.012),silver,.003)
for x,y in [(12,-24),(17,-18),(-16,-12),(-23,18),(27,12)]:
 cube('Rolling tool cabinet',(x,y,.65),(1.3,.7,1.1),blue,.035);cube('Cabinet worktop',(x,y,1.23),(1.4,.8,.06),silver,.02)
 for i in range(5):cube('Drawer face',(x,y-.36,.3+i*.18),(1.2,.025,.13),dark,.01);cube('Drawer pull',(x,y-.39,.32+i*.18),(.45,.035,.025),silver,.005)
 for dx in [-.5,.5]:
  for dy in [-.22,.22]:cyl('Cabinet caster',(x+dx,y+dy,.08),.08,.09,dark)
# Daylight through the front opening plus warm/cool industrial practicals.
w=bpy.data.worlds.new('Daylight');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.55,.68,.82,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.16;bpy.context.scene.world=w
area('Hangar daylight entrance',(0,-42,14),(0,0,5),30000,42,(.76,.86,1),19)
area('Warm side reflection',(-30,-10,12),(0,-8,5),18000,15,(1,.78,.55),12)
area('Robot cell soft key',(12,-30,5),(9,-26,1.3),450,4,(.8,.92,1),3)
bpy.ops.object.light_add(type='SUN',location=(20,-35,30));sun=bpy.context.object;sun.rotation_euler=(math.radians(24),math.radians(-15),math.radians(-25));sun.data.energy=.7;sun.data.angle=.09
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=args.samples;
if args.device=='METAL':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 if not any(d.type=='METAL' for d in prefs.devices):raise RuntimeError('No Metal rendering device available; select CPU explicitly.')
 for d in prefs.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
s.cycles.use_denoising=True;s.cycles.max_bounces=8;s.cycles.transparent_max_bounces=8;s.render.resolution_x=args.width;s.render.resolution_y=round(args.width*9/16);s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.render.film_transparent=False;s.view_settings.exposure=-.25
views=[('01-hangar',(39,-56,14),(0,-1,6),34),('02-aircraft-detail',(26,-26,7),(12,-4,5.8),46),('03-robot-cell',(12.7,-32,3.0),(9,-26.5,1.45),43)]
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.clip_end=300

report={'scope':'AUTHORED VISUAL REVIEW / NOT HARDWARE OR EXECUTION EVIDENCE','asset_sha256':hashlib.sha256(args.asset.read_bytes()).hexdigest(),'renderer':bpy.app.version_string,'engine':'CYCLES','device':args.device,'samples':args.samples,'dimensions':[s.render.resolution_x,s.render.resolution_y],'views':[],'physical_motion_authorized':False}
for name,pos,target,lens in views:
 if args.views and name not in args.views:continue
 cam.location=pos;cam.data.lens=lens;aim(cam,target)
 if name==views[0][0]:bpy.ops.wm.save_as_mainfile(filepath=str((args.out/'aircraft-review.blend').resolve()))
 s.render.filepath=str((args.out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True);report['views'].append({'name':name,'position':pos,'target':target,'lens_mm':lens,'sha256':hashlib.sha256(Path(s.render.filepath).read_bytes()).hexdigest()});(args.out/'render-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('REVIEW_STILLS_RENDERED',json.dumps(report),flush=True)
