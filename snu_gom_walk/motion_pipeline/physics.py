"""Local free-base rollout with contact-consistent bounded joint torques.

Uses MuJoCo's own inverse/forward soft-contact law, not guessed contact forces.
No base tracking force, root teleportation, or GPU training is used.
"""
import numpy as np
from scipy.optimize import lsq_linear
from scipy.spatial.transform import Rotation,Slerp


def sample(a,time):
    t=float(np.clip(time,a['time'][0],a['time'][-1]));i=min(int(np.searchsorted(a['time'],t,side='right')-1),len(a['time'])-2);i=max(i,0)
    u=(t-a['time'][i])/(a['time'][i+1]-a['time'][i]);result={}
    for k in ['joints_pos','joints_vel','root_pos','world_linear_vel','world_angular_vel','com_world','foot_positions_world']:
        result[k]=a[k][i]*(1-u)+a[k][i+1]*u
    result['root_quat']=Slerp([0,1],Rotation.from_quat(a['root_quat'][i:i+2]))([u]).as_quat()[0]
    result['planned_contacts']=a['planned_contacts'][i]
    return result


class ContactController:
    def __init__(self,robot):
        import mujoco
        self.r=robot;self.m=robot.model;self.probe=mujoco.MjData(self.m);self.inverse=mujoco.MjData(self.m)
        self.u=np.zeros(len(robot.names));self.S=np.eye(self.m.nv)[:,robot.vi]
        motors=robot.profile['motors'];rows=[motors.get('overrides',{}).get(n,motors['default']) for n in robot.names]
        self.stall=np.array([v['stall_nm'] for v in rows]);self.speed=np.array([v['no_load_rad_s'] for v in rows]);self.max_error=0.

    def forward(self,d,u):
        import mujoco
        p=self.probe;p.qpos[:]=d.qpos;p.qvel[:]=d.qvel;p.ctrl[:]=u;p.qfrc_applied[:]=0;p.xfrc_applied[:]=0
        mujoco.mj_forward(self.m,p);return p.qacc.copy()

    def inverse_gradient(self,d,a):
        import mujoco
        p=self.inverse;p.qpos[:]=d.qpos;p.qvel[:]=d.qvel;p.qacc[:]=a
        mujoco.mj_inverse(self.m,p);F=np.empty((self.m.nv,self.m.nv))
        # mjd_inverseFD returns transposed derivatives.
        mujoco.mjd_inverseFD(self.m,p,1e-6,0,None,None,F,None,None,None,None)
        return p.qfrc_inverse.copy(),F.T

    def step(self,d,target):
        import mujoco
        r=self.r;m=self.m;nv=m.nv;settings=r.profile['physics'];Jq=np.eye(nv)[r.vi]
        C=[Jq];b=[settings['kp']*(target['joints_pos']-d.qpos[r.qi])+settings['kd']*(target['joints_vel']-d.qvel[r.vi])]
        J=np.zeros((3,nv));mujoco.mj_jacSubtreeCom(m,d,J,r.root_id)
        C.append(np.sqrt(30)*J);b.append(np.sqrt(30)*(60*(target['com_world']-d.subtree_com[r.root_id])-12*(J@d.qvel)))
        J=np.zeros((3,nv));W=J.copy();mujoco.mj_jacBody(m,d,J,W,r.root_id)
        error=(Rotation.from_quat(target['root_quat'])*Rotation.from_matrix(d.xmat[r.root_id].reshape(3,3)).inv()).as_rotvec()
        C.append(np.sqrt(3)*W);b.append(np.sqrt(3)*(50*error+12*(target['world_angular_vel']-W@d.qvel)))
        for s,body in enumerate(r.foot_ids):
            point=d.xmat[body].reshape(3,3)@r.sole_local[s]+d.xpos[body];J=np.zeros((3,nv));mujoco.mj_jac(m,d,J,None,point,body)
            weight=100 if target['planned_contacts'][s] else 20
            desired=150*(target['foot_positions_world'][s]-point)-20*(J@d.qvel)
            C.append(np.sqrt(weight)*J);b.append(np.sqrt(weight)*desired)
        C=np.concatenate(C);b=np.concatenate(b)
        cap=np.minimum(r.effort,np.minimum(self.stall*settings['stall_fraction'],self.stall*np.maximum(0,1-abs(d.qvel[r.vi])/self.speed)))
        safe=np.maximum(cap,1e-9);u=np.clip(self.u,-cap,cap);a=self.forward(d,u)
        def cost(acc,effort):return np.sum((C@acc-b)**2)+.01*np.sum((effort/safe)**2)
        value=cost(a,u)
        for _ in range(3):
            _,F=self.inverse_gradient(d,a);G=np.linalg.solve(F,self.S)*safe[None,:]
            offset=a-G@(u/safe)
            A=np.r_[C@G,np.eye(len(u))*.1];y=np.r_[b-C@offset,np.zeros(len(u))]
            solution=lsq_linear(A,y,bounds=(-1,1),tol=1e-6,max_iter=40)
            proposed=np.clip(solution.x*safe,-cap,cap);improved=False
            for alpha in [1.,.5,.25]:
                candidate=u+alpha*(proposed-u);predicted=self.forward(d,candidate);trial=cost(predicted,candidate)
                if np.isfinite(trial) and trial<value-1e-7:u=candidate;a=predicted;value=trial;improved=True;break
            if not improved:break
        required,_=self.inverse_gradient(d,a);self.max_error=max(self.max_error,float(abs(required-self.S@u).max()));self.u=u
        return u,cap


