# GitHub release checks

Date: 2026-09-22. Scope: text-only project upload with external CAD in Onshape.

| Check | Result |
| --- | --- |
| Motion/runtime and XML model tests | 14 passed |
| Optional binary mesh test | 1 explicitly skipped because every mesh is intentionally omitted |
| Python source compilation | Passed for motion sources, scripts and examples |
| Policy registry listing | All five skills remain untrained |
| Robot metadata | Original V0.6 URDF, parameters and joint registry retained |
| Geometry files | STEP, STL, BREP and other CAD files excluded |
| GitHub Actions | Workflow included; no remote execution result claimed by this record |

The existing combined model test was separated so joint structure, inertias, estimated mass and endpoint kinematics still run without CAD files. The separate mesh test runs when any mesh is present and rejects an incomplete set. It retains the original binary STL format and meter-scale checks.

The tests ran from this checkout with `PYTHONPATH=motion/src python -m unittest discover -s motion/tests -v`. Compilation used `python -m compileall -q motion/src motion/scripts motion/examples`; policy status used `python -m snu_bear_motion.cli list --registry motion/policies/registry.json` with the same source path.

The [original motion validation record](../motion/VALIDATION.md) and [historical CAD report](V06_HISTORICAL_FEASIBILITY.md) refer to earlier full bundles. Those records are not evidence that this reduced checkout contains the meshes or that the live Onshape geometry was validated.

Isaac import, dynamics, training, ONNX policy evaluation and hardware tests were not run for this upload. Dimensions are provisional; sit-to-low feasibility remains an engineering and simulation task.
