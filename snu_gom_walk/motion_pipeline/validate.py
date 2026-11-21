"""Full-frame collision, floor, FK and velocity checks bound to asset contents."""
import numpy as np
from scipy.spatial.transform import Rotation

from .model import digest,write_json


def validate_arrays(robot,a):
    checks={};g=robot.profile['gates'];n=len(a['time'])
    required={'joints_pos':(n,len(robot.names)),'joints_vel':(n,len(robot.names)),'root_pos':(n,3),'root_quat':(n,4),
              'planned_contacts':(n,2),'foot_positions_world':(n,2,3),'com_world':(n,3)}
    if n<3 or any(a[k].shape!=shape for k,shape in required.items()):raise ValueError('Malformed reference shapes')
    if not all(np.isfinite(v).all() for v in a.values() if np.issubdtype(v.dtype,np.number)):raise ValueError('Nonfinite reference rejected before physics')
    checks['model_matches']=str(a['model_id'])==robot.model_id
    checks['joint_names_match']=a['joint_names'].tolist()==robot.names
    checks['finite']=all(np.isfinite(v).all() for v in a.values() if np.issubdtype(v.dtype,np.number))
    checks['uniform_time']=n>=3 and bool(np.allclose(np.diff(a['time']),1/float(a['fps']),atol=1e-8))
    checks['unit_quaternions']=bool(np.allclose(np.linalg.norm(a['root_quat'],axis=1),1,atol=1e-6))
    q=a['joints_pos'];v=a['joints_vel']
    checks['joint_positions']=bool(((q>=robot.lower-1e-6)&(q<=robot.upper+1e-6)).all())
    checks['joint_velocities']=bool((abs(v)<=robot.speed+1e-6).all())
    computed=np.gradient(q,1/float(a['fps']),axis=0,edge_order=2)
    checks['stored_velocity_consistent']=bool(np.max(abs(computed-v))<1e-6)
    hits={};allowed={frozenset(p['links']):p['max_penetration_m'] for p in robot.profile.get('allowed_collision_pairs',[])}
    fk_error=0.;floor=1.;gap=0.;sole=[];com_error=0.;min_margin=1.;preview=[]
    for i in range(n):
        robot.set_state(q[i],a['root_pos'][i],a['root_quat'][i]);d=robot.data;m=robot.model
        feet=robot.world_feet();heights=np.array([p[:,2].min() for p in feet]);sole.append(heights.tolist())
        floor=min(floor,float(heights.min()))
        if np.any(a['planned_contacts'][i]):gap=max(gap,float(abs(heights[a['planned_contacts'][i].astype(bool)]).max()))
        fk_error=max(fk_error,float(abs(robot.sole_positions()-a['foot_positions_world'][i]).max()))
        com_error=max(com_error,float(abs(d.subtree_com[robot.root_id]-a['com_world'][i]).max()))
        for c in d.contact:
            if 0 in c.geom:
                other=int(c.geom[1] if c.geom[0]==0 else c.geom[0]);body=int(m.geom_bodyid[other])
                if body not in robot.foot_ids and c.dist < -g['floor_tolerance_m']:
                    hits[m.body(body).name+' / floor']=max(hits.get(m.body(body).name+' / floor',0.),float(-c.dist))
                continue
            if c.dist>=-g['collision_tolerance_m']:continue
            names=tuple(m.body(int(m.geom_bodyid[int(k)])).name for k in c.geom)
            if names[0]==names[1]:continue
            if -c.dist<=allowed.get(frozenset(names),0):continue
            key=' / '.join(sorted(names));hits[key]=max(hits.get(key,0.),float(-c.dist))
        support=np.concatenate([feet[s] for s in range(2) if a['planned_contacts'][i,s]],axis=0)
        center=d.subtree_com[robot.root_id]
        margin=min(float((center[:2]-support[:,:2].min(0)).min()),float((support[:,:2].max(0)-center[:2]).min()))
        min_margin=min(min_margin,margin)
        boxes=[]
        for geom in range(1,m.ngeom):
            # Exact box colliders; mesh/sphere/cylinder are represented by their
            # oriented bounding box for review only, never for the contact solver.
            size=m.geom_size[geom].copy()
            if int(m.geom_type[geom])!=6:size[:]=m.geom_rbound[geom]/np.sqrt(3)
            boxes.append([*d.geom_xpos[geom].tolist(),*d.geom_xmat[geom].tolist(),*size.tolist()])
        preview.append(boxes)
    foot_error=float(abs(a['target_foot_positions_world']-a['foot_positions_world']).max())
    # LIPM only plans XY. Actual vertical CoM is free to change with the authored pelvis.
    target_com_error=float(abs(a['target_com_world'][:,:2]-a['com_world'][:,:2]).max())
    checks.update(foot_targets=foot_error<=g['foot_error_m'],com_targets_xy=target_com_error<=g['com_error_m'],
                  exported_fk=fk_error<1e-6 and com_error<1e-6,floor_clearance=floor>=-g['floor_tolerance_m'],
                  support_floor_gap=gap<=g['support_gap_m'],critical_collisions=not hits)
    rpy=Rotation.from_quat(a['root_quat']).as_euler('xyz')
    tilt=np.rad2deg(np.arccos(np.clip(Rotation.from_quat(a['root_quat']).as_matrix()[:,2,2],-1,1)))
    checks['torso_tilt']=bool(tilt.max()<=g['max_tilt_deg'])
    report={'schema':'gom_kinematic_validation_v1','model_id':robot.model_id,'passed':all(checks.values()),'checks':checks,
            'frames_checked':n,'geometry_frame_stride':1,'collision_max_penetration_m':hits,'floor_min_m':floor,'support_gap_max_m':gap,
            'foot_error_max_m':foot_error,'com_xy_error_max_m':target_com_error,'fk_error_max_m':fk_error,
            'torso_peak_to_peak_deg':np.rad2deg(np.ptp(rpy,axis=0)).tolist(),
            'joint_peak_speed_rad_s':dict(zip(robot.names,abs(v).max(0).tolist())),
            'joint_acceleration_rms_rad_s2':dict(zip(robot.names,np.sqrt((np.gradient(v,1/float(a['fps']),axis=0)**2).mean(0)).tolist())),
            'support_aabb_margin_min_m':min_margin,'support_margin_is_dynamic_certificate':False,
            'dynamics_verified':False,'hardware_ready':False,
            'limits':'Discrete full-frame collision inspection; not swept-volume, torque or dynamic balance certification.'}
    return report,dict(time=a['time'].tolist(),root=a['root_pos'].tolist(),boxes=preview,sole_heights=sole,
                       contacts=a['planned_contacts'].tolist(),joints=q.tolist(),joint_names=robot.names)


def validate_file(robot,path):
    with np.load(path,allow_pickle=False) as raw:a={k:raw[k] for k in raw.files}
    report,preview=validate_arrays(robot,a);report['clip_sha256']=digest(path)
    write_json(path.with_suffix('.validation.json'),report)
    return report,preview
