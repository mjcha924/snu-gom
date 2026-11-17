# V7A reduced-reference-weight experiment

Research checkpoint, **not a validated walking controller or hardware artifact**.
Uses the original implicit actuators; BAM is disabled. Compared with v6, only
reference imitation weight changes from 3 to 1. The reference remains an in-place
stepping seed despite the 0.01 m/s moving command.

Trained from scratch: 512 environments, seed 42, 100 PPO updates, 1,638,400
transitions. TorchScript action equivalence passes. See the
[experiment report](../../docs/experiments/reference-weight-v7a.md) for actual
survival and stepping results; training return alone is not a walking metric.

Three flat trials survive 12 seconds each but move only 7.6–9.2 mm and complete
zero qualified steps. This is near-standing, not improved walking. Training stops
at this checkpoint rather than extending the same zero-step result.

From the repository root, with the pinned Isaac environment:

```bash
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint policies/reference-weight-v7a/model.pt --scene flat --seconds 12 --episodes 3 --video --headless
"$SNU_GOM_PYTHON" scripts/record_grid.py --checkpoint policies/reference-weight-v7a/model.pt --num-envs 16 --seconds 8 --headless
```

The grid shows exploratory saved-policy rollouts, not optimizer updates. Load only
trusted checkpoints. If source hashes change, use the introducing commit found
with `git log --diff-filter=A -- policies/reference-weight-v7a/model.pt`; do not
bypass the source/model/settings checks.
