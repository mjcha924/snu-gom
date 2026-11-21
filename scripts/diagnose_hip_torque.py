"""Isolate simulated self-collision from ground-reaction and motor-cap effects.

Diagnostic counterfactuals only; none of these runs certify hardware or become
training references. Run before changing a baseline generator/controller.
"""
import argparse
import copy
import os
from pathlib import Path
import sys

for name in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']:os.environ.setdefault(name,'1')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import json
import numpy as np
import mujoco

from snu_gom_walk.motion_pipeline.model import RobotModel,write_json,digest
from snu_gom_walk.motion_pipeline.physics import ContactController,sample


def contact_terms(robot,data):
    """Sum contact forces in generalized coordinates and verify the convention."""
    m=robot.model;nv=m.nv;floor=np.zeros(nv);vertical=floor.copy();self_force=floor.copy()
    loads=np.zeros(2);weighted=np.zeros((2,3));self_count=0;self_peak=0.
    for i,c in enumerate(data.contact):
        force=np.zeros(6);mujoco.mj_contactForce(m,data,i,force)
        f=c.frame.reshape(3,3).T@force[:3];moment=c.frame.reshape(3,3).T@force[3:]
        b0,b1=[int(m.geom_bodyid[int(g)]) for g in c.geom]
        J0=np.zeros((3,nv));W0=J0.copy();J1=J0.copy();W1=J0.copy()
        mujoco.mj_jac(m,data,J0,W0,c.pos,b0);mujoco.mj_jac(m,data,J1,W1,c.pos,b1)
        generalized=(J1-J0).T@f+(W1-W0).T@moment
        if 0 in c.geom:
            floor+=generalized;vertical+=(J1-J0).T@np.array([0.,0.,f[2]])
            for side,body in enumerate(robot.foot_ids):
                on_foot=f if b1==body else -f if b0==body else np.zeros(3)
                loads[side]+=on_foot[2];weighted[side]+=on_foot[2]*c.pos
        else:
            self_force+=generalized
            if np.linalg.norm(force)>1e-6:self_count+=1;self_peak=max(self_peak,float(np.linalg.norm(force[:3])))
    return dict(floor=floor,vertical=vertical,self_force=self_force,loads=loads,
                cop=weighted/np.maximum(loads[:,None],1e-9),self_count=self_count,self_peak=self_peak,
                constraint_residual=float(abs(floor+self_force-data.qfrc_constraint).max()))


