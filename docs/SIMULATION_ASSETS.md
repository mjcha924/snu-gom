# Simulation assets

The repository includes the audited V0.6 URDF and all ten original CAD-derived meshes. STEP/BRep manufacturing files remain in the shared Onshape/CAD workspace.

Run from the repository root:

```bash
python scripts/restore_meshes.py
```

This reconstructs binary STL files into `motion/src/snu_bear_motion/data/robot/meshes_m/`, using lossless XZ/base64 chunks in `assets/v06_meshes/`. The text representation supports the repository upload connection; these are the original meshes, not simplified substitutes. No downloads or CAD libraries are required. Original STL SHA-256 and byte sizes are checked before each write; edited local meshes are not overwritten. The generated STL files are intentionally ignored by git.

The simulation runner restores them automatically. Restore before installing a non-editable wheel or invoking the Isaac tools. All ten meshes must accompany the URDF, and are already in metres.

See [Simulating motion](SIMULATING_MOTION.md) for setup, playback, experimental physics and Isaac import instructions. A URDF alone does not supply a control policy. Mesh restoration does not establish valid collision cooking or physical stability.
