"""CPU-only entry point. No Isaac import, GPU allocation, SSH, or training."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
# Tiny dense dynamics solves are slower when each uses a large BLAS thread pool.
for variable in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']:
    os.environ.setdefault(variable,'1')


def main():
    from snu_gom_walk.motion_pipeline.model import DEFAULT_PROFILE,RobotModel,digest,write_json
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    inspect=sub.add_parser('inspect');run=sub.add_parser('run')
    for p in [inspect,run]:
        p.add_argument('--profile',type=Path,default=DEFAULT_PROFILE);p.add_argument('--urdf',type=Path)
    run.add_argument('--output',type=Path,default=ROOT/'reports/motion_pipeline');run.add_argument('--count',type=int,default=4)
    run.add_argument('--seconds',type=float,default=4.);run.add_argument('--fps',type=int,default=50);run.add_argument('--seed',type=int,default=20261121)
    run.add_argument('--physics-seconds',type=float,help='Optional shorter diagnostic; never marks the full clip physics-passing')
    plan=sub.add_parser('train-plan');plan.add_argument('--run',type=Path,required=True);plan.add_argument('--kind',choices=['stand','walk'],default='walk')
    plan.add_argument('--allow-kinematic',action='store_true');plan.add_argument('--urdf',type=Path)
    review=sub.add_parser('review');review.add_argument('--run',type=Path)
    export=sub.add_parser('export');export.add_argument('--run',type=Path,required=True);export.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.command=='inspect':print(json.dumps(RobotModel(args.profile,args.urdf).audit(),ensure_ascii=False,indent=2))
    elif args.command=='run':
        from snu_gom_walk.motion_pipeline.library import build
        path,result=build(RobotModel(args.profile,args.urdf),args.output,args.count,args.seconds,args.fps,args.seed,args.physics_seconds)
        print(json.dumps(result,indent=2));print('REVIEW='+str(path.resolve()/'review.html'))
    elif args.command=='review':
        import webbrowser
        run=args.run or ROOT/json.loads((ROOT/'reports/motion_pipeline/latest.json').read_text())['run']
        page=run.resolve()/'review.html'
        if not page.is_file():raise FileNotFoundError('Generate the library before opening review')
        webbrowser.open(page.as_uri());print(page)
    elif args.command=='export':
        from snu_gom_walk.motion_pipeline.library import export_dataset
        print(json.dumps(export_dataset(args.run,args.output),indent=2))
    else:
        from snu_gom_walk.motion_pipeline.library import load_library
        path=args.run.resolve()/'manifest.json';robot,manifest,train=load_library(path,kind=args.kind,allow_kinematic=args.allow_kinematic,urdf=args.urdf)
        _,_,val=load_library(path,kind=args.kind,split='val',allow_kinematic=args.allow_kinematic,urdf=args.urdf)
        from snu_gom_walk.model import ALL_JOINTS
        if set(robot.names)!=set(ALL_JOINTS):raise ValueError('Motion generated, but current Isaac adapter requires the SNU GOM 12-joint contract')
        if robot.profile['root_link']!='base_reference' or robot.feet!=['left_foot_link','right_foot_link']:raise ValueError('Changed root/foot roles require a training adapter update')
        from snu_gom_walk.motion_pipeline.model import origin
        import numpy as np
        fixed=next((j for j in robot.robot.findall('joint') if j.find('parent').get('link')=='base_reference' and j.find('child').get('link')=='base_link'),None)
        if fixed is None or fixed.get('type')!='fixed' or not np.allclose(origin(fixed),np.eye(4),atol=1e-9):raise ValueError('Changed root datum requires an Isaac adapter update')
        relative=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        command=['python','scripts/train.py','--task',args.kind,'--motion-manifest',relative,'--num-envs','32','--iterations','2','--headless']
        if args.allow_kinematic:command.append('--allow-kinematic')
        result=dict(schema='gom_training_handoff_v1',model_id=robot.model_id,manifest_sha256=digest(path),
                    train=[e['id'] for e,_ in train],val=[e['id'] for e,_ in val],
                    allow_kinematic=args.allow_kinematic,command=command,training_executed=False,isaac_runtime_verified=False)
        write_json(args.run/'train-plan.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
