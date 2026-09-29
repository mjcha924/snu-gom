# SNU Bear — SHAPE-UP

A small teddy-bear robot project inspired by MicroDuck, with short-looking limbs, oversized paws, and nine actuated pitch joints. The goal is to develop the mechanical design in Onshape, train feedback motion policies in Isaac Lab / Isaac Sim, and run a selectable motion library using joint encoders and an IMU.

**[Open the SNU Bear CAD in Onshape](https://cad.onshape.com/documents/70e60901c3f0fdac6b9cd14a/w/8da76927eccdd278710924b6/e/0a419943727577ede2a57301)**

This repository contains documentation, V0.6 design parameters, an audited URDF, all ten CAD-derived simulation meshes (restored offline from compressed assets), a motion viewer, and the v0.1 motion-library source. STEP/BRep CAD files remain external. Onshape is the shared CAD workspace; the dimensions below record the saved V0.6 baseline and do not automatically track edits to that workspace.

## Design baseline

- Exactly two joints per limb: shoulder + elbow in front, hip + knee at the rear.
- One neck pitch joint; no waist or passive ankle joints.
- Elbow/knee motor cases move with the large paws, with horns connected to the short upper carriers.
- Large head close to the rounded torso, tucked-in limbs, and small lift-and-place shuffles.
- Internal battery space, joint encoders and an IMU; camera-free motion is the initial target.

| Parameter | V0.6 value |
| --- | --- |
| Torso nominal X × Y × Z | 82 × 94 × 104 mm |
| Main head ellipsoid X × Y × Z | 112 × 138 × 114 mm, excluding ears/muzzle |
| Front limb model lengths | 40 + 28 mm |
| Hind limb model lengths | 34 + 30 mm |
| Front paw nominal X × Y × Z | 48 × 50 × 62 mm |
| Hind paw nominal X × Y × Z | 52 × 60 × 66 mm |
| Actuated joints | 9 pitch joints; 10 rigid links |

See [mechanical architecture and parameter definitions](docs/MECHANICAL_DESIGN.md) for joint origins, shell assumptions, packaging, and the distinction between nominal dimensions and finished part bounds.

## Current status

The hardware remains a packaging and kinematic candidate. The recorded V0.6 study checked a small shuffle, but a reliable dynamic sit-to-low transition has not been demonstrated. The motion library provides five training tasks; **all policies remain untrained**. Motor/horn mounts, clearances, electronics selection, dynamics, and hardware testing are unfinished.

| Workstream | Included here | Next step |
| --- | --- | --- |
| Mechanical | Onshape reference, parameters, joint registry, historical feasibility notes | Fit the selected motors/horns and resolve clearances |
| Electronics | [Architecture and open decisions](docs/ELECTRONICS.md), calibration template | Select actuators, power system, controller and IMU |
| Simulation | URDF, restorable meshes, CAD motion playback, experimental PyBullet runner, Isaac task code | Validate collision geometry, motor response and balance |
| Controls | Policy registry, observation/action contract and runtime interfaces | Train, evaluate and calibrate real hardware |
| Project | Roadmap, contribution guide, issue/PR templates and CPU CI | Record reproducible results per robot revision |

## Watch the robot move

```bash
python -m pip install -r requirements-sim.txt
python scripts/simulate.py --mode replay
```

Run inside your virtual environment from the repository root. This restores the meshes automatically and plays the recorded CAD shuffle; it is prescribed motion, not proven dynamic walking. See [the simulation guide](docs/SIMULATING_MOTION.md) for pose inspection, gravity-based tests and Isaac Sim/RL setup.

## Start here

- [Onshape and team CAD workflow](docs/ONSHAPE.md)
- [Mechanical dimensions](docs/MECHANICAL_DESIGN.md)
- [Motion library](motion/README.md) and [training workflow](motion/docs/TRAINING.md)
- [Simulation asset requirements](docs/SIMULATION_ASSETS.md)
- [Roadmap](docs/ROADMAP.md), [contribution guide](CONTRIBUTING.md), and [validation scope](docs/VALIDATION.md)

## Run the CPU tooling

```bash
git clone https://github.com/mjcha924/snu-bear.git
cd snu-bear
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ./motion
snu-bear list --registry motion/policies/registry.json
snu-bear doctor
python scripts/restore_meshes.py
python -m unittest discover -s motion/tests -v
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell. CPU tooling needs Python 3.10 or newer. Simulator code retains the prior API target of Isaac Lab 2.3.0 / Isaac Sim 5.1.0 / Python 3.11; it has not been integration-tested. Restore the included meshes before running tests or simulator imports. The separate mesh test then runs rather than skipping.

## Repository layout

| Path | Contents |
| --- | --- |
| `docs/` | Design dimensions, Onshape link, electronics plan, asset requirements, roadmap and validation |
| `motion/` | Python motion library, training tasks, model metadata, runtime interfaces and tests |
| `.github/` | CPU workflow and collaboration templates |

Project code retains the existing [MIT license](LICENSE). Third-party tools retain their own licenses. The project name and markings do not imply university endorsement.

