"""CPU integration tests; no Isaac, GPU, remote login or policy training."""
import copy
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET

import numpy as np
import torch

from snu_gom_walk.model import ALL_JOINTS,LEG_JOINTS,forward_kinematics
from snu_gom_walk.motion_pipeline.model import RobotModel,digest,write_json
from snu_gom_walk.motion_pipeline.model import origin
from scipy.spatial.transform import Rotation
from snu_gom_walk.motion_pipeline.generate import generate
from snu_gom_walk.motion_pipeline.validate import validate_arrays,validate_file
from snu_gom_walk.motion_pipeline.library import load_library,source_hashes
from snu_gom_walk.motion_pipeline.bank import MotionBank,observation_features,slerp
from snu_gom_walk.motion_pipeline.physics import ContactController,loaded_contacts
from snu_gom_walk.motion_pipeline.feasibility import screen_reference
from snu_gom_walk.motion_pipeline.motors import torque_envelope,curve_arrays,torch_curve_cap,motor_rows


def fixture(directory,robot=None):
    directory=Path(directory);robot=robot or RobotModel()
    a,_=generate(robot,'stand',seconds=2,fps=10)
    manifest=dict(schema='gom_motion_library_v1',model_id=robot.model_id,profile=robot.profile,asset_hashes=robot.hashes,
                  generator_hashes=source_hashes(),clips=[])
    for i,split in enumerate(['train','val']):
        path=directory/f'clip_{i}.npz';np.savez_compressed(path,**a,clip_seed=np.asarray(i))
        report,_=validate_file(robot,path)
        if not report['passed']:raise AssertionError(report)
        screen=screen_reference(robot,a);screen['clip_sha256']=digest(path);write_json(path.with_suffix('.screen.json'),screen)
        manifest['clips'].append(dict(id=f'clip_{i}',file=path.name,kind='stand',split=split,sha256=digest(path),
                                      validation_sha256=digest(path.with_suffix('.validation.json')),dynamics_verified=False,
                                      screen_sha256=digest(path.with_suffix('.screen.json')),reference_eligible=screen['reference_eligible'],
                                      parameters=robot.profile['generation']))
    path=directory/'manifest.json';write_json(path,manifest);return path,a


