# Working in this repository

This is a small, partially validated physical-robot project. Read this file and
[the motion pipeline handoff](docs/MOTION_PIPELINE_HANDOFF.md) before changing
the reference-generation or imitation-training path. User instructions and the
user's chosen working branch take precedence. Keep changes on that branch;
merging or changing another branch is a separate task.

## Sources of truth

- Current 12-joint robot: `snu_gom_description/urdf/snu_gom_preview_relative.urdf`,
  its referenced meshes, and the model's mass/joint tables.
- CPU authoring assumptions: `configs/motion_pipeline/gom.json`.
- CPU entry point: `scripts/motion_pipeline.py`.
- Isaac environment and pinned setup: `snu_gom_walk/env.py`,
  `snu_gom_walk/native_model.py`, and `HEADLESS_TRAINING.md`.
- Start with `docs/MOTION_PIPELINE_KO.md` for usage and
  `docs/MOTION_PIPELINE_HANDOFF.md` for architecture/data contracts.
- `robot/` is an older 0.6 kg proxy. Old checkpoints, CAD previews and experiment
  reports are historical evidence, not validation of a newly edited robot.

## Invariants to preserve

- Read the supplied URDF; do not silently rewrite geometry, axes, inertias,
  position stops, or motor limits to make a test pass. Explicit profile planning
  allowances must remain visible in reports.
- Keep kinematic validity, independent motor-screen eligibility, tracking
  qualification, GPU learning, and hardware performance separate. The default
  learning path intentionally accepts conditional, screened references even if
  this local tracker fails. `--require-dynamics` is an additional opt-in gate.
- Do not bypass model/source/data/report hashes or train/val separation. Source
  changes normally require regenerating references. Preserve LF in Python files.
- The existing Isaac adapter has 12 measured joints, 10 leg actions, and an
  identity `base_reference` -> `base_link` fixed transform. New topology or root
  frames need an explicit adapter update, not guessed joint indices.
- Keep CPU authoring usable without importing Isaac. Do not start GPU training
  as a side effect of review or validation. Use the server's existing pinned
  environment for an explicitly requested GPU run.
- Check the diff before staging. Generated reports, local environments,
  recordings and private CAD do not belong in a code-only change. Include new
  model artifacts only when the current task asks for them.

## Relevant CPU checks

Run from the repository root in a personal Python 3.11 environment with
`requirements-motion-pipeline.txt` and a suitable CPU Torch installed:

```bash
python -m unittest discover -s tests/motion_pipeline -v
python -m unittest discover -s tests/walking -v
python -m unittest discover -s tests -v
python tools/check_project.py
python -m compileall -q snu_gom_walk scripts
```

The last project check covers the older proxy/budget only. After changes to
generation, models, contacts, or acceptance gates, also generate a fresh library
and run `train-plan` for stand and walk, then export/reload it. See the handoff
for exact commands and the distinction between a CPU check and an Isaac run.
Record actual results and remaining limits; do not relabel old evidence as new.
