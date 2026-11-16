#!/usr/bin/env python3
"""Rebuild the organized preview URDF. Requires Python, numpy and scipy.

CSV masses/limits are the source of truth. No hardware commands are generated.
The source CAD mesh geometry and the 12 intended joint axes are preserved.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
import csv, copy, re, shutil, warnings

P = Path(__file__).resolve().parents[1]
SRC = ET.parse(P/'source/original_export.urdf').getroot()
LINKS = {e.get('name'):e for e in SRC.findall('link')}
JOINTS = {e.get('name'):e for e in SRC.findall('joint')}
# Names follow exported +Y = left, -Y = right. Face direction must be confirmed
# against the manufactured assembly; no servo polarity changes are made.
MAPPING = {
 'yaw':('neck_yaw_joint','neck_yaw_link'),
 'pitch':('neck_pitch_joint','head_link'),
 'revolute_1':('right_hip_yaw_joint','right_hip_yaw_link'),
 'revolute_3':('right_hip_roll_joint','right_hip_roll_link'),
 'revolute_6':('right_hip_pitch_joint','right_thigh_link'),
 'revolute_5':('right_knee_pitch_joint','right_shank_link'),
 'revolute_4':('right_ankle_pitch_joint','right_foot_link'),
 'revolute_2':('left_hip_yaw_joint','left_hip_yaw_link'),
 'revolute_7':('left_hip_roll_joint','left_hip_roll_link'),
 'revolute_10':('left_hip_pitch_joint','left_thigh_link'),
 'revolute_9':('left_knee_pitch_joint','left_shank_link'),
 'revolute_8':('left_ankle_pitch_joint','left_foot_link'),
}

def fmt(v): return ' '.join(f'{x:.12g}' for x in np.asarray(v).ravel())
def transform(e):
 o=e.find('origin'); T=np.eye(4)
 if o is not None:
  T[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ')
  T[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
 return T
def origin(e,T):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore'); angles=Rotation.from_matrix(T[:3,:3]).as_euler('xyz')
 ET.SubElement(e,'origin',xyz=fmt(T[:3,3]),rpy=fmt(angles))
def inertia(e):
 a={k:float(v) for k,v in e.attrib.items()}
 return np.array([[a['ixx'],a['ixy'],a['ixz']],[a['ixy'],a['iyy'],a['iyz']],[a['ixz'],a['iyz'],a['izz']]])
def write_csv(path,rows):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader();w.writerows(rows)
def read_csv(path):
 with path.open(encoding='utf-8') as f:return list(csv.DictReader(f))

children={n:[] for n in LINKS}
for j in JOINTS.values(): children[j.find('parent').get('link')].append(j)
T0={'root':np.eye(4)}; GROUP={'root':'base_link'}
def walk(n):
 for j in children[n]:
  c=j.find('child').get('link');T0[c]=T0[n]@transform(j)
  GROUP[c]=MAPPING[j.get('name')][1] if j.get('name') in MAPPING else GROUP[n]
  walk(c)
walk('root')
# Only translate the root to pelvis center. Retain original root axis convention.
BASE=np.eye(4);BASE[:3,3]=T0['trunk_base_躯干底座_1__body1'][:3,3]
FRAMES={'base_link':BASE}
for old,(_,new) in MAPPING.items(): FRAMES[new]=T0[JOINTS[old].find('child').get('link')]

MOTOR_LINKS=[n for n,l in LINKS.items() if l.find('inertial/mass') is not None
 and abs(float(l.find('inertial/mass').get('value'))-1.49287e-5)<1e-10]
HEAD_MOTORS={
 'neck_yaw':[n for n in LINKS if 'lower_xl330' in n]+['root'],
 'neck_pitch':[n for n in LINKS if 'upper_xl330' in n],
}
HEAD_SUM={k:sum(float(LINKS[n].find('inertial/mass').get('value')) for n in v) for k,v in HEAD_MOTORS.items()}
MOTOR_ROLE={
 'xl330_m288_t1_1__body1_2':'right_hip_yaw_joint',
 'xl330_m288_t1_1__body1_1':'left_hip_yaw_joint',
 'xl330_m288_t1_1__body1':'right_hip_roll_joint',
 'xl330_m288_t1_1__body1_3':'left_hip_roll_joint',
 'pitch1_1__body1':'right_hip_pitch_joint',
 'xl3302_1__body1':'left_hip_pitch_joint',
 'xl3302_v1_3__body1':'right_knee_pitch_joint',
 'xl3302_v1_1__body1':'left_knee_pitch_joint',
 'xl3302_v1_4__body1':'right_ankle_pitch_joint',
 'xl3302_v1_2__body1':'left_ankle_pitch_joint',
}
BOARD_MASSES={'_autosave_bcm17_a01_e001_rev_b_pcb':.020,'board_1__board':.010,
 'respeaker_lite_v1_1_pcb':.015,'pcb__rpi4modelb__cornerradius':.046}

mass_path=P/'config/component_masses.csv'
if not mass_path.exists():
 rows=[]
 for n,l in LINKS.items():
  m=l.find('inertial/mass')
  if m is None:continue
  old=float(m.get('value')); role=''; status='ESTIMATE_CONFIRM';kind='printed_part'
  val=old*1240; basis='Assumed uniform density 1240 kg/m3; adjust for material and infill'
  if n in MOTOR_LINKS:
   val=.018;kind='leg_motor';role=MOTOR_ROLE[n]
   basis='XL330 18g placeholder; identify four XC330 locations and use verified model mass'
  elif any(n in v for v in HEAD_MOTORS.values()):
   k=next(k for k,v in HEAD_MOTORS.items() if n in v);val=.018*old/HEAD_SUM[k]
   kind='neck_motor_component';role=k+'_joint';basis='Share of one 18g XL330; source-volume distribution estimates CoM and inertia'
  elif 'bearing' in n or n.startswith('轴承'):
   val=old*7800;kind='bearing';basis='Assumed steel envelope density 7800 kg/m3; replace by catalog mass'
  elif n in BOARD_MASSES:
   val=BOARD_MASSES[n];kind='electronics';basis='Unmeasured board mass placeholder; identify exact board and weigh'
  rows.append(dict(source_link=n,rigid_link=GROUP[n],kind=kind,actuated_joint=role,mass_kg=f'{val:.12g}',status=status,basis=basis))
 write_csv(mass_path,rows)
mass_rows=read_csv(mass_path); MASSES={r['source_link']:float(r['mass_kg']) for r in mass_rows}
assert all(m>0 and np.isfinite(m) for m in MASSES.values())

limits_path=P/'config/joint_parameters.csv'
if not limits_path.exists():
 rows=[]
 for old,(new,_) in MAPPING.items():
  if old in ['yaw','pitch']:
   lim=JOINTS[old].find('limit');low=np.rad2deg(float(lim.get('lower')));high=np.rad2deg(float(lim.get('upper')))
   basis='Angular limits retained from CAD export; effort and speed are preview placeholders'
  else:
   angle=30 if 'hip_yaw' in new else 20 if 'hip_roll' in new else 45 if 'hip_pitch' in new else 60 if 'knee' in new else 25
   low,high=-angle,angle;basis='Temporary preview window around exported pose; NOT checked mechanical limits'
  rows.append(dict(joint=new,source_joint=old,lower_deg=f'{low:.8g}',upper_deg=f'{high:.8g}',effort_nm='0.15',velocity_rad_s='1.0',damping_nms_rad='0.01',friction_nm='0',motor_model='XL330-M288-T' if old in ['yaw','pitch'] else 'UNCONFIRMED_XL330_OR_XC330',servo_id='',status='PREVIEW_ONLY_CONFIRM',basis=basis))
 write_csv(limits_path,rows)
PARAMS={r['joint']:r for r in read_csv(limits_path)}

mesh_dir=P/'source/meshes'
asset_map_path=P/'source/mesh_filename_map.csv'
old_assets={r['source_mesh']:r['organized_mesh'] for r in read_csv(asset_map_path)} if asset_map_path.exists() else {}
def source_mesh_path(fn):
 direct=mesh_dir/fn
 return direct if direct.exists() else P/'meshes'/old_assets[fn]
DT=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
mesh_cache={}
def mesh_points(v):
 m=v.find('geometry/mesh');fn=m.get('filename').split('/')[-1]
 if fn not in mesh_cache:
  data=source_mesh_path(fn).read_bytes();count=int.from_bytes(data[80:84],'little')
  assert len(data)==84+50*count
  mesh_cache[fn]=np.frombuffer(data,dtype=DT,offset=84)['vertices'].reshape(-1,3).astype(float)
 return mesh_cache[fn]*np.fromstring(m.get('scale','1 1 1'),sep=' ')

R=ET.Element('robot',name='snu_gom_preview')
R.append(ET.Comment('PREVIEW MODEL: estimated masses, temporary limits, approximate collision boxes. Read docs/START_HERE.txt.'))
# A massless reference avoids the KDL root-inertia limitation. It is NOT world.
ET.SubElement(R,'link',name='base_reference')
j=ET.SubElement(R,'joint',name='base_reference_joint',type='fixed');ET.SubElement(j,'parent',link='base_reference');ET.SubElement(j,'child',link='base_link');origin(j,np.eye(4))
new_links={g:ET.SubElement(R,'link',name=g) for g in FRAMES}
part_map=[];mesh_names={}; visual_transforms={}; boxes={g:[] for g in FRAMES}
payload_path=P/'config/additional_masses.csv'
payloads=read_csv(payload_path) if payload_path.exists() else []
payloads=[p for p in payloads if p.get('enabled','1')=='1']
for p in payloads:
 assert p['rigid_link'] in FRAMES, p['rigid_link']
 assert float(p['mass_kg'])>0
 assert all(float(p[k])>0 for k in ['size_x_m','size_y_m','size_z_m'])
body_stats=[]

for g,out in new_links.items():
 inv=np.linalg.inv(FRAMES[g]);terms=[];seq=0
 for n,l in LINKS.items():
  if GROUP[n]!=g:continue
  relative=inv@T0[n]
  iner=l.find('inertial')
  if iner is not None:
   old=float(iner.find('mass').get('value'));m=MASSES[n];A=relative@transform(iner)
   I=A[:3,:3]@inertia(iner.find('inertia'))@A[:3,:3].T*(m/old)
   terms.append((m,A[:3,3],I))
  visuals=l.findall('visual')
  kind=next((r['kind'] for r in mass_rows if r['source_link']==n),'frame')
  for vi,v in enumerate(visuals):
   seq+=1;A=relative@transform(v)
   known={'00_fixed_base':'neck_base_plate','03_center_riser_and_crossbar':'torso_center_riser',
    '04_left_torso_rail':'torso_left_rail','04_right_torso_rail':'torso_right_rail',
    '05_neck_platform':'torso_neck_platform','06_electronics_shelves_rear_brace':'torso_electronics_shelves',
    '18_hollow_mascot_head':'head_shell','19_original_detail_0':'head_right_ear',
    '20_original_detail_1':'head_nose','21_original_detail_2':'head_left_ear',
    'pcb__rpi4modelb__cornerradius':'raspberry_pi_board','respeaker_lite_v1_1_pcb':'respeaker_board',
    '_autosave_bcm17_a01_e001_rev_b_pcb':'openrb150_controller','board_1__board':'bno085_imu',
    'trunk_base_躯干底座_1__body1':'pelvis_bridge','16_yaw_carrier':'neck_yaw_carrier','17_pitch_bracket':'head_pitch_bracket',
    'right_1__body1':'right_foot','right_1__body1_1':'left_foot'}
   component=known.get(n,MOTOR_ROLE.get(n,'').replace('_joint','_motor') or f'{g}_{kind}_{seq:02d}')
   vv=ET.SubElement(out,'visual',name=component)
   origin(vv,A);geom=copy.deepcopy(v.find('geometry'));oldfile=geom.find('mesh').get('filename').split('/')[-1]
   if oldfile not in mesh_names:
    mesh_names[oldfile]=component+'.stl'
    src_path=source_mesh_path(oldfile);dest_path=P/'meshes'/mesh_names[oldfile]
    if src_path.resolve()!=dest_path.resolve():shutil.copyfile(src_path,dest_path)
   geom.find('mesh').set('filename','package://snu_gom_description/meshes/'+mesh_names[oldfile]);vv.append(geom)
   if v.find('material') is not None:vv.append(copy.deepcopy(v.find('material')))
   visual_transforms[(n,vi)]=(g,A)
   part_map.append(dict(source_link=n,source_mesh=oldfile,rigid_link=g,visual_name=vv.get('name'),mesh=mesh_names[oldfile],kind=kind))
  # Boxes follow actual part-local mesh frames; do not enclose the whole robot.
  # Use one envelope per detailed neck servo, not one per internal screw.
  selected=n in MOTOR_LINKS or n.startswith('link_v2_') or n.startswith('link_to_link_') or n in ['01_lower_xl330_00','22_upper_xl330_00','18_hollow_mascot_head','right_1__body1','right_1__body1_1','04_left_torso_rail','04_right_torso_rail']
  if selected:
   for v in visuals:
    A=relative@transform(v);pts=mesh_points(v);lo=pts.min(0);hi=pts.max(0)
    center=(lo+hi)/2;size=hi-lo;B=A.copy();B[:3,3]=A[:3,:3]@center+A[:3,3]
    boxes[g].append((n,B,size))
 # Give link-only hip brackets a conservative envelope when no motor was selected.
 if not boxes[g]:
  pts=[]
  for n,l in LINKS.items():
   if GROUP[n]!=g:continue
   for v in l.findall('visual'):
    A=inv@T0[n]@transform(v);a=mesh_points(v);pts.append(a@A[:3,:3].T+A[:3,3])
  a=np.concatenate(pts);lo=a.min(0);hi=a.max(0);B=np.eye(4);B[:3,3]=(lo+hi)/2
  boxes[g].append(('group_envelope',B,hi-lo))
 # Additional hardware: mass/inertia only, not collision or claimed CAD fit.
 for p in payloads:
  if p['rigid_link']!=g:continue
  m=float(p['mass_kg']);x=np.array([float(p[k]) for k in ['x_m','y_m','z_m']])
  sx,sy,sz=[float(p[k]) for k in ['size_x_m','size_y_m','size_z_m']]
  J=m/12*np.diag([sy*sy+sz*sz,sx*sx+sz*sz,sx*sx+sy*sy])
  terms.append((m,x,J))
 mass=sum(t[0] for t in terms);c=sum(m*x for m,x,_ in terms)/mass
 I=sum(J+m*((x-c)@(x-c)*np.eye(3)-np.outer(x-c,x-c)) for m,x,J in terms)
 eig=np.linalg.eigvalsh(I);assert min(eig)>0 and eig[-1]<=sum(eig[:2])+1e-12
 ie=ET.SubElement(out,'inertial');A=np.eye(4);A[:3,3]=c;origin(ie,A);ET.SubElement(ie,'mass',value=fmt([mass]))
 ET.SubElement(ie,'inertia',**{k:f'{v:.12g}' for k,v in zip(['ixx','ixy','ixz','iyy','iyz','izz'],[I[0,0],I[0,1],I[0,2],I[1,1],I[1,2],I[2,2]])})
 body_stats.append(dict(link=g,mass_kg=f'{mass:.9g}',com_x_m=f'{c[0]:.9g}',com_y_m=f'{c[1]:.9g}',com_z_m=f'{c[2]:.9g}'))
 for i,(n,B,size) in enumerate(boxes[g]):
  ce=ET.SubElement(out,'collision',name=f'{g}_collision_{i+1:02d}');origin(ce,B);ge=ET.SubElement(ce,'geometry');ET.SubElement(ge,'box',size=fmt(size))

for old,(new,child) in MAPPING.items():
 src=JOINTS[old];parent=GROUP[src.find('parent').get('link')];j=ET.SubElement(R,'joint',name=new,type='revolute')
 ET.SubElement(j,'parent',link=parent);ET.SubElement(j,'child',link=child)
 origin(j,np.linalg.inv(FRAMES[parent])@FRAMES[child]);j.append(copy.deepcopy(src.find('axis')))
 p=PARAMS[new];lo,hi=np.deg2rad([float(p['lower_deg']),float(p['upper_deg'])]);assert lo<hi
 ET.SubElement(j,'limit',lower=fmt([lo]),upper=fmt([hi]),effort=p['effort_nm'],velocity=p['velocity_rad_s'])
 ET.SubElement(j,'dynamics',damping=p['damping_nms_rad'],friction=p['friction_nm'])

ET.indent(R,space='  ');ET.ElementTree(R).write(P/'urdf/snu_gom_preview.urdf',encoding='utf-8',xml_declaration=True)
# Relative mesh paths are convenient for direct non-ROS importers; identical model.
portable=copy.deepcopy(R)
for m in portable.iter('mesh'):m.set('filename',m.get('filename').replace('package://snu_gom_description/','../'))
ET.ElementTree(portable).write(P/'urdf/snu_gom_preview_relative.urdf',encoding='utf-8',xml_declaration=True)
write_csv(P/'docs/part_name_map.csv',part_map)
write_csv(P/'docs/rigid_body_masses.csv',body_stats)
write_csv(asset_map_path,[dict(source_mesh=a,organized_mesh=b) for a,b in mesh_names.items()])
write_csv(P/'docs/link_name_map.csv',[dict(source_link=n,rigid_link=GROUP[n],note='Planar helper removed' if n.startswith('평면') else 'Rigidly consolidated') for n in LINKS])

# Compare full FK at neutral and 20 random articulated configurations. This
# catches origin, axis and rigid-group errors without assuming a physics engine.
newjs=R.findall('joint');newchildren={n:[] for n in ['base_reference']+list(FRAMES)}
for j in newjs:newchildren[j.find('parent').get('link')].append(j)
def fk_source(q):
 ts={'root':np.eye(4)}
 def rec(n):
  for j in children[n]:
   c=j.find('child').get('link');A=transform(j)
   if j.get('name') in MAPPING:
    ax=np.fromstring(j.find('axis').get('xyz'),sep=' ');B=np.eye(4);B[:3,:3]=Rotation.from_rotvec(ax*q.get(MAPPING[j.get('name')][0],0)).as_matrix();A=A@B
   ts[c]=ts[n]@A;rec(c)
 rec('root');return ts
def fk_new(q):
 ts={'base_reference':np.eye(4)}
 def rec(n):
  for j in newchildren[n]:
   c=j.find('child').get('link');A=transform(j)
   if j.get('type')=='revolute':
    ax=np.fromstring(j.find('axis').get('xyz'),sep=' ');B=np.eye(4);B[:3,:3]=Rotation.from_rotvec(ax*q.get(j.get('name'),0)).as_matrix();A=A@B
   ts[c]=ts[n]@A;rec(c)
 rec('base_reference');return ts
rng=np.random.default_rng(330);err=0
for t in range(21):
 q={name:float(rng.uniform(-.2,.2)) if t else 0 for name in PARAMS};a=fk_source(q);b=fk_new(q)
 for (n,vi),(g,A) in visual_transforms.items():
  expect=np.linalg.inv(BASE)@a[n]@transform(LINKS[n].findall('visual')[vi]);actual=b[g]@A;err=max(err,float(np.abs(expect-actual).max()))
assert err<1e-8,err
mass=sum(MASSES.values())+sum(float(p['mass_kg']) for p in payloads)
serialized_mass=sum(float(l.find('inertial/mass').get('value')) for l in R.findall('link') if l.find('inertial/mass') is not None)
assert abs(serialized_mass-mass)<1e-9
report=f'''LOCAL VALIDATION\nPhysical rigid bodies: {len(FRAMES)}\nReference frames: 1 (not world)\nRevolute joints: {len(MAPPING)}\nFixed reference joints: 1\nPrismatic joints: 0\nVisual instances preserved: {len(part_map)}\nCollision boxes: {sum(map(len,boxes.values()))}\nEstimated total mass: {mass:.6f} kg\nFK comparisons: 21 poses x {len(part_map)} visual instances\nMaximum transform matrix error: {err:.3e}\nAll aggregate inertia tensors positive definite and satisfy principal-moment triangle inequality.\nGeometry scale, individual axes and zero-pose placement preserved, modulo one root translation.\nBase translated to original pelvis center {fmt(BASE[:3,3])} m.\n\nNOT VALIDATED: physics engine import, balance, walking, self-collision clearance, collision simplifications, mechanical limits, real masses, servo sign/IDs, installed hardware versus guide mapping.\nThe estimated mass excludes components absent from the source, including any unmodeled battery, wiring or outer torso/paw shell.\n'''
report=report.replace('The estimated mass excludes components absent from the source, including any unmodeled battery, wiring or outer torso/paw shell.',f'Includes {len(payloads)} enabled additional mass allowances; see config/additional_masses.csv. Allowances are not physical CAD parts and their mounting/clearance is unverified.')
(P/'docs/VALIDATION.txt').write_text(report)
print(report)

if __name__=='__main__': pass
