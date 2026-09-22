"""Explicit checkpoint registration; no bundled policy weights are invented."""
import hashlib
import json
import shutil
from pathlib import Path
from .contract import fingerprint, SKILLS

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Registry:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.data = json.loads(self.path.read_text())
        if self.data.get("schema_version") != 1:
            raise ValueError("Unsupported registry schema")

    def resolve(self, skill):
        entry = self.data["skills"][skill]
        if entry["status"] not in ("trained_unverified", "evaluated_in_sim") or not entry["onnx"]:
            raise RuntimeError(f"{skill} has no trained policy. Train and export it first.")
        path = (self.path.parent / entry["onnx"]).resolve()
        if not path.is_relative_to(self.path.parent):
            raise ValueError("Checkpoint must remain inside the policy directory")
        if entry["contract_sha256"] != fingerprint():
            raise ValueError("Checkpoint robot/IO contract does not match this library")
        if not path.is_file() or sha256(path) != entry["sha256"]:
            raise ValueError("Checkpoint missing or checksum mismatch")
        return path

    def register(self, skill, onnx_path, contract_hash):
        if skill not in SKILLS:
            raise ValueError("Unknown skill")
        if contract_hash != fingerprint():
            raise ValueError("Export contract differs from this library")
        src = Path(onnx_path).resolve()
        if src.suffix != ".onnx" or not src.is_file() or src.stat().st_size == 0:
            raise ValueError("Supply a real exported ONNX file")
        # Constructor verifies actual ONNX IO with onnxruntime, not just the extension.
        from .runtime import OnnxPolicy
        OnnxPolicy(src)
        dst = self.path.parent / skill / "policy.onnx"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src != dst:
            shutil.copy2(src, dst)
        self.data["skills"][skill].update(status="trained_unverified", onnx=str(dst.relative_to(self.path.parent)),
            sha256=sha256(dst), contract_sha256=contract_hash, evaluation=None)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2) + "\n")
        tmp.replace(self.path)
