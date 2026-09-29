"""Fixed-base pose/joint-sweep inspection; never sends hardware commands."""
import argparse
import math
import time
from check_project import check_model
from generate_robot import OUTPUT, load_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['pose','sweep'], default='pose')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--seconds', type=float, default=30)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error('--seconds must be finite and positive')
    check_model()
    cfg = load_config()
    try:
        import pybullet as p
    except ImportError:
        raise SystemExit('Install: python -m pip install -r requirements-gom-viewer.txt')
    client = p.connect(p.DIRECT if args.headless else p.GUI)
    if client < 0:
        raise RuntimeError('Could not connect to PyBullet')
    try:
        robot = p.loadURDF(str(OUTPUT), [0,0,cfg['base_height_m']], useFixedBase=True)
        joints = {p.getJointInfo(robot,i)[1].decode(): i for i in range(p.getNumJoints(robot))
                  if p.getJointInfo(robot,i)[2] != p.JOINT_FIXED}
        if set(joints) != {j['name'] for j in cfg['joints']}:
            raise RuntimeError('Simulator joint mapping differs from contract')
        if not args.headless:
            p.resetDebugVisualizerCamera(.65,45,-15,[0,0,.16])
            p.addUserDebugText('KINEMATIC PROXY - NOT WALKING',[-.15,0,.37],textSize=1)
        for step in range(max(1,int(args.seconds*120))):
            if not p.isConnected():
                break
            t = step/120
            active = int(t/2)%10
            for i,spec in enumerate(cfg['joints']):
                q = 0.0
                if args.mode == 'sweep' and i == active:
                    wave = math.sin(math.pi*(t%2))
                    q = .12*wave if spec['lower_rad']<0 else .12*abs(wave)
                q = min(spec['upper_rad'],max(spec['lower_rad'],q))
                p.resetJointState(robot,joints[spec['name']],q)
            if not args.headless:
                time.sleep(1/120)
        print('PASS: loaded 10 actuated joints and completed kinematic inspection; no gait claim.')
    finally:
        if p.isConnected():
            p.disconnect()


if __name__ == '__main__':
    main()