class PipelineTests(unittest.TestCase):
    def test_adapter_preserves_mass_fk_and_original_joint_stops(self):
        r=RobotModel();r.set_state(r.nominal,[0,0,0],[0,0,0,1])
        expected=forward_kinematics(dict(zip(r.names,r.nominal)))
        self.assertAlmostEqual(r.mass,float(r.model.body_mass.sum()),places=9)
        for name,T in expected.items():
            site=r.model.site(name+'__frame').id
            np.testing.assert_allclose(r.data.site_xpos[site],T[:3,3],atol=1e-9)
            np.testing.assert_allclose(r.data.site_xmat[site].reshape(3,3),T[:3,:3],atol=1e-9)
        knee=r.names.index('left_knee_pitch_joint');j=r.model.joint(r.names[knee]).id
        self.assertGreater(r.lower[knee],r.urdf_lower[knee])
        self.assertAlmostEqual(r.model.jnt_range[j,0],r.urdf_lower[knee])

    def test_generated_walk_passes_full_frame_kinematics_without_dynamic_claim(self):
        r=RobotModel();a,_=generate(r,'walk',seconds=4,fps=50);report,_=validate_arrays(r,a)
        self.assertTrue(report['passed'],report)
        self.assertEqual(report['frames_checked'],201)
        self.assertFalse(report['dynamics_verified'])
        self.assertTrue((a['target_sole_height_m'].max(0)>.003).all())
        self.assertLess(max(report['torso_peak_to_peak_deg'][:2]),3.)
        screen=screen_reference(r,a)
        self.assertTrue(screen['reference_eligible'],screen)
        self.assertTrue(set(screen['solver_statuses'])<={0,2})
        self.assertLess(screen['max_equation_residual'],1e-6)

    def test_stand_never_schedules_or_lifts_a_swing_foot(self):
        a,_=generate(RobotModel(),'stand',seconds=2,fps=10)
        np.testing.assert_array_equal(a['planned_contacts'],1)
        np.testing.assert_allclose(a['target_sole_height_m'],0)

    def test_nonfinite_input_rejected_before_calling_physics(self):
        r=RobotModel();a,_=generate(r,'stand',seconds=2,fps=10);a['joints_pos'][0,0]=np.nan
        with self.assertRaisesRegex(ValueError,'Nonfinite'):validate_arrays(r,a)

    def test_body_ground_contact_is_not_mistaken_for_valid_support(self):
        r=RobotModel();a,_=generate(r,'stand',seconds=2,fps=10)
        for key in ['root_pos','com_world','target_com_world']:a[key][...,2]-=.3
        for key in ['foot_positions_world','target_foot_positions_world']:a[key][...,2]-=.3
        report,_=validate_arrays(r,a)
        self.assertFalse(report['passed'])
        self.assertTrue(any(' / floor' in pair for pair in report['collision_max_penetration_m']))

    def test_stl_sole_requires_datum_and_preserves_contact_vertices(self):
        from scipy.spatial import ConvexHull
        with tempfile.TemporaryDirectory() as directory:
            r=RobotModel();xml=ET.parse(r.urdf);profile=copy.deepcopy(r.profile)
            for mesh in xml.getroot().findall('.//mesh'):mesh.set('filename',str(r.resolve_mesh(mesh.get('filename'))))
            n=r.feet[0];c=xml.getroot().find(f"link[@name='{n}']/collision");T=origin(c)
            size=np.fromstring(c.find('geometry/box').get('size'),sep=' ')
            import itertools
            vertices=np.array(list(itertools.product([-1,1],repeat=3)))*size/2;triangles=vertices[ConvexHull(vertices).simplices]
            mesh_path=Path(directory)/'sole.stl'
            with mesh_path.open('wb') as f:
                f.write(b'test contact hull'.ljust(80,b'\0'));f.write(struct.pack('<I',len(triangles)))
                for tri in triangles:f.write(struct.pack('<12fH',0.,0.,0.,*tri.reshape(-1),0))
            geometry=c.find('geometry');geometry.remove(geometry.find('box'));ET.SubElement(geometry,'mesh',filename=str(mesh_path))
            urdf=Path(directory)/'robot.urdf';xml.write(urdf,encoding='utf-8');profile['urdf']=str(urdf)
            with self.assertRaisesRegex(ValueError,'sole_frames'):RobotModel(profile)
            profile['sole_frames']={n:dict(xyz=r.sole_local[0].tolist(),rpy=Rotation.from_matrix(T[:3,:3]).as_euler('xyz').tolist())}
            adapted=RobotModel(profile)
            expected=r.foot_points[0];actual=adapted.foot_points[0]
            self.assertLess(np.max(np.min(np.linalg.norm(expected[:,None]-actual[None],axis=-1),axis=1)),1e-7)

    def test_screened_reference_is_default_and_tracker_pass_is_optional(self):
        with tempfile.TemporaryDirectory() as d:
            path,_=fixture(d)
            _,_,clips=load_library(path,kind='stand')
            self.assertEqual(len(clips),1)
            with self.assertRaisesRegex(ValueError,'physics'):load_library(path,kind='stand',require_dynamics=True)

    def test_motor_screen_cannot_be_bypassed_with_compatibility_flag(self):
        with tempfile.TemporaryDirectory() as d:
            path,_=fixture(d);manifest=json.loads(path.read_text());report=Path(d)/'clip_0.screen.json'
            screen=json.loads(report.read_text());screen['reference_eligible']=False;write_json(report,screen)
            manifest['clips'][0]['screen_sha256']=digest(report);write_json(path,manifest)
            with self.assertRaisesRegex(ValueError,'motor planning'):load_library(path,allow_kinematic=True)

    def test_motor_profile_replaces_only_explicit_placeholder_limits(self):
        r=RobotModel();roll=r.names.index('left_hip_roll_joint');pitch=r.names.index('left_hip_pitch_joint')
        self.assertAlmostEqual(r.urdf_effort[roll],.15);self.assertAlmostEqual(r.effort[roll],.312)
        self.assertAlmostEqual(r.effort[pitch],.558)
        profile=copy.deepcopy(r.profile);profile['motors']['override_provisional_urdf_effort_velocity']=False
        limited=RobotModel(profile);self.assertLessEqual(limited.effort[roll],.15);self.assertLessEqual(limited.speed[roll],1.)
        np.testing.assert_array_equal(limited.urdf_lower,r.urdf_lower)
        x,y=curve_arrays(r.profile,r.names);tx=torch.tensor(x);ty=torch.tensor(y)
        for speed in [0,1,2,4,7,11]:
            v=np.full(len(r.names),speed);curve=torch_curve_cap(torch.tensor(v)[None],tx,ty).numpy()[0]
            linear=np.array([row['stall_nm']*max(0,1-speed/row['no_load_rad_s']) for row in motor_rows(r.profile,r.names)])
            np.testing.assert_allclose(np.minimum(np.minimum(curve,linear),r.effort),torque_envelope(r.profile,r.names,v,r.effort))

    def test_reference_screen_rejects_implausible_motors_without_a_tracker(self):
        r=RobotModel();a,_=generate(r,'stand',seconds=2,fps=10)
        screen=screen_reference(r,a);self.assertTrue(screen['reference_eligible']);self.assertFalse(screen['tracking_controller_used'])
        profile=copy.deepcopy(r.profile);profile['motors']['planning_stall_fraction']=.001
        weak=RobotModel(profile);bad=screen_reference(weak,a)
        self.assertFalse(bad['reference_eligible']);self.assertGreater(bad['peak_minimum_torque_utilization'],1)
        a['joints_vel'][:]=100;self.assertFalse(screen_reference(r,a)['reference_eligible'])

    def test_support_polygon_excludes_phantom_aabb_corners(self):
        from snu_gom_walk.motion_pipeline.generate import preview_com
        nominal=np.tile([-.02,.02,.15],(21,1));feet=np.tile([[.02,.02,0],[-.02,-.02,0]],(21,1,1))
        with self.assertRaisesRegex(ValueError,'infeasible'):
            preview_com(nominal,feet,np.ones((21,2)),np.full((2,2),.002),.15,.1)

    def test_train_val_are_disjoint_and_joint_mapping_is_named(self):
        with tempfile.TemporaryDirectory() as d:
            path,a=fixture(d)
            train=MotionBank(path,ALL_JOINTS,kind='stand',allow_kinematic=True)
            val=MotionBank(path,ALL_JOINTS,kind='stand',split='val',allow_kinematic=True)
            self.assertFalse({e['id'] for e in train.entries}&{e['id'] for e in val.entries})
            reverse=MotionBank(path,ALL_JOINTS[::-1],kind='stand',allow_kinematic=True)
            x=train.sample([0],[.37]);y=reverse.sample([0],[.37])
            torch.testing.assert_close(x['joints_pos'].flip(-1),y['joints_pos'])
            before=train.sample([0],[-10]);after=train.sample([0],[100])
            np.testing.assert_allclose(before['joints_pos'][0],a['joints_pos'][0],atol=1e-7)
            np.testing.assert_allclose(after['joints_pos'][0],a['joints_pos'][-1],atol=1e-7)
            extra=observation_features(x,[ALL_JOINTS.index(n) for n in LEG_JOINTS],[10,11])
            self.assertEqual(extra.shape,(1,27));self.assertTrue(torch.isfinite(extra).all())

    def test_sampler_quaternion_shortest_arc(self):
        q=torch.tensor([[1.,0.,0.,0.]])
        torch.testing.assert_close(slerp(q,-q,torch.tensor([[.5]])),q)

    def test_modified_clip_or_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path,_=fixture(d);report=Path(d)/'clip_0.validation.json'
            report.write_bytes(report.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'report modified'):load_library(path,allow_kinematic=True)
        with tempfile.TemporaryDirectory() as d:
            path,_=fixture(d);clip=Path(d)/'clip_0.npz';clip.write_bytes(clip.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'Motion file modified'):load_library(path,allow_kinematic=True)

    def test_modified_generator_and_split_leaks_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path,_=fixture(d);manifest=json.loads(path.read_text());manifest['generator_hashes']['generate.py']='changed';write_json(path,manifest)
            with self.assertRaisesRegex(ValueError,'Generator'):load_library(path,allow_kinematic=True)
            manifest['generator_hashes']=source_hashes();manifest['clips'][1]['sha256']=manifest['clips'][0]['sha256'];write_json(path,manifest)
            with self.assertRaisesRegex(ValueError,'leaked'):load_library(path,allow_kinematic=True)

    def test_urdf_and_mesh_content_changes_invalidate_old_library(self):
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d);original=RobotModel();xml=ET.parse(original.urdf)
            for mesh in xml.getroot().findall('.//mesh'):mesh.set('filename',str(original.resolve_mesh(mesh.get('filename'))))
            visual=xml.getroot().find('.//mesh');local_mesh=directory/'visual.stl';shutil.copyfile(visual.get('filename'),local_mesh);visual.set('filename',str(local_mesh))
            urdf=directory/'robot.urdf';xml.write(urdf,encoding='utf-8')
            profile=copy.deepcopy(original.profile);profile['urdf']=str(urdf)
            robot=RobotModel(profile);path,_=fixture(directory,robot)
            original_bytes=local_mesh.read_bytes();local_mesh.write_bytes(original_bytes+b' ')
            with self.assertRaisesRegex(ValueError,'URDF/profile/mesh'):load_library(path,allow_kinematic=True)
            local_mesh.write_bytes(original_bytes)
            inertial=xml.getroot().find('link/inertial/mass');inertial.set('value',str(float(inertial.get('value'))*1.01));xml.write(urdf,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'URDF/profile/mesh'):load_library(path,allow_kinematic=True)

    def test_contact_derivative_matches_real_forward_dynamics(self):
        import mujoco
        r=RobotModel();a,_=generate(r,'stand',seconds=2,fps=10)
        r.set_state(a['joints_pos'][0],a['root_pos'][0]-[0,0,.0005],a['root_quat'][0]);d=r.data
        self.assertGreater(d.ncon,0)
        c=ContactController(r);u=np.linspace(-.01,.01,len(r.names));acc=c.forward(d,u);force,F=c.inverse_gradient(d,acc)
        np.testing.assert_allclose(force,c.S@u,atol=2e-6)
        expected=np.linalg.solve(F,c.S)
        actual=np.column_stack([(c.forward(d,u+np.eye(len(u))[i]*1e-6)-acc)/1e-6 for i in range(len(u))])
        self.assertLess(np.linalg.norm(expected-actual)/np.linalg.norm(actual),1e-3)
        np.testing.assert_array_equal(d.qfrc_applied,0);np.testing.assert_array_equal(d.xfrc_applied,0)

    def test_separating_geometric_contact_is_not_loaded_support(self):
        import mujoco
        r=RobotModel();a,_=generate(r,'stand',seconds=2,fps=10)
        r.set_state(a['joints_pos'][0],a['root_pos'][0]-[0,0,.0005],a['root_quat'][0])
        state,loads=loaded_contacts(r,r.data,np.zeros(2,dtype=bool))
        self.assertTrue(state.all());self.assertGreater(loads.sum(),r.mass*9.81*.1)
        # Shapes still overlap at this instant, but both feet move away rapidly.
        r.data.qvel[2]=1.;mujoco.mj_forward(r.model,r.data)
        self.assertGreater(r.data.ncon,0)
        state,loads=loaded_contacts(r,r.data,state)
        self.assertFalse(state.any());self.assertLess(loads.sum(),.001)


if __name__=='__main__':unittest.main()
