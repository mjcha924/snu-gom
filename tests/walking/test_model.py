"""CPU checks for the supplied detailed robot, independent of the legacy proxy."""

from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest
import xml.etree.ElementTree as ET

import numpy as np

from snu_gom_walk.model import ALL_JOINTS, FOOT_LINKS, LEG_JOINTS, ROOT, URDF, audit_model
import snu_gom_walk.model as model_module


class DetailedRobotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = audit_model()
        cls.robot = ET.parse(URDF).getroot()

    def test_mass_and_joint_contract(self):
        self.assertAlmostEqual(self.model["mass_kg"], 1.19250734231, places=8)
        self.assertEqual(len(LEG_JOINTS), 10)
        self.assertEqual(len(ALL_JOINTS), 12)
        self.assertEqual(set(self.model["joints"]), set(ALL_JOINTS))
        self.assertEqual(len(self.model["body_masses"]), 13)

    def test_relative_meshes_are_self_contained(self):
        meshes = self.robot.findall("link/visual/geometry/mesh")
        self.assertEqual(len(meshes), 79)
        for mesh in meshes:
            name = mesh.get("filename")
            self.assertFalse(Path(name).is_absolute())
            path = (URDF.parent / name).resolve()
            self.assertTrue(path.is_relative_to(ROOT / "snu_gom_description"))
            self.assertTrue(path.is_file(), str(path))
            self.assertIn(path.relative_to(ROOT).as_posix(), self.model["hashes"])

    def test_provisional_limits_and_axes(self):
        for name, values in self.model["joints"].items():
            self.assertLess(values["lower"], values["upper"], name)
            self.assertAlmostEqual(values["effort"], 0.15)
            self.assertAlmostEqual(values["velocity"], 1.0)
            self.assertAlmostEqual(np.linalg.norm(values["axis_at_neutral"]), 1.0, places=5)
        left = self.model["joints"]["left_knee_pitch_joint"]["axis_at_neutral"]
        right = self.model["joints"]["right_knee_pitch_joint"]["axis_at_neutral"]
        self.assertLess(np.dot(left, right), -0.99)

    def test_changed_root_datum_requires_an_explicit_training_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            tree=ET.parse(URDF)
            tree.getroot().find("joint[@name='base_reference_joint']/origin").set('xyz','.01 0 0')
            filename=Path(directory)/'robot.urdf';tree.write(filename,encoding='utf-8')
            with patch.object(model_module,'URDF',filename):
                with self.assertRaisesRegex(ValueError,'Changed root datum'):audit_model()

    def test_primitive_collision_and_foot_contract(self):
        collisions = self.robot.findall("link/collision")
        self.assertEqual(len(collisions), 29)
        self.assertTrue(all(collision.find("geometry/box") is not None for collision in collisions))
        self.assertEqual(set(self.model["foot_corners"]), set(FOOT_LINKS))
        for corners in self.model["foot_corners"].values():
            self.assertEqual(np.array(corners).shape, (8, 3))
        self.assertGreater(self.model["initial_height"], 0.15)
        self.assertLess(self.model["initial_height"], 0.18)


if __name__ == "__main__":
    unittest.main()
