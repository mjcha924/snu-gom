# Experimental BAM actuator integration

Date: 2026-11-17 KST. **Opt-in research adapter, not hardware-calibrated control.**

## Purpose and scope

[BAM](https://github.com/Rhoban/bam) identifies actuator behavior from measured
trajectories. Better motor, friction, and reflected-inertia estimates can reduce
sim-to-real mismatch, provided they match the actual servos, operating mode,
supply, and gains. They do not make an infeasible gait balanced.

Upstream currently supplies MuJoCo and mjlab integrations, not an Isaac Sim
backend. Its package declares Python >=3.12,<3.13; our Isaac environment uses
Python 3.11. This implementation does not force-install incompatible packages,
change CUDA, or replace Isaac Sim. It uses a small native Torch motor equation and
Isaac Sim 5's torque-valued joint friction, with pinned BAM parameters.

The first supported model is **XL330 M1**, not M6. M1 uses Coulomb/viscous friction:
this is identified parameterization, not yet BAM's extended load-dependent
friction. M2–M6 need separate simulator integration and dynamic validation.

## What changes

- Eight XL330-M288-T joints: both hip yaw, hip roll, ankle pitch, and neck joints.
- PWM-limited position control and DC motor torque with back-EMF, evaluated on
  the GPU every physics step (2 ms). Firmware P gain is not an Isaac stiffness.
- BAM reflected armature inertia and native PhysX static/dynamic friction, both
  set to the M1 Coulomb torque, plus native viscous friction. The adapter does not
  also subtract friction in its torque calculation.
- Disable implicit PD stiffness/damping on these joints to avoid double control.
- Four XC330-M288-T hip-pitch/knee joints retain the existing provisional implicit
  controller. **No XL330 parameters are substituted for XC330s.** The CSV motor
  table and joint layout are checked before activation.
- Preserve the URDF's provisional 0.15 N·m actuator cap and 1 rad/s speed setting.
  The cap is an experiment constraint, not an identified current limiter. Solver
  speed settings still do not establish hard physical speed compliance.
- Default training remains `--actuator-model implicit`. Original URDF/STLs,
  rewards, observations, and termination rules are unchanged by enabling BAM.

`computed_effort` is electrical torque before the experiment cap;
`applied_effort` is the capped motor command, excluding passive joint friction.
Neither is measured hardware torque. M1 friction is resolved by PhysX, so matching
coefficients does not establish trajectory equivalence to MuJoCo.

## Provenance and deliberately excluded assumptions

Upstream revision: `b9e11118e17fe8ec803d430202f6fcf31d57901e`.

- [Parameter file](https://github.com/Rhoban/bam/blob/b9e11118e17fe8ec803d430202f6fcf31d57901e/bam/params/xl330/m1.json)
- [Electrical model](https://github.com/Rhoban/bam/blob/b9e11118e17fe8ec803d430202f6fcf31d57901e/bam/actuator.py)
- [XL330 control conversion](https://github.com/Rhoban/bam/blob/b9e11118e17fe8ec803d430202f6fcf31d57901e/bam/dynamixel/actuator.py)
- [Upstream Apache-2.0 license](https://github.com/Rhoban/bam/blob/b9e11118e17fe8ec803d430202f6fcf31d57901e/LICENSE)

The fetcher verifies SHA-256
`3774df0ea9e329b9e1ae6b1debb18d701d674a84006def89e23f90e38883acf2`.
Run manifests embed parameters, selected voltage/gain, and provenance; playback
needs no network or downloaded profile. Modified fits fail validation rather
than silently changing an experiment. Future measured fits require a reviewed
profile/version update.

Supply and gain must be explicitly supplied. The bench below uses **5 V and gain
400 as trial assumptions**, not measurements of SNU-GOM. Upstream's XL330 class
has a 7.5 V default; we do not adopt it. ROBOTIS specifies 3.7–6 V, recommending
5 V for this motor; the adapter rejects out-of-range voltage.
[ROBOTIS specification](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/)

The fit's `q_offset` and `command_delay` are test-rig nuisance parameters and are
not applied to this robot. Command transport delay, firmware I/D control, profile
generation, current limiting, battery sag, backlash, thermal behavior, and
load-dependent friction remain unmodeled here. Measure them before expanding
the adapter; do not assume zero real-world delay because this prototype omits it.

## Reproduce

From the repository root, using the existing Isaac Python environment:

```bash
PY=/home/mjcha/miniconda3/envs/env_isaaclab/bin/python
$PY scripts/fetch_bam_profile.py
$PY scripts/check_stand.py --seconds 10 --headless \
  --actuator-model bam-xl330-m1 --bam-profile .deps/bam/xl330-m1.json \
  --bam-voltage 5 --bam-kp 400

$PY scripts/train.py --task stand --num-envs 64 --iterations 5 --headless \
  --actuator-model bam-xl330-m1 --bam-profile .deps/bam/xl330-m1.json \
  --bam-voltage 5 --bam-kp 400 --output runs/bam_m1_smoke_64
```

Use a new output directory on subsequent runs. The five-update run is an API,
batching, reset, and export smoke test, **not evidence of learned standing**.
Runtime checks verify native friction/inertia and disabled implicit drives.
Changing actuator models is a new experiment; strict source/settings guards
intentionally reject resuming old checkpoints under changed dynamics.

For equation parity against upstream, without installing BAM into Isaac:

```bash
git clone https://github.com/Rhoban/bam.git .upstream/bam
git -C .upstream/bam checkout b9e11118e17fe8ec803d430202f6fcf31d57901e
$PY -m pip install --target .deps/bam-parity colorama==0.4.6
PYTHONPATH="$PWD/.deps/bam-parity" $PY scripts/check_bam_parity.py --upstream .upstream/bam
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $PY -m pytest tests/walking -q
```

This narrowly exercises upstream's NumPy model source on the tested interpreter;
it is not a claim that upstream's full package supports Python 3.11.

## Initial evidence

Machine-readable results: [validation report](data/bam-m1-validation.json).

- 512 position/velocity samples match upstream electrical torque to approximately
  1.1e-16 N·m. Friction parameters and armature match. This validates equations,
  not simulator trajectories or hardware transfer.
- The first 5 V / gain-400 neutral-target standing trial falls at **1.32 s**, with
  76.7 mm horizontal drift. Do not replace the stable implicit baseline.
- Repeated with runtime parameter checks: the same 1.32 s failure. The unchanged
  implicit neutral controller survives 10 s with 3.64 mm drift in the same session.
- A 64-environment / five-update smoke run completes 10,240 transitions in 9.39 s;
  native parameter checks and TorchScript action-equivalence checks pass. Saved
  checkpoint playback loads successfully, but that policy falls at 0.74 s. This
  is an integration test, not a trained standing policy; no long run was launched.
- All 31 walking unit tests pass (including CPU/CUDA motor-equation checks on this
  host). Existing support-reference tests are included in that total.
- These settings change effective control stiffness as well as inertia/friction;
  a failure does not identify which contribution dominates or prove real hardware
  cannot stand. Do not raise motor torque limits to conceal the failure.

## Next acceptance gates

### Optional Isaac → MuJoCo → hardware workflow

BAM is optional. The upstream [MuJoCo integration](https://bam.readthedocs.io/en/latest/usage/mujoco_cpu.html)
is a more direct route to its full models than this experimental Isaac adapter.
First transfer the policy interface and reproduce the baseline actuation model
in MuJoCo; otherwise a failure conflates simulator differences with changed motor
dynamics. Match joint signs/order, observations and normalization, action offsets
and scaling, timing, model inertias, and contact settings before interpreting a
cross-simulator result.

Next compare independently calibrated actuator models, including BAM if useful.
If the more realistic dynamics break a policy, train/fine-tune with those dynamics
or a validated approximation rather than swapping them only at deployment. BAM's
[mjlab backend](https://bam.readthedocs.io/en/latest/usage/mjlab_gpu.html) is another
training option, not a requirement to abandon Isaac now. A successful sim-to-sim
test is a robustness check, not proof of sim-to-real success or safety. A simpler
model that predicts held-out hardware measurements better is preferable to an
uncalibrated complex one.

### Calibration and deployment gates

1. Verify real servo models, supply under load, firmware mode, P/I/D gains,
   PWM/current limits, position profiles, encoder signs, and transport timing.
2. On a restrained single-joint pendulum bench, collect time-aligned target,
   position, velocity, voltage, and current over multiple loads and speeds.
   Fit XL330 and XC330 separately; reserve held-out trajectories.
3. Compare the original controller, matched small-signal motor response, then
   friction/inertia additions independently. Do not interpret this first combined
   model switch as a controlled friction ablation.
4. Require agreement on held-out step responses, reversals, settling, and loaded
   holding. Compare cross-engine pendulum trajectories before claiming PhysX
   reproduces BAM dynamics, especially around sticking/sliding transitions.
5. Restore standing and repeated lift/land balance with the validated model before
   launching long PPO runs. Report all failures and retain the implicit baseline.
6. Add M2–M6 only with validated friction-budget semantics and external joint-load
   estimation. Do not feed motor command back as a substitute for external load.
7. Finally randomize measured parameter ranges and test policies on restrained
   hardware. This is where reduced sim-to-real error must actually be demonstrated.
