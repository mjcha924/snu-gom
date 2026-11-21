"""Shared reference-planning envelope, distinct from a continuous motor rating."""
import numpy as np


def motor_rows(profile,names):
    motors=profile['motors']
    return [dict(motors['default'],**motors.get('overrides',{}).get(n,{})) for n in names]


def limits(profile,names,urdf_effort,urdf_speed):
    rows=motor_rows(profile,names);settings=profile['motors']
    stall=np.array([r['stall_nm'] for r in rows]);no_load=np.array([r['no_load_rad_s'] for r in rows])
    fraction=float(settings.get('planning_stall_fraction',profile['physics']['stall_fraction']))
    speed_fraction=float(settings.get('planning_speed_fraction',1.))
    if not (0<fraction<=1 and 0<speed_fraction<1.01) or not np.isfinite([stall,no_load]).all() or min(stall.min(),no_load.min())<=0:
        raise ValueError('Invalid motor planning envelope')
    effort=stall*fraction;speed=no_load*speed_fraction
    if not settings.get('override_provisional_urdf_effort_velocity',False):
        effort=np.minimum(effort,urdf_effort);speed=np.minimum(speed,urdf_speed)
    return effort,speed


def torque_envelope(profile,names,velocity,effort):
    """Symmetric motoring bound; conservative for regenerative/braking quadrants.

    XC curve is manually read from ROBOTIS's graph, not measured on this robot.
    Outside the published loaded samples, hold the last torque rather than
    extrapolating a stall intercept. This is still not a thermal model.
    """
    rows=motor_rows(profile,names);v=np.abs(np.asarray(velocity));caps=[]
    for i,row in enumerate(rows):
        bound=row['stall_nm']*max(0.,1-v[i]/row['no_load_rad_s'])
        if 'curve_speed_rpm' in row:
            speeds=np.array(row['curve_speed_rpm'])*2*np.pi/60;torques=np.array(row['curve_torque_nm'])
            if len(speeds)!=len(torques) or len(speeds)<2 or not (np.diff(speeds)>0).all() or not (np.diff(torques)<=0).all():
                raise ValueError('Motor curve must have increasing speeds and decreasing torques')
            bound=min(bound,float(np.interp(v[i],speeds,torques,left=torques[0],right=0.)))
        caps.append(min(float(effort[i]),bound))
    return np.array(caps)


def torch_curve_cap(velocity,speeds,torques):
    """Vectorized piecewise interpolation shared by CPU tests and Isaac runtime."""
    import torch
    v=velocity.abs();x=speeds.expand(*v.shape,speeds.shape[-1]);y=torques.expand_as(x)
    index=((v[...,None]>=x).sum(-1)-1).clamp(0,x.shape[-1]-2)[...,None]
    lo=x.gather(-1,index).squeeze(-1);hi=x.gather(-1,index+1).squeeze(-1)
    yl=y.gather(-1,index).squeeze(-1);yh=y.gather(-1,index+1).squeeze(-1)
    return torch.lerp(yl,yh,((v-lo)/(hi-lo)).clamp(0,1)).clamp_min(0)


def curve_arrays(profile,names):
    rows=motor_rows(profile,names);curves=[]
    for row in rows:
        curves.append((list(np.array(row.get('curve_speed_rpm',[0,row['no_load_rad_s']*30/np.pi]))*np.pi/30),
                       row.get('curve_torque_nm',[row['stall_nm'],0.])))
    width=max(len(x) for x,y in curves)
    return (np.array([x+[x[-1]+i+1 for i in range(width-len(x))] for x,y in curves]),
            np.array([y+[0.]*(width-len(y)) for x,y in curves]))
