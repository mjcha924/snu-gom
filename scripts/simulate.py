"""CAD pose/replay viewer and experimental PyBullet dynamics. No trained policy."""
from pathlib import Path
import argparse,json,math,time
from restore_meshes import restore
ROOT=Path(__file__).resolve().parents[1]
ROBOT=ROOT/'motion/src/snu_bear_motion/data/robot'
def state_to_pose(state,registry):
 return {'base_xyz_m':[v/1000 for v in state['body_origin']],
         'base_rpy_rad':[0,math.radians(state['body_pitch_deg']),0],
         'joint_positions_rad':{j['name']:(math.radians(state['angles'][j['angle_key']]-j['neutral_angle_deg'])+math.pi)%(2*math.pi)-math.pi for j in registry}}
def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument('--mode',choices=['pose','replay','physics'],default='replay')
 a.add_argument('--pose',choices=['sit','crawl'],default='crawl')
 a.add_argument('--motion',choices=['hold','crawl'],default='hold',help='Physics motor targets only; crawl tracking is unvalidated.')
 a.add_argument('--seconds',type=float,default=15)
 a.add_argument('--headless',action='store_true')
 args=a.parse_args()
 if args.seconds<=0:a.error('--seconds must be positive')
 restore()
 try:import pybullet as p
 except ImportError:raise SystemExit('Install dependencies: python -m pip install -r requirements-sim.txt')
 presets=json.loads((ROBOT/'pose_presets.json').read_text())
 registry=json.loads((ROBOT/'joint_registry.json').read_text())
 states=json.loads((ROBOT/'crawl_states.json').read_text())
 track=[state_to_pose(s,registry) for s in states]
 initial=presets[args.pose] if args.mode=='pose' or (args.mode=='physics' and args.motion=='hold') else track[0]
 p.connect(p.DIRECT if args.headless else p.GUI)
 try:
  dt=1/240;p.setTimeStep(dt);p.setGravity(0,0,-9.81 if args.mode=='physics' else 0)
  plane=p.createCollisionShape(p.GEOM_PLANE);p.createMultiBody(0,plane)
  flags=p.URDF_USE_INERTIA_FROM_FILE|p.URDF_USE_SELF_COLLISION|p.URDF_USE_SELF_COLLISION_EXCLUDE_PARENT
  robot=p.loadURDF(str(ROBOT/'snu_bear_v06.urdf'),initial['base_xyz_m'],p.getQuaternionFromEuler(initial['base_rpy_rad']),useFixedBase=args.mode!='physics',flags=flags)
  joints={p.getJointInfo(robot,i)[1].decode():i for i in range(p.getNumJoints(robot))}
  assert set(joints)==set(initial['joint_positions_rad']) and len(joints)==9
  for name,q in initial['joint_positions_rad'].items():p.resetJointState(robot,joints[name],q)
  inertial=p.getDynamicsInfo(robot,-1);com_xyz,com_quat=inertial[3:5]
  def place(pose):
   # resetBasePositionAndOrientation expects the COM frame, unlike loadURDF's link frame.
   pos,orn=p.multiplyTransforms(pose['base_xyz_m'],p.getQuaternionFromEuler(pose['base_rpy_rad']),com_xyz,com_quat)
   p.resetBasePositionAndOrientation(robot,pos,orn)
   for name,q in pose['joint_positions_rad'].items():p.resetJointState(robot,joints[name],q)
  if not args.headless:
   p.resetDebugVisualizerCamera(.55,45,-20,[.03,0,.10])
   label='PRESCRIBED CAD PLAYBACK — NOT DYNAMICS' if args.mode!='physics' else 'EXPERIMENTAL PHYSICS — UNCALIBRATED MOTORS/COLLISIONS'
   p.addUserDebugText(label,[-.15,0,.3],textSize=1)
  print('9 joints loaded. Physics uses coarse convex mesh collisions; no walking claim.')
  for k in range(round(args.seconds/dt)):
   if not p.isConnected():break
   # One recorded 3 mm cycle, displayed at 80 ms/sample. Hold the final pose afterwards.
   sample=min(int(k*dt/.08),len(track)-1)
   desired=track[sample]
   if args.mode=='replay':place(desired)
   elif args.mode=='pose':place(initial)
   else:
    target=desired if args.motion=='crawl' else initial
    for name,q in target['joint_positions_rad'].items():
     p.setJointMotorControl2(robot,joints[name],p.POSITION_CONTROL,targetPosition=q,force=.2,maxVelocity=1,positionGain=.1,velocityGain=1)
    p.stepSimulation()
    pos,orn=p.getBasePositionAndOrientation(robot)
    values=list(pos)+list(orn)+[v for j in joints.values() for v in p.getJointState(robot,j)[:2]]
    if not all(math.isfinite(v) for v in values):raise RuntimeError('Nonfinite physics state')
   if not args.headless:time.sleep(dt)
  if p.isConnected():print(json.dumps({'mode':args.mode,'seconds':args.seconds,'final_base_com_xyz_m':p.getBasePositionAndOrientation(robot)[0],'claim':'execution check only; no balance or gait validation'}))
 finally:
  if p.isConnected():p.disconnect()
if __name__=='__main__':main()
