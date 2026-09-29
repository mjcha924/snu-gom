> **Legacy V0.6 / 9 joints.** This file describes the previous crawling bear. For the SNU GOM biped start at the root README and `robot/config.json`.

# Policy storage

All registry entries are untrained. There are no bundled `.onnx`, `.pt` or fake checkpoint files.

After training/export, `snu-bear register` copies a real ONNX file into `<skill>/policy.onnx`, records its checksum and the matching training contract hash, and sets status to `trained_unverified`. Registration checks the ONNX input/output interface. Evaluation reports are separate evidence; no automatic hardware-readiness designation is made.

Preserve the associated Isaac environment/agent configs, training manifest, checkpoint and evaluation reports when sharing a learned skill.
