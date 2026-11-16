"""CPU regression checks for portable asset caches and failure reporting."""

from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest

from scripts.runtime import ROOT, configure_asset_cache


class RuntimeTests(unittest.TestCase):
    def test_asset_cache_changes_with_mesh_contents(self):
        cfg = SimpleNamespace(robot=SimpleNamespace(spawn=SimpleNamespace()))
        configure_asset_cache(cfg, {"hashes": {"robot.urdf": "first", "mesh.stl": "first"}})
        previous = cfg.robot.spawn.usd_dir
        configure_asset_cache(cfg, {"hashes": {"robot.urdf": "first", "mesh.stl": "changed"}})
        self.assertNotEqual(previous, cfg.robot.spawn.usd_dir)
        self.assertTrue(Path(cfg.robot.spawn.usd_dir).is_relative_to(ROOT / "assets/generated"))

    def test_asset_cache_is_order_independent(self):
        cfg = SimpleNamespace(robot=SimpleNamespace(spawn=SimpleNamespace()))
        configure_asset_cache(cfg, {"hashes": {"robot.urdf": "first", "mesh.stl": "second"}})
        previous = cfg.robot.spawn.usd_dir
        configure_asset_cache(cfg, {"hashes": {"mesh.stl": "second", "robot.urdf": "first"}})
        self.assertEqual(previous, cfg.robot.spawn.usd_dir)

    def test_exception_cannot_be_hidden_by_simulator_shutdown(self):
        program = "\n".join([
            "from scripts.runtime import close_app",
            "try:",
            "    raise RuntimeError('expected failure')",
            "finally:",
            "    close_app(None)",
        ])
        result = subprocess.run([sys.executable, "-c", program], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("RuntimeError: expected failure", result.stderr)


if __name__ == "__main__":
    unittest.main()
