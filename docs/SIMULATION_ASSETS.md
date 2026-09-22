# Simulation assets omitted from this release

This GitHub upload intentionally excludes CAD geometry and STL meshes. CPU policy/runtime tooling and XML model checks can run; Isaac robot import and training need matching geometry first.

The included URDF expects these ten files under `motion/src/snu_bear_motion/data/robot/meshes_m/`:

- `torso.stl`, `head.stl`
- `left_fore_upper.stl`, `left_fore_lower.stl`
- `right_fore_upper.stl`, `right_fore_lower.stl`
- `left_hind_upper.stl`, `left_hind_lower.stl`
- `right_hind_upper.stl`, `right_hind_lower.stl`

For exact baseline reproduction, copy the meter-scale, link-local meshes from the previously saved V0.6 CAD bundle or motion-library bundle. [V06_MESH_SHA256.json](V06_MESH_SHA256.json) records their expected SHA-256 checksums. Keep those files local; geometry extensions are ignored by Git for this release.

The [Onshape document](ONSHAPE.md) is the CAD collaboration reference. A new export from Onshape must be converted into the URDF's link-local frames and meter units; a whole-assembly STL or millimeter export cannot be dropped into these paths. If the geometry differs, update mass/inertia, collision shapes, joint frames, endpoint fixtures and the motion contract deliberately. Record the exact Onshape version and revalidate the robot model.

The test suite skips the mesh test only when every referenced mesh is absent. If some are supplied, it requires the full set. Restoring or changing assets changes the library's contract fingerprint; train/export policies against the completed model. All initial policy registry entries remain untrained.