def run_case(profile,arrays,case):
    r=RobotModel(profile);m=r.model;d=mujoco.MjData(m)
    if case=='no_self':
        # Floor-robot collisions remain enabled; only robot-robot pairs are disabled.
        m.geom_contype[0]=1;m.geom_conaffinity[0]=2;m.geom_contype[1:]=2;m.geom_conaffinity[1:]=1
    if case=='roomier_motor_only':
        r.profile['physics']['stall_fraction']=.6
        motors=r.profile['motors'];r.effort=np.array([motors.get('overrides',{}).get(n,motors['default'])['stall_nm']*.6 for n in r.names])
    ctrl=ContactController(r);grav=mujoco.MjData(m);warmup=float(r.profile['physics']['warmup_s']);dt=m.opt.timestep
    d.qpos[:3]=arrays['root_pos'][0];d.qpos[3:7]=arrays['root_quat'][0][[3,0,1,2]];d.qpos[r.qi]=arrays['joints_pos'][0]
    mujoco.mj_forward(m,d);rows=[];failed=None
    stride=round(1/float(arrays['fps'])/dt)
    for step in range(round((warmup+float(arrays['time'][-1]))/dt)+1):
        t=step*dt;target=sample(arrays,max(0.,t-warmup))
        if t<warmup:target['joints_vel'][:]=0;target['world_angular_vel'][:]=0
        u,cap=ctrl.step(d,target);d.ctrl[:]=u;mujoco.mj_step(m,d);mujoco.mj_forward(m,d)
        tilt=float(np.degrees(np.arccos(np.clip(d.xmat[r.root_id].reshape(3,3)[2,2],-1,1))))
        if t>=warmup and step%stride==0:
            terms=contact_terms(r,d);M=np.zeros((m.nv,m.nv));mujoco.mj_fullM(m,M,d.qM)
            grav.qpos[:]=d.qpos;grav.qvel[:]=0;mujoco.mj_forward(m,grav)
            hips={}
            for side in ['left','right']:
                for axis in ['roll','pitch']:
                    name=f'{side}_hip_{axis}_joint';j=r.names.index(name);joint=m.joint(name).id;v=r.vi[j]
                    hips[name]=dict(torque_nm=float(u[j]),cap_nm=float(cap[j]),floor_contact_nm=float(terms['floor'][v]),
                        vertical_contact_nm=float(terms['vertical'][v]),horizontal_contact_nm=float((terms['floor']-terms['vertical'])[v]),
                        self_contact_nm=float(terms['self_force'][v]),gravity_nm=float(grav.qfrc_bias[v]),
                        inertial_nm=float((M@d.qacc)[v]),velocity_bias_nm=float(d.qfrc_bias[v]-grav.qfrc_bias[v]),
                        axis_world=d.xaxis[joint].tolist(),anchor_world_m=d.xanchor[joint].tolist())
            rows.append(dict(time_s=t-warmup,root_pos=d.xpos[r.root_id].tolist(),tilt_deg=tilt,hips=hips,
                             foot_loads_n=terms['loads'].tolist(),cop_world=terms['cop'].tolist(),
                             active_self_contacts=terms['self_count'],max_self_contact_force_n=terms['self_peak'],
                             contact_force_reconstruction_residual=terms['constraint_residual'],
                             joints_pos=d.qpos[r.qi].tolist(),torques_nm=u.tolist()))
        if tilt>45 or d.xpos[r.root_id,2]<.65*r.height:
            failed=t-warmup;break
    summary=dict(case=case,fell_at_motion_s=failed,frames=len(rows),active_self_contact_samples=sum(x['active_self_contacts'] for x in rows),
                 max_self_contact_force_n=max((x['max_self_contact_force_n'] for x in rows),default=0),
                 max_contact_force_reconstruction_residual=max((x['contact_force_reconstruction_residual'] for x in rows),default=0),hips={})
    for name in rows[0]['hips'] if rows else []:
        v=[x['hips'][name] for x in rows];torque=np.array([x['torque_nm'] for x in v]);cap=np.array([x['cap_nm'] for x in v])
        summary['hips'][name]=dict(saturation_fraction=float((abs(torque)>=.99*cap).mean()),
             peak_applied_nm=float(abs(torque).max()),rms_applied_nm=float(np.sqrt((torque**2).mean())),
             **{k+'_rms':float(np.sqrt(np.mean([x[k]**2 for x in v]))) for k in
                ['floor_contact_nm','vertical_contact_nm','horizontal_contact_nm','self_contact_nm','gravity_nm','inertial_nm']})
    return summary,rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--clip',default='walk_001_a0')
    p.add_argument('--output',type=Path,default=ROOT/'reports/hip-torque-audit');args=p.parse_args()
    manifest=json.loads((args.run/'manifest.json').read_text());path=args.run/(args.clip+'.npz')
    with np.load(path,allow_pickle=False) as raw:a={k:raw[k].copy() for k in raw.files}
    results={};traces={};args.output.mkdir(parents=True,exist_ok=True)
    for case in ['baseline','no_self','roomier_motor_only']:
        results[case],traces[case]=run_case(copy.deepcopy(manifest['profile']),a,case)
        write_json(args.output/(case+'.json'),dict(summary=results[case],frames=traces[case]))
        print(json.dumps(results[case],indent=2),flush=True)
    common=min(len(traces['baseline']),len(traces['no_self']))
    difference=max((float(abs(np.array(traces['baseline'][i]['torques_nm'])-np.array(traces['no_self'][i]['torques_nm'])).max()) for i in range(common)),default=0.)
    report=dict(schema='gom_hip_torque_causal_audit_v1',reference_sha256=digest(path),purpose='counterfactual diagnosis, not training certification',
                cases=results,no_self_vs_baseline_max_torque_difference_nm=difference)
    write_json(args.output/'summary.json',report)


if __name__=='__main__':main()
