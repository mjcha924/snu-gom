# V5A supported-lift reward ablation — failed balance

Research checkpoint, **not a walking controller or hardware deployment artifact**.
100 updates, 512 environments, 1,638,400 transitions. The final policy lifts the
right sole about 10–11 mm but falls before a qualified landing; all three flat
diagnostics terminate at approximately 3.3 seconds. Do not replace the more stable
v4 baseline with this policy on the strength of its clearance reward.

See [diagnostics and results](../../docs/experiments/stepping-v5-diagnostics.md).
The checkpoint, exported actor, configuration/hash manifest, and training summary
are included for reproducible experimentation. Load only trusted checkpoints.

After the pinned Isaac setup, from the repository root:

```bash
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint policies/stepping-v5a/model.pt --scene flat --seconds 12 --episodes 3 --video --headless
"$SNU_GOM_PYTHON" scripts/record_grid.py --checkpoint policies/stepping-v5a/model.pt --num-envs 16 --seconds 8 --headless
```

If source hashes later differ, use the commit introducing this checkpoint:
`git log --diff-filter=A -- policies/stepping-v5a/model.pt`. Do not bypass the hash
checks. Keep new training under `runs/`, and preserve the failed experiment.
