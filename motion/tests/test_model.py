"""Independent XML forward-kinematics and inertial checks; no physics claims."""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from snu_bear_motion.contract import DATA, JOINTS, CONTRACT as C

def transform(xyz, pitch):
    s, c = np.sin(pitch), np.cos(pitch)
    t = np.eye(4)
    t[:3,:3] = [[c,0,s], [0,1,0], [-s,0,c]]
    t[:3,3] = xyz
    return t

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.robot = ET.parse(DATA/"robot/snu_bear_v06.urdf").getroot()

    def test_nine_pitch_joints_and_positive_inertias(self):
        joints = self.robot.findall("joint")
        self.assertEqual(tuple(j.attrib["name"] for j in joints), JOINTS)
        self.assertEqual(len(self.robot.findall("link")), 10)
        mass = 0
        for link in self.robot.findall("link"):
            mass += float(link.find("inertial/mass").attrib["value"])
            i = {k:float(v) for k,v in link.find("inertial/inertia").attrib.items()}
            matrix = np.array([[i['ixx'],i['ixy'],i['ixz']], [i['ixy'],i['iyy'],i['iyz']],
                               [i['ixz'],i['iyz'],i['izz']]])
            self.assertTrue(np.all(np.linalg.eigvalsh(matrix) > 0))
        self.assertAlmostEqual(mass, 0.6647901834523413, places=10)

    def test_optional_mesh_assets(self):
        paths = sorted({DATA/"robot"/m.attrib['filename']
                        for m in self.robot.findall(".//mesh")})
        if not any(p.is_file() for p in paths):
            self.skipTest("CAD-free release: meshes omitted; see docs/SIMULATION_ASSETS.md")
        for path in paths:
            self.assertTrue(path.is_file(), f"Incomplete mesh set: {path.name}")
            # Binary STL expected model dimensions are meters, not millimeters.
            b = path.read_bytes(); count = int.from_bytes(b[80:84], 'little')
            self.assertEqual(len(b), 84+50*count)
            dtype = np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
            v = np.frombuffer(b, dtype=dtype, offset=84)['v']
            self.assertLess(float(np.abs(v).max()), 0.3)

    def test_endpoint_link_positions_match_original_geometry(self):
        expected = json.loads((Path(__file__).parent/"endpoint_links.json").read_text())
        for pose_name, p in C["poses"].items():
            frames = {"torso": transform([0,0,p["root_height_m"]], p["pitch_rad"])}
            for j, q in zip(self.robot.findall("joint"), p["q_rad"]):
                parent, child = j.find('parent').attrib['link'], j.find('child').attrib['link']
                origin = j.find('origin')
                xyz = [float(x) for x in origin.attrib['xyz'].split()]
                pitch = float(origin.attrib['rpy'].split()[1])
                frames[child] = frames[parent] @ transform(xyz, pitch+q)
            for name, xyz in expected[pose_name].items():
                np.testing.assert_allclose(frames[name][:3,3], xyz, atol=1e-10,
                                           err_msg=f"{pose_name}/{name}")

if __name__ == "__main__": unittest.main()
