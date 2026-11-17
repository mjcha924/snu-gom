# Next session: genuine stepping, then longer strides and higher speed

Prepared: 2026-11-17 KST. Execute when the user resumes work; no scheduled or
overnight training is started by this document.

Execution update, November 17: diagnostics and the bounded v5A supported-lift
experiment are complete. A right-foot lift appears, but all three final flat/home
trials fall at approximately 3.3 seconds with zero qualified landings. No speed or
stride progression is authorized by these results. Next isolate a smaller,
joint-rate-feasible lift-and-land sequence with negligible fore-aft motion and
test shorter single support / longer double support, auditing support-knee
saturation and torso pitch. See [the session report](docs/experiments/stepping-v5-diagnostics.md).

## 1. Objective and starting point

Improve the policy/rewards so SNU-GOM transfers weight, lifts each foot, and lands
alternately while moving forward. **Only then increase measured stride length and
walking speed.** Simply rewarding more velocity now risks faster sliding.

Workspace: `/home/mjcha/snu-gom`. Baseline revision: `da2ced7`.

- Latest checkpoint: `policies/support-v4/model.pt`; original run:
  `runs/support_v4_512/`.
- Baseline: 512 environments, 250 PPO updates, 4.096 million transitions,
  approximately 9.5 minutes; about 3 GB total GPU memory at completion.
- Final deterministic flat/home diagnostics: 12 seconds upright, 98.97 mm forward,
  −39.26 mm lateral, −9.20° heading change, **zero clear touchdowns**.
- Sole clearance stayed below 0.50 mm. This is sliding/shuffling, not a short-stride
  walk. No valid measured stride length exists yet.
- Shallow-support reference: 18/20 phases pass the ideal static effort audit;
  unassisted dynamic replay still falls. It is not a validated gait.
- Provisional limits remain 0.15 N·m and 1 rad/s. Observed speed reached 3.22 rad/s;
  configured speed limits are not established hard physical bounds.

Read first: [latest experiment](docs/experiments/support-v4.md),
[setup/reproduction](HEADLESS_TRAINING.md), and
[full curriculum](WALKING_TRAINING_PLAN.md).

## 2. Preserve the baseline and establish diagnostics

1. Read workspace instructions and inspect `git status`; preserve user edits.
2. Verify baseline source/model hashes and keep its checkpoint and videos intact.
   Run baseline playback before changing `snu_gom_walk`, or use an isolated pinned
   checkout inside the workspace. Never bypass the source-hash guard.
3. Extend diagnostics to log, per foot and joint:
   - Normal contact force, minimum sole height, airborne duration, and touchdowns.
   - Reference, residual correction, final slew-limited target, actual position,
     and target-tracking error; look for the policy cancelling the reference.
   - Applied torque, time near the effort limit, and joint velocity at physics
     substeps during a short diagnostic, not only at 50 Hz control samples.
   - Contact-point tangential velocity and accumulated stance sliding distance.
   - Root roll/pitch/yaw, body height, and non-foot contacts during weight transfer.
4. Compare neutral standing, the unassisted seed, and the saved policy under the
   same command. Use short one-robot runs, with plots and a close foot view.
5. Record whether failure is dominated by saturation, unintended collision,
   incorrect target geometry/timing, residual cancellation, or reward incentives.
   Treat these as hypotheses until the traces support them.

Deliverable: `docs/experiments/stepping-v5-diagnostics.md`, with evidence and the
chosen intervention. Do not assume that reward tuning alone fixes infeasible motion.

## 3. Check dynamic feasibility before increasing the task demand

Relevant files: `snu_gom_walk/support_reference.py`, `snu_gom_walk/model.py`,
`scripts/audit_reference_support.py`, and `scripts/check_stand.py`.

1. Inspect the two failed static phases and actual support-leg tracking. Check
   whether the predicted foot motion is realizable with the supplied five-axis
   legs, absent ankle roll, current colliders, and bounded actuators.
2. Test a gentler weight-transfer / small foot-lift sequence if needed. Begin with
   approximately 3–5 mm intended clearance rather than demanding the current seed's
   approximately 13 mm geometric lift. Recompute targets from actual kinematics;
   do not just change a reward constant while leaving reference geometry unchanged.
3. Audit every candidate's position limits, periodic wrap, target velocity, support
   geometry, and collision clearance. The current seed peaks at about 0.969 rad/s,
   so faster cadence or longer strides have almost no demonstrated speed margin.
4. Evaluate under free-base dynamics. Root poses in reference files are audit data,
   never prescribed simulator trajectories. Do not add hidden balancing forces,
   disable self-collision, or raise motor limits to manufacture success.
5. If actuator/model corrections are justified, document the evidence and create a
   separate model-version experiment. Do not silently change the supplied URDF/STLs.
   Missing physical calibration is a limitation to report, not a number to invent.

