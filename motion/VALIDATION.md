# Verification record

**Scope note for the 2026-09-22 GitHub upload:** the record below describes the original full bundle. This checkout omits CAD/STL assets. Its current checks and the explicit mesh-test skip are recorded in [repository validation](../docs/VALIDATION.md). No wheel containing geometry is distributed here.

Build date: 2026-09-21. Version: 0.1.0. Policy status: **all five skills untrained**.

## Completed in the build workspace

- 14 CPU unit tests passed with Python 3.12.14 and NumPy 2.3.5.
- All Python files compiled successfully, including the Isaac modules and launch scripts. Compilation is a syntax check; it does not import Isaac or establish API compatibility.
- A Python wheel built successfully with the bundled URDF, data and ten mesh files.
- CLI environment detection and policy listing ran successfully; all five skills report `untrained`.

Tests independently check the nine named joints, ten rigid links, valid meter-scale binary STL files, positive inertias, estimated total mass, and forward kinematics against the source geometry at both endpoints. Other checks cover the original-neutral/revised-pose distinction, the 136-input history layout, target clipping and slew, rejection of missing/mismatched checkpoints, stale/repeated sensor samples, non-finite policy output, measured tick conversion and the selector's dwell/timeout behavior.

The policy-switch tests use clearly identified mock functions to exercise software routing. They do not test neural network competence and are not supplied as usable policies.

## Not run

| Check | Status and reason |
|---|---|
| Isaac asset import and PhysX collision inspection | Not run: Isaac Sim/Isaac Lab unavailable |
| RSL-RL training or convergence | Not run: simulator, PyTorch and GPU runtime unavailable |
| ONNX export and numerical parity | Not run: no trained checkpoint or ONNX Runtime |
| Single-skill simulation evaluation | Not run: no trained checkpoint/simulator |
| Dynamic sit-to-low, return, crawl or chained handoff | Not established |
| Hardware calibration or deployment | Not run: servo model/measurements and robot access unavailable |

The code targets Isaac Lab 2.3.0 and Isaac Sim 5.1.0 using the primary API references in `docs/SOURCES.md`. A simulator-equipped environment must run `scripts/smoke_sim.py` and the short training API check before long training. The CPU checks establish package and interface behavior only.