def rollout(robot,a,seconds=None):
    import mujoco
    m=robot.model;d=mujoco.MjData(m);controller=ContactController(robot);warmup=robot.profile['physics']['warmup_s']
    duration=float(a['time'][-1]) if seconds is None else min(float(seconds),float(a['time'][-1]))
    if duration<=0:raise ValueError('Positive rollout duration required')
    d.qpos[:3]=a['root_pos'][0];d.qpos[3:7]=a['root_quat'][0][[3,0,1,2]];d.qpos[robot.qi]=a['joints_pos'][0]
    mujoco.mj_forward(m,d);trace=[];failure=None;all_tau=[];all_caps=[];errors=[]
    dt=m.opt.timestep;record_stride=max(1,round(1/float(a['fps'])/dt));q_within=True;speed_within=True;critical={};max_tilt=0.
    for step in range(round((warmup+duration)/dt)+1):
        time=step*dt;ref=sample(a,max(0,time-warmup))
        if time<warmup:
            ref['joints_vel']=np.zeros(len(robot.names));ref['world_angular_vel']=np.zeros(3)
        u,cap=controller.step(d,ref);d.ctrl[:]=u;mujoco.mj_step(m,d);mujoco.mj_forward(m,d)
        all_tau.append(u.copy());all_caps.append(cap.copy())
        q_within &= bool(((d.qpos[robot.qi]>=robot.urdf_lower-1e-4)&(d.qpos[robot.qi]<=robot.urdf_upper+1e-4)).all())
        speed_within &= bool((abs(d.qvel[robot.vi])<=robot.speed+1e-4).all())
        allowed={frozenset(p['links']):p['max_penetration_m'] for p in robot.profile.get('allowed_collision_pairs',[])}
        for c in d.contact:
            if 0 in c.geom:
                other=int(c.geom[1] if c.geom[0]==0 else c.geom[0]);body=int(m.geom_bodyid[other])
                if body not in robot.foot_ids and c.dist < -robot.profile['gates']['floor_tolerance_m']:
                    critical[m.body(body).name+' / floor']=float(-c.dist)
                continue
            if c.dist>=-robot.profile['gates']['collision_tolerance_m']:continue
            names=tuple(m.body(int(m.geom_bodyid[int(k)])).name for k in c.geom)
            if names[0]!=names[1] and -c.dist>allowed.get(frozenset(names),0):critical[' / '.join(sorted(names))]=float(-c.dist)
        tilt=float(np.rad2deg(np.arccos(np.clip(d.xmat[robot.root_id].reshape(3,3)[2,2],-1,1))))
        max_tilt=max(max_tilt,tilt)
        if not np.isfinite(d.qpos).all() or tilt>45 or d.xpos[robot.root_id,2]<.65*robot.height:
            failure={'time_s':float(time),'during_warmup':time<warmup,'reason':'fell / invalid state'}
        if time>=warmup and step%record_stride==0:
            robot.data=d;points=robot.world_feet();heights=[float(p[:,2].min()) for p in points];contacts=[False,False]
            for c in d.contact:
                if 0 not in c.geom or c.dist>.0005:continue
                geom=int(c.geom[1] if c.geom[0]==0 else c.geom[0]);body=int(m.geom_bodyid[geom])
                for s,bid in enumerate(robot.foot_ids):
                    if body==bid:contacts[s]=True
            error=d.qpos[robot.qi]-ref['joints_pos'];errors.append(error)
            boxes=[]
            for g in range(1,m.ngeom):
                size=m.geom_size[g].copy()
                if int(m.geom_type[g])!=6:size[:]=m.geom_rbound[g]/np.sqrt(3)
                boxes.append([*d.geom_xpos[g].tolist(),*d.geom_xmat[g].tolist(),*size.tolist()])
            trace.append(dict(time_s=float(time-warmup),root_pos=d.xpos[robot.root_id].tolist(),tilt_deg=tilt,
                 root_quat=Rotation.from_matrix(d.xmat[robot.root_id].reshape(3,3)).as_quat().tolist(),
                 joints_pos=d.qpos[robot.qi].tolist(),joints_vel=d.qvel[robot.vi].tolist(),torque_nm=u.tolist(),
                 contacts=contacts,reference_contacts=ref['planned_contacts'].tolist(),sole_heights=heights,boxes=boxes))
        if failure:break
    tau=np.asarray(all_tau);caps=np.asarray(all_caps);agreement=0.;single=0.;progress=None;qualified=[0,0];alternating=0
    if trace:
        actual=np.array([r['contacts'] for r in trace]);expected=np.array([r['reference_contacts'] for r in trace]);agreement=float((actual==expected).mean());single=float((actual.sum(1)==1).mean())
        intended=sample(a,min(duration,trace[-1]['time_s']))['root_pos'][:2]-a['root_pos'][0,:2]
        achieved=np.array(trace[-1]['root_pos'])[:2]-np.array(trace[0]['root_pos'])[:2]
        if np.linalg.norm(intended)>=.002:progress=float(achieved@intended/(intended@intended))
        air=[0,0];cleared=[False,False];supported=[True,True];last=-1
        for row in trace:
            for s in range(2):
                if not row['contacts'][s]:
                    if air[s]==0:supported[s]=True
                    air[s]+=1;cleared[s]|=row['sole_heights'][s]>.002;supported[s]&=row['contacts'][1-s]
                else:
                    if air[s]/float(a['fps'])>=.06 and cleared[s] and supported[s]:
                        qualified[s]+=1
                        if last>=0 and last!=s:alternating+=1
                        last=s
                    air[s]=0;cleared[s]=False
    wanted_single=float((a['planned_contacts'].sum(1)==1).mean())
    full_duration=duration>=float(a['time'][-1])-1e-6
    checks=dict(survived=failure is None,full_reference_duration=full_duration,contact_match=agreement>=.75,
                single_support=wanted_single<.1 or single>=.5*wanted_single,
                qualified_alternation=wanted_single<.1 or (min(qualified)>=1 and alternating>=1),
                forward_progress=progress is None or .5<=progress<=1.75,
                torque_envelope=bool((abs(tau)<=caps+1e-7).all()),
                actual_joint_positions=q_within,actual_joint_velocities=speed_within,actual_critical_collisions=not critical,
                profile_tilt=max_tilt<=robot.profile['gates']['max_tilt_deg'],
                tracking=bool(errors) and float(np.sqrt(np.mean(np.asarray(errors)**2)))<robot.profile['gates']['tracking_rmse_rad'])
    return dict(schema='gom_physics_validation_v1',backend='MuJoCo '+mujoco.__version__,model_id=robot.model_id,
                passed=all(checks.values()),checks=checks,failure=failure,duration_s=duration,warmup_s=warmup,
                contact_schedule_agreement=agreement,single_support_fraction=single,reference_single_support_fraction=wanted_single,
                qualified_touchdowns=qualified,alternating_touchdowns=alternating,path_progress_ratio=progress,
                joint_tracking_rmse_rad=float(np.sqrt(np.mean(np.asarray(errors)**2))) if errors else None,
                max_inverse_forward_force_error=controller.max_error,
                max_tilt_deg=max_tilt,
                joint_peak_torque_nm=dict(zip(robot.names,abs(tau).max(0).tolist())),
                joint_rms_torque_nm=dict(zip(robot.names,np.sqrt((tau*tau).mean(0)).tolist())),
                critical_collisions=critical,
                base_force_applied=False,root_teleported_after_reset=False,hardware_ready=False,
                limitations=['Rigid provisional contacts/inertias, not measured servos or pads.','A failure does not prove RL cannot learn a stabilizing policy.','Short diagnostics do not qualify a whole clip.']),trace