Decision: proceed with a bounded reward experiment only with explicit feasibility
limitations recorded. If controlled foot unloading remains infeasible, investigate
that first instead of launching repeated long PPO runs.

## 4. Update rewards to distinguish stepping from sliding

Primary file: `snu_gom_walk/env.py`. Keep the actor architecture and observation
contract unchanged initially unless diagnostics show a specific missing input.
Version new reward settings and record them in each run's manifest.

### Problems to test

- Current velocity tracking uses a 0.025 m/s tolerance. At a 0.01 m/s command,
  stationary motion earns `exp(-(0.01 / 0.025)^2) ≈ 0.85` of the maximum forward
  tracking score. This weakly distinguishes standing from moving.
- Reference-assisted clearance uses a narrow Gaussian around target height. From
  grounded feet, a high target can provide very little useful reward variation.
- Reference tracking, contact matching, and placement can reward approximate poses
  without demonstrating a completed alternating step.
- Forward displacement alone accepts skating. A stronger slip penalty alone already
  led to standing in v2; do not repeat that isolated change without diagnostics.

### Proposed reward changes, tested in separate ablations

1. **Dense unloading/lift shaping:** during the intended swing window, reward
   decreasing swing-foot load and increasing clearance toward a modest feasible
   target, with the opposite foot supporting the robot. Saturate above the target;
   do not reward arbitrarily high lifting or prolonged flight. Preserve a smooth
   learning signal before a full clear step is achieved.
2. **Qualified alternating touchdown bonus:** one bounded event bonus after an
   actual lift and landing. Require >2 mm clearance, at least 60 ms airborne,
   opposite-foot support, and correct alternation. Reject contact chatter,
   repeated same-foot taps, simultaneous hopping, and reset/terminal events.
3. **Forward foot placement:** reward bounded landing advance along the commanded
   heading only for qualified touchdowns. Track same-foot stride separately from
   consecutive left/right step spacing. Normalize against a feasible target;
   never pay an uncapped reward for displacement caused by a fall.
4. **Anti-skating:** retain contact-point slip measurement, distinguish rolling
   from whole-foot sliding, and log both speed and accumulated slip. Investigate a
   moderate stance penalty together with lift incentives, rather than merely
   increasing the penalty until the policy stands still.
5. **Sharper speed tracking, later:** once alternating steps appear, test a smaller
   command-relative tracking tolerance, with a documented nonzero floor. Avoid
   making all locomotion reward depend on sparse step events from initialization.
6. **Reference balance:** if residuals cancel an infeasible seed, fix the seed; if
   tracking an overly rigid seed prevents valid motion, test a lower reference
   weight. Change only one interpretable reward group per ablation.

Keep upright survival, bounded yaw/lateral drift, smooth targets, and effort
regularization. For zero command, disable swing/event rewards and reward stable
standing; do not encourage perpetual stepping. Update event state exactly once per
control step and reset it per environment. Account explicitly for event bonuses
versus time-integrated dense rewards so changing timestep does not change incentives.

## 5. Tests and bounded experiment sequence

Before GPU training:

- Add unit tests for genuine alternating landings, grounded sliding, contact chatter,
  both-feet hopping, wrong-foot repetitions, zero commands, and per-env resets.
- Test geometry-derived targets, cyclic continuity, limits, finite rewards, and
  event accounting. Ensure reward and evaluation touchdown definitions agree.
- Keep evaluation independent: also inspect sliding, clearance traces, and video,
  rather than declaring success solely because a training reward rises.

Existing CPU check command:

```bash
cd /home/mjcha/snu-gom
export SNU_GOM_PYTHON=/home/mjcha/miniconda3/envs/env_isaaclab/bin/python
"$SNU_GOM_PYTHON" -m unittest discover -s tests/walking -v
"$SNU_GOM_PYTHON" -m compileall -q snu_gom_walk scripts
```

Experiment order:

| Stage | Budget | Decision |
| --- | --- | --- |
| Diagnostics / reference tests | Short one-robot runs | Identify the primary limitation |
| New environment smoke test | 64 envs, 5 updates | No NaNs, correct resets/events, valid export |
| A: dense unloading/lift shaping | 512 envs, up to 100 updates | Checkpoints at 50/100; inspect actual lifts |
| B: qualified touchdown/placement addition | Same budget and seed as A | Run only if lift is reachable; compare alternation/slip |
| Extend best candidate | At most 250 total updates initially | Only if measured steps improve without losing balance |

Use separate `runs/stepping_v5_*` directories and freeze environment source while
each experiment trains/evaluates. Keep original motor limits and flat floor.
Use fresh training for changed reward/reference contracts; do not silently resume
v4 with incompatible settings or transfer its optimizer state. Resume a new run
only when the existing strict source/settings checks pass.

