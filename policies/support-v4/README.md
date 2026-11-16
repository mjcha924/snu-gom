# Experimental shallow-support checkpoint

This is a simulation research artifact, **not a hardware-ready walking policy**.
It uses the supplied robot's provisional limits and a shallow-support joint-target
seed. See [measured results](../../docs/experiments/support-v4.md).

Files: `model.pt` (PPO state), `policy_jit.pt` (exported actor), `config.json`
(settings, dependency versions, source/model hashes), and `summary.json` (training
cost and export check). Only load checkpoints from trusted sources. The exported
actor alone is not a hardware controller: observation construction, residual
reference targets, target slew, actuator bounds, and reset handling are required.

From the repository root, after the pinned Isaac setup:

```bash
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint policies/support-v4/model.pt --scene flat --seconds 12 --video --headless
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint policies/support-v4/model.pt --scene home --seconds 12 --video --headless
"$SNU_GOM_PYTHON" scripts/record_grid.py --checkpoint policies/support-v4/model.pt --num-envs 16 --seconds 8 --headless
```

Playback verifies environment-source and supplied-model hashes. If later code
changes invalidate these hashes, use the commit that introduced this checkpoint
(`git log --diff-filter=A -- policies/support-v4/model.pt`), rather than bypassing
the checks. New experiments should write to `runs/`; do not overwrite this artifact.
