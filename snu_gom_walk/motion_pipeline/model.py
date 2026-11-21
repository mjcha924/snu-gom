"""Explicit robot profile and lossless-inertia MuJoCo collision adapter.

No source URDF is edited. Unknown joint/geometry types fail instead of silently
substituting a proxy. Mesh collisions use MuJoCo's convex representation.
"""
import copy
import hashlib
import itertools
import json
import re
import struct
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE = ROOT / 'configs/motion_pipeline/gom.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def origin(element):
    T=np.eye(4);o=element.find('origin')
    if o is not None:
        T[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ')
        T[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
    return T


def numbers(a):
    return ' '.join(f'{float(x):.15g}' for x in a)


def pose(T):
    return dict(pos=numbers(T[:3,3]),quat=numbers(Rotation.from_matrix(T[:3,:3]).as_quat()[[3,0,1,2]]))


def mesh_vertices(path):
    """Local STL/OBJ contact hull vertices; visual meshes are never substituted."""
    path=Path(path);data=path.read_bytes()
    if path.suffix.lower()=='.stl':
        count=struct.unpack_from('<I',data,80)[0] if len(data)>=84 else 0
        if len(data)==84+50*count and count:
            dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
            vertices=np.frombuffer(data,offset=84,count=count,dtype=dtype)['vertices'].reshape(-1,3)
        else:
            rows=re.findall(r'\bvertex\s+([^\r\n]+)',data.decode('ascii'))
            vertices=np.array([[float(x) for x in row.split()] for row in rows])
    elif path.suffix.lower()=='.obj':
        vertices=np.array([[float(x) for x in line.split()[1:4]] for line in data.decode().splitlines() if line.startswith('v ')])
    else:raise ValueError('Foot contact sampling supports STL/OBJ meshes; export the collision hull or add a geometry adapter')
    points=np.unique(vertices,axis=0)
    if len(points)<4 or not np.isfinite(points).all():raise ValueError('Invalid collision mesh')
    return points[ConvexHull(points).vertices]


class RobotModel:
    def __init__(self,profile=DEFAULT_PROFILE,urdf=None,with_physics=True):
        self.profile=copy.deepcopy(profile if isinstance(profile,dict) else json.loads(Path(profile).read_text(encoding='utf-8')))
        self.urdf=Path(urdf or self.profile['urdf'])
        if not self.urdf.is_absolute():self.urdf=ROOT/self.urdf
        self.urdf=self.urdf.resolve()
        self.profile['urdf']=self.urdf.relative_to(ROOT).as_posix() if self.urdf.is_relative_to(ROOT) else str(self.urdf)
        self.robot=ET.parse(self.urdf).getroot()
        self.names=self.profile['joint_order'];self.feet=self.profile['feet']
        if len(set(self.names))!=len(self.names) or len(self.feet)!=2:raise ValueError('Duplicate joints or missing bilateral feet')
        self.links={l.get('name'):l for l in self.robot.findall('link')}
        if len(self.links)!=len(self.robot.findall('link')):raise ValueError('Duplicate links')
        joints=self.robot.findall('joint');active={j.get('name'):j for j in joints if j.get('type')!='fixed'}
        if set(active)!=set(self.names):raise ValueError('URDF actuated joints changed; update joint_order and the training adapter explicitly')
        roots=set(self.links)-{j.find('child').get('link') for j in joints}
        if roots!={self.profile['root_link']}:raise ValueError('Profile root does not match the unique URDF root')
        if any(n not in self.links for n in self.feet+[self.profile['torso_link']]):raise ValueError('Profile body name missing')
        self.tree=[];available=set(roots);pending=joints.copy()
        while pending:
            found=[j for j in pending if j.find('parent').get('link') in available]
            if not found:raise ValueError('Disconnected/cyclic URDF')
            for j in found:
                if j.get('type') not in ('fixed','revolute','continuous','prismatic') or j.find('mimic') is not None:
                    raise ValueError('Unsupported/mimic joint requires an explicit adapter: '+j.get('name'))
                self.tree.append(j);available.add(j.find('child').get('link'));pending.remove(j)
        if available!=set(self.links):raise ValueError('Disconnected links')
        self.lower=[];self.upper=[];self.speed=[];self.effort=[];self.urdf_lower=[];self.urdf_upper=[]
        for n in self.names:
            j=active[n];limit=j.find('limit')
            if limit is None:raise ValueError('Explicit effort/speed and position ranges required: '+n)
            lo=float(limit.get('lower',-np.pi));hi=float(limit.get('upper',np.pi))
            self.urdf_lower.append(lo);self.urdf_upper.append(hi)
            working=self.profile.get('working_limits',{}).get(n,[lo,hi])
            lo=max(lo,working[0]);hi=min(hi,working[1])
            if not lo<hi:raise ValueError('Empty joint working range: '+n)
            self.lower.append(lo);self.upper.append(hi);self.speed.append(float(limit.get('velocity')));self.effort.append(float(limit.get('effort')))
        self.lower=np.asarray(self.lower);self.upper=np.asarray(self.upper);self.speed=np.asarray(self.speed);self.effort=np.asarray(self.effort)
        self.urdf_lower=np.asarray(self.urdf_lower);self.urdf_upper=np.asarray(self.urdf_upper)
        if not np.isfinite([self.lower,self.upper,self.speed,self.effort]).all() or min(self.speed.min(),self.effort.min())<=0:raise ValueError('Nonfinite/nonpositive limits')
        self.urdf_speed=self.speed.copy();self.urdf_effort=self.effort.copy()
        from .motors import limits
        self.effort,self.speed=limits(self.profile,self.names,self.urdf_effort,self.urdf_speed)
        self.nominal=np.array([self.profile.get('nominal_joints',{}).get(n,0.) for n in self.names])
        if ((self.nominal<self.lower)|(self.nominal>self.upper)).any():raise ValueError('Nominal pose outside revised joint ranges; edit nominal_joints')
        self.hashes={'urdf':digest(self.urdf)};self.meshes={}
        for mesh in self.robot.findall('.//mesh'):
            uri=mesh.get('filename');p=self.resolve_mesh(uri)
            self.meshes[uri]=p;self.hashes['mesh:'+uri]=digest(p)
        self.model_id=fingerprint({'profile':self.profile,'assets':self.hashes})
        self.mass=0.
        for name,link in self.links.items():
            inertial=link.find('inertial')
            if inertial is None:continue
            mass=float(inertial.find('mass').get('value'));v=inertial.find('inertia')
            I=np.array([[float(v.get('ixx')),float(v.get('ixy')),float(v.get('ixz'))],
                        [float(v.get('ixy')),float(v.get('iyy')),float(v.get('iyz'))],
                        [float(v.get('ixz')),float(v.get('iyz')),float(v.get('izz'))]])
            eigen=np.linalg.eigvalsh(I)
            if mass<=0 or eigen.min()<=0 or eigen[-1]>eigen[:2].sum()+1e-10:raise ValueError('Invalid physical inertia: '+name)
            self.mass+=mass
        if with_physics:self._build_mujoco()

    def resolve_mesh(self,uri):
        if uri.startswith('package://'):
            package,relative=uri[len('package://'):].split('/',1)
            root=self.profile.get('package_roots',{}).get(package)
            if root is None:raise ValueError('Add package_roots mapping for '+package)
            base=Path(root);base=base if base.is_absolute() else ROOT/base
            path=base/relative
        elif '://' in uri:raise ValueError('Only local mesh assets are supported')
        else:path=self.urdf.parent/uri
        path=path.resolve()
        if not path.is_file():raise FileNotFoundError(path)
        return path

    def _build_mujoco(self):
        import mujoco
        xml=ET.Element('mujoco',model='gom_profile_bound')
        ET.SubElement(xml,'compiler',angle='radian',fusestatic='true',inertiafromgeom='false')
        physics=self.profile['physics'];dt=float(physics['dt'])
        if not 0<dt<=.01 or not 0<physics['stall_fraction']<=1 or not 0<physics['friction']<=2:raise ValueError('Invalid physics bounds')
        ET.SubElement(xml,'option',timestep=str(dt),gravity='0 0 -9.81',iterations='80',cone='elliptic')
        defaults=ET.SubElement(xml,'default')
        ET.SubElement(defaults,'geom',friction=f'{physics["friction"]} .005 .0001',condim='3',solref='.005 1')
        assets=ET.SubElement(xml,'asset');buffers={};world=ET.SubElement(xml,'worldbody')
        ET.SubElement(world,'geom',name='floor',type='plane',size='5 5 .1',rgba='.85 .88 .9 1')
        children={n:[] for n in self.links}
        for joint in self.tree:children[joint.find('parent').get('link')].append(joint)
        def body(parent,name,joint=None):
            item=ET.SubElement(parent,'body',name=name,**pose(origin(joint) if joint is not None else np.eye(4)))
            if joint is None:ET.SubElement(item,'freejoint',name='floating_base')
            elif joint.get('type')!='fixed':
                n=joint.get('name');i=self.names.index(n);axis=joint.find('axis')
                ET.SubElement(item,'joint',name=n,type='slide' if joint.get('type')=='prismatic' else 'hinge',
                    axis=axis.get('xyz','1 0 0') if axis is not None else '1 0 0',limited='false' if joint.get('type')=='continuous' else 'true',
                    range=numbers([self.urdf_lower[i],self.urdf_upper[i]]),damping='.001',armature='.00001')
            link=self.links[name];inertial=link.find('inertial')
            if inertial is not None:
                v=inertial.find('inertia');p=origin(inertial)
                I=np.array([[float(v.get('ixx')),float(v.get('ixy')),float(v.get('ixz'))],
                            [float(v.get('ixy')),float(v.get('iyy')),float(v.get('iyz'))],
                            [float(v.get('ixz')),float(v.get('iyz')),float(v.get('izz'))]])
                I=p[:3,:3]@I@p[:3,:3].T
                ET.SubElement(item,'inertial',mass=inertial.find('mass').get('value'),pos=numbers(p[:3,3]),fullinertia=numbers([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
            for index,c in enumerate(link.findall('collision')):
                attrs=dict(name=f'{name}__collision_{index}',rgba='.35 .55 .65 1',**pose(origin(c)))
                g=c.find('geometry')
                if g.find('box') is not None:attrs.update(type='box',size=numbers(np.fromstring(g.find('box').get('size'),sep=' ')/2))
                elif g.find('sphere') is not None:attrs.update(type='sphere',size=g.find('sphere').get('radius'))
                elif g.find('cylinder') is not None:
                    s=g.find('cylinder');attrs.update(type='cylinder',size=f'{s.get("radius")} {float(s.get("length"))/2}')
                elif g.find('mesh') is not None:
                    mesh=g.find('mesh');p=self.meshes[mesh.get('filename')];key=f'mesh_{len(buffers)}{p.suffix}'
                    buffers[key]=p.read_bytes();mn=f'collision_mesh_{len(buffers)}'
                    ET.SubElement(assets,'mesh',name=mn,file=key,scale=mesh.get('scale','1 1 1'));attrs.update(type='mesh',mesh=mn)
                else:raise ValueError('Unsupported collision geometry: '+name)
                ET.SubElement(item,'geom',**attrs)
            ET.SubElement(item,'site',name=name+'__frame',size='.001')
            for j in children[name]:body(item,j.find('child').get('link'),j)
        body(world,self.profile['root_link'])
        actuators=ET.SubElement(xml,'actuator')
        for n in self.names:ET.SubElement(actuators,'motor',name=n,joint=n,gear='1')
        self.xml=ET.tostring(xml,encoding='unicode');self.model=mujoco.MjModel.from_xml_string(self.xml,assets=buffers)
        self.data=mujoco.MjData(self.model)
        self.qi=np.array([self.model.jnt_qposadr[self.model.joint(n).id] for n in self.names])
        self.vi=np.array([self.model.jnt_dofadr[self.model.joint(n).id] for n in self.names])
        self.root_id=self.model.body(self.profile['root_link']).id
        self.foot_ids=[self.model.body(n).id for n in self.feet]
        # Mesh soles use their convex contact hull and require an explicit datum.
        self.foot_points=[]
        for n in self.feet:
            boxes=self.links[n].findall('collision')
            points=[]
            for c in boxes:
                box=c.find('geometry/box')
                if box is not None:
                    p=np.array(list(itertools.product([-1,1],repeat=3)))*np.fromstring(box.get('size'),sep=' ')/2
                elif c.find('geometry/mesh') is not None:
                    mesh=c.find('geometry/mesh')
                    p=mesh_vertices(self.meshes[mesh.get('filename')])*np.fromstring(mesh.get('scale','1 1 1'),sep=' ')
                else:raise ValueError('Foot sole requires box or STL/OBJ mesh collisions and a sole frame')
                T=origin(c);points.extend(p@T[:3,:3].T+T[:3,3])
            if not points:raise ValueError('Foot has no collision geometry: '+n)
            self.foot_points.append(np.asarray(points))
        self.set_state(self.nominal,np.zeros(3),np.array([0.,0.,0.,1.]))
        self.height=-min(p[:,2].min() for p in self.world_feet())
        self.set_state(self.nominal,np.array([0.,0.,self.height]),np.array([0.,0.,0.,1.]))
        self.sole_local=[];self.sole_rotations=[]
        for i,b in enumerate(self.foot_ids):
            boxes=self.links[self.feet[i]].findall('collision')
            explicit=self.profile.get('sole_frames',{}).get(self.feet[i])
            if explicit:
                self.sole_local.append(np.asarray(explicit['xyz'],dtype=float))
                local_R=Rotation.from_euler('xyz',explicit.get('rpy',[0,0,0])).as_matrix()
                R=self.data.xmat[b].reshape(3,3)@local_R
                self.sole_rotations.append(Rotation.from_euler('z',np.arctan2(R[1,0],R[0,0])).as_matrix()@local_R.T)
                continue
            chosen=self.profile.get('sole_collisions',{}).get(self.feet[i])
            if chosen is None and len(boxes)!=1:raise ValueError('Multiple foot colliders: select sole_collisions explicitly')
            collision=next((c for c in boxes if chosen is None or c.get('name')==chosen),None)
            if collision is None:raise ValueError('Selected sole collider not found')
            if collision.find('geometry/box') is None:raise ValueError('Mesh soles require an explicit sole_frames xyz/rpy entry; do not guess a contact datum')
            T=origin(collision);half=np.fromstring(collision.find('geometry/box').get('size'),sep=' ')/2
            self.sole_local.append(T[:3,3]-T[:3,2]*half[2])
            R=self.data.xmat[b].reshape(3,3)@T[:3,:3]
            yaw=np.arctan2(R[1,0],R[0,0])
            self.sole_rotations.append(Rotation.from_euler('z',yaw).as_matrix()@T[:3,:3].T)

    def set_state(self,q,root_pos,root_quat):
        import mujoco
        d=self.data;d.qpos[:3]=root_pos;d.qpos[3:7]=np.asarray(root_quat)[[3,0,1,2]];d.qpos[self.qi]=q;d.qvel[:]=0
        mujoco.mj_forward(self.model,d)

    def world_feet(self):
        return [p@self.data.xmat[b].reshape(3,3).T+self.data.xpos[b] for p,b in zip(self.foot_points,self.foot_ids)]

    def sole_positions(self):
        return np.array([self.data.xmat[b].reshape(3,3)@p+self.data.xpos[b] for p,b in zip(self.sole_local,self.foot_ids)])

    def audit(self):
        return {'schema':'gom_model_audit_v1','model_id':self.model_id,'profile':self.profile,'asset_hashes':self.hashes,
                'mass_kg':self.mass,'mujoco_mass_kg':float(self.model.body_mass.sum()),'joints':self.names,
                'nominal_root_height_m':self.height,'hardware_ready':False}
