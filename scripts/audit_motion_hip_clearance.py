"""Optional full-frame CAD surface check of hip-yaw housing/thigh plate pairs.

Uses requirements-collision-audit.txt. Visual surface intersections are reported
separately from the contact forces in diagnose_hip_torque.py. No geometry edits.
"""
import argparse
import os
from pathlib import Path
import sys

for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ.setdefault(name,'1')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import json
import numpy as np
import trimesh
from snu_gom_walk.motion_pipeline.model import RobotModel,origin,digest,write_json


def check_run(run):
    manifest=json.loads((run/'manifest.json').read_text());r=RobotModel(manifest['profile'])
    if r.model_id!=manifest['model_id'] or r.hashes!=manifest['asset_hashes']:raise ValueError('Asset/profile mismatch')
    managers={};object_names={}
    for side in ['left','right']:
        for suffix in ['hip_yaw_link','thigh_link']:
            name=side+'_'+suffix;manager=trimesh.collision.CollisionManager();names=[]
            for i,visual in enumerate(r.links[name].findall('visual')):
                mesh=visual.find('geometry/mesh')
                if mesh is None:raise ValueError('This CAD audit expects mesh visuals')
                p=r.resolve_mesh(mesh.get('filename'));obj=trimesh.load_mesh(p)
                obj.apply_scale(np.fromstring(mesh.get('scale','1 1 1'),sep=' '));obj.apply_transform(origin(visual))
                key=f'{name}/{i}/{p.name}';manager.add_object(key,obj);names.append(key)
            managers[name]=manager;object_names[name]=names
    clips=[]
    for entry in manifest['clips']:
        if entry['kind']!='walk':continue
        path=run/entry['file']
        if digest(path)!=entry['sha256']:raise ValueError('Clip modified')
        with np.load(path,allow_pickle=False) as a:
            rows=[]
            for i,t in enumerate(a['time']):
                r.set_state(a['joints_pos'][i],a['root_pos'][i],a['root_quat'][i])
                for side in ['left','right']:
                    left=side+'_hip_yaw_link';right=side+'_thigh_link'
                    for name in [left,right]:
                        site=r.model.site(name+'__frame').id;T=np.eye(4)
                        T[:3,:3]=r.data.site_xmat[site].reshape(3,3);T[:3,3]=r.data.site_xpos[site]
                        for key in object_names[name]:managers[name].set_transform(key,T)
                    collision,pairs=managers[left].in_collision_other(managers[right],return_names=True)
                    if collision:distance=0.;nearest=sorted(pairs)[0]
                    else:distance,nearest=managers[left].min_distance_other(managers[right],return_names=True)
                    rows.append(dict(frame=i,time_s=float(t),side=side,intersects=bool(collision),gap_mm=float(distance*1000),nearest_pair=nearest,
                                     hip_roll_deg=float(np.rad2deg(a['joints_pos'][i,r.names.index(side+'_hip_roll_joint')]))))
        clips.append(dict(id=entry['id'],sha256=entry['sha256'],sampled_frames=len(rows)//2,
                          intersecting_side_frames=sum(x['intersects'] for x in rows),
                          minimum_gap_mm=min(x['gap_mm'] for x in rows),worst=min(rows,key=lambda x:x['gap_mm']),rows=rows))
        print(json.dumps({k:v for k,v in clips[-1].items() if k!='rows'}),flush=True)
    return dict(schema='gom_motion_hip_cad_audit_v1',model_id=r.model_id,script_sha256=digest(__file__),clips=clips,
                scope='Discrete visual-surface checks of hip-yaw/thigh assemblies only. Not other pairs, continuous sweep, forces or strength.',
                geometry_modified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();write_json(args.output,check_run(args.run.resolve()))


if __name__=='__main__':main()
