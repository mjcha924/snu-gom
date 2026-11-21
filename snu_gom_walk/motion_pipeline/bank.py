"""GPU-ready finite-clip lookup. All hashes and acceptance gates precede loading."""
import numpy as np
import torch

from .library import load_library


def slerp(a,b,u):
    dot=(a*b).sum(-1,keepdim=True);b=torch.where(dot<0,-b,b);dot=dot.abs().clamp(0,1)
    angle=torch.acos(dot.clamp(max=.999999));sine=angle.sin().clamp_min(1e-8)
    q=torch.where(dot>.9995,a+u*(b-a),((1-u)*angle).sin()/sine*a+(u*angle).sin()/sine*b)
    return q/torch.linalg.vector_norm(q,dim=-1,keepdim=True).clamp_min(1e-8)


class MotionBank:
    def __init__(self,path,joint_names,*,device='cpu',kind='walk',split='train',allow_kinematic=False,urdf=None):
        robot,manifest,clips=load_library(path,split=split,kind=kind,allow_kinematic=allow_kinematic,urdf=urdf)
        if len(set(joint_names))!=len(joint_names) or set(joint_names)!=set(robot.names):raise ValueError('Training joint mapping differs from motion profile')
        self.device=torch.device(device);self.entries=[e for e,_ in clips];self.model_id=robot.model_id;self.joint_names=list(joint_names)
        self.fps=torch.tensor([float(a['fps']) for _,a in clips],device=self.device)
        self.duration=torch.tensor([float(a['time'][-1]) for _,a in clips],device=self.device)
        self.lengths=torch.tensor([len(a['time']) for _,a in clips],device=self.device)
        sole=clips[0][1]['sole_points_link']
        if any(not np.allclose(a['sole_points_link'],sole,atol=1e-9) for _,a in clips):raise ValueError('Sole frames differ between clips')
        self.sole_points_link=torch.tensor(sole,dtype=torch.float32,device=self.device)
        fields=['joints_pos','joints_vel','root_pos','root_quat','world_linear_vel','world_angular_vel','foot_positions_body','planned_contacts','phase','sole_heights']
        maximum=int(self.lengths.max());packed={k:[] for k in fields}
        for entry,a in clips:
            order=[a['joint_names'].tolist().index(n) for n in joint_names]
            for k in ['joints_pos','joints_vel']:a[k]=a[k][:,order]
            a['root_quat']=a['root_quat'][:,[3,0,1,2]]
            a['sole_heights']=a['target_sole_height_m'];a['phase']=a['phase'][:,None]
            for k in fields:
                values=a[k];packed[k].append(np.r_[values,np.repeat(values[-1:],maximum-len(values),axis=0)])
        self.data={k:torch.tensor(np.stack(v),dtype=torch.float32,device=self.device) for k,v in packed.items()}

    def sample(self,ids,times):
        ids=torch.as_tensor(ids,device=self.device,dtype=torch.long);times=torch.as_tensor(times,device=self.device,dtype=torch.float32)
        times=times.clamp_min(0).minimum(self.duration[ids]);coordinate=times*self.fps[ids]
        i=coordinate.floor().long().minimum(self.lengths[ids]-2);u=(coordinate-i).clamp(0,1)
        out={}
        for k,v in self.data.items():
            a=v[ids,i];b=v[ids,i+1];fraction=u.reshape(*u.shape,*([1]*(a.ndim-u.ndim)))
            out[k]=a if k=='planned_contacts' else slerp(a,b,fraction) if k=='root_quat' else torch.lerp(a,b,fraction)
        out['phase']=out['phase'][...,0]
        return out


def observation_features(reference,leg_indices,neck_indices):
    """27 extra inputs for the existing 10-action / 12-joint GOM policy."""
    angle=4*torch.pi*reference['phase']
    return torch.cat([reference['joints_pos'][:,leg_indices],reference['joints_vel'][:,leg_indices],
                      reference['planned_contacts'],reference['root_pos'][:,2:3],reference['joints_pos'][:,neck_indices],
                      torch.stack([angle.sin(),angle.cos()],dim=-1)],dim=-1)
