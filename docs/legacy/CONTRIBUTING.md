# Contributing

Use a focused branch and a pull request describing the problem, change and checks performed. The [Onshape workspace](docs/ONSHAPE.md) holds the CAD; this release keeps geometry files out of GitHub.

## Mechanical work

Start with the [design baseline](docs/MECHANICAL_DESIGN.md) and [joint registry](motion/src/snu_bear_motion/data/robot/joint_registry.json). Record the affected part, dimensions, axes, selected hardware and intended manufacturing method. Keep electronics envelopes separate from printed plastic.

Create a named Onshape version and link it in the PR. Revisit reach, collisions, contact, mass and motion assumptions after changing geometry. Simulation meshes must be exported in meters in their link-local frames, as described in [asset requirements](docs/SIMULATION_ASSETS.md).

## Software work

```bash
python -m pip install -e ./motion
python -m unittest discover -s motion/tests -v
python -m compileall -q motion/src motion/scripts motion/examples
```

State whether a change was checked on CPU, imported into Isaac, trained, evaluated dynamically or tested on hardware. The intentionally absent meshes have a separate explicit test skip; CPU success does not prove simulator readiness.

Keep generated logs, simulator caches, measured private calibration and policy weights out of source commits. Tie trained checkpoints to the robot revision, contract fingerprint and evaluation evidence. All initial entries remain untrained. Retain the existing license and relevant third-party notices.