At each checkpoint, run a fixed three-trial, 12-second deterministic diagnostic
with the same nominal/perturbed starts. Log survival, clear touchdowns per foot,
alternation, distance, heading, sole height, slip, and saturation. Do not cherry-pick
the visually best robot. If no real lifts appear by update 100, stop and inspect
the traces instead of blindly extending the same experiment.

Suggested stepping-discovery gate: all three trials survive; each has at least
two qualified touchdowns per foot and three alternating transitions, with bounded
heading/lateral drift and no hopping exploit. This is only a development gate,
not the final walking acceptance test. Validate promising candidates on fresh seeds.

## 6. Longer strides and faster walking, after stepping works

1. Measure a baseline of real same-foot strides and cadence; no stride estimate
   from sliding displacement. For steady periodic walking, intended same-foot
   stride is approximately commanded speed × full gait-cycle period.
2. First increase intended stride by roughly 10–15% at fixed cycle period, only
   if joint-rate, effort, support, and collision audits retain margin. Compare
   actual landing displacement and stance slip, not just commanded stride.
3. Separately test a modest cadence increase at fixed stride. Do not change stride
   and cadence together initially. Retain whichever changes improve measured
   walking without sacrificing balance or actuator feasibility.
4. Candidate speed stages are 0.01 → 0.015 → 0.02 → 0.025 m/s, conditional on
   feasibility and repeated stepping. These are experiment targets, not promised
   capabilities or an automatic schedule. Hold or revert a stage that regresses.
5. At each successful stage, test start/stop and preservation of standing. Expand
   command ranges only after fixed-command behavior works; scale or regenerate the
   reference consistently rather than changing the command alone.

Final straight-walking gate remains the existing `straight_walk_gate`: at least
20 trials, at least 90% satisfying all checks, 30 seconds upright, ≥0.5 m forward,
≤0.10 m lateral drift, ≤15° heading change, ≥3 clear touchdowns per foot, ≥5
alternating transitions, and speed MAE ≤0.012 m/s. Start/stop, multiple training
seeds, and actuator validation remain additional requirements. A 0.01 m/s target
cannot cover 0.5 m in 30 seconds even with perfect tracking; do not lower the gate.

## 7. Videos, home comparison, and end-of-session handoff

- Train camera-free on flat ground; render separately on the 8 GB GPU.
- Record a close single-robot video and an eight-second 16-robot exploration
  rollout from the selected checkpoint, including failures/resets. Clearly label
  saved-policy rollout versus actual optimizer footage.
- Compare that exact checkpoint on flat and primitive-home scenes with matched
  seeds, commands, and durations. Preserve checkpoint hashes and all trial metrics.
- Keep friction variation, rug edges, thresholds, turning, head motion, and camera
  avoidance out of this experiment. Home training remains an explicit separate run.
- Publish the changed code, tests, measured outcomes, replayable checkpoint, and
  small videos/GIFs using the existing repository workflow. Do not claim natural
  walking if clearance/alternation fail, even when displacement increases.
- End the session with training stopped at a saved checkpoint, a clear pass/fail
  summary, remaining limitations, and the next specific experiment.

## Resume checklist

### Future design changes noted during execution

The user expects short, close-to-body, single-motor arms and a large hollow bear
shell. Exact joint count, masses, materials, attachment points, and motions are
not finalized. Do not assume these additions are massless or build guessed assets.

- Preserve reusable training infrastructure, metrics, and versioned robot assets.
- Initially hold new arms at fixed targets and preserve the leg-policy input/output
  contract where practical. Update mass, center of mass, inertia, and collision
  geometry before evaluating any previous policy on the changed design.
- A visual-only appearance change does not affect the current non-visual actor;
  real shell/servo/arm mass and collision changes do affect dynamics.
- Reconcile existing allowances rather than double-counting them: the supplied
  mass table already reserves 80 g for a torso shell and 15 g per paw cover, and
  includes the printed head shell. Additional arm mechanisms are not included.
  Replace these estimates with measured/final-design mass and inertia as available.
- Try explicitly versioned warm-start/fine-tuning only with compatible observations,
  actions, and normalization. The current strict resume guard must not be bypassed;
  a future migration path must validate compatibility and record the parent policy.
- Train representative arm motion only after fixed-arm locomotion works. Larger
  mechanical changes may need fresh training; transfer success is not guaranteed.
- After reliable walking, consider measured mass/CoM/inertia variation to cover
  modest design uncertainty. Do not add broad guessed randomization to today's
  already-unresolved stepping experiment.

### Session tasks

- [x] Inspect baseline and obtain diagnostic traces.
- [x] Identify feasibility versus reward limitations (dynamic balance still unresolved).
- [x] Implement/test supported-lift and unloading reward ablation A.
- [x] Run bounded ablation A and evaluate checkpoints; defer B after failed balance gate.
- [ ] Increase stride/speed only after qualified alternating steps appear.
- [x] Produce single/16-robot videos and matched home comparison.
- [x] Update results, preserve artifacts, and leave a reproducible handoff.
