"""Workspace-local runtime paths for the installed Isaac Python environment."""

import os
import sys
import traceback
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def configure_runtime(name):
    paths = {
        "XDG_CACHE_HOME": ROOT / ".cache",
        "CUDA_CACHE_PATH": ROOT / ".cache/cuda",
        "TORCH_HOME": ROOT / ".cache/torch",
        "MPLCONFIGDIR": ROOT / ".cache/matplotlib",
        "PYTHONPYCACHEPREFIX": ROOT / ".cache/pycache",
    }
    for variable, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[variable] = str(path)
    for directory in ["reports", "runs", "assets/generated", ".cache/kit", ".cache/warp"]:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    return " ".join([
        f"--/log/file={ROOT}/reports/{name}_kit.log",
        f"--/app/userConfigPath={ROOT}/.cache/kit/user.config.json",
        f"--/app/cachePath={ROOT}/.cache/kit",
        f"--/app/userDataPath={ROOT}/.cache/kit/data",
        "--/app/settings/persistent=false",
        "--/app/asyncRendering=false",
    ])


def close_app(launcher):
    if sys.exc_info()[0] is not None:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    sys.stdout.flush()
    sys.stderr.flush()
    launcher.app.close(skip_cleanup=True)


def configure_asset_cache(cfg, model):
    fingerprint = hashlib.sha256(json.dumps(model["hashes"], sort_keys=True).encode()).hexdigest()[:16]
    cfg.robot.spawn.usd_dir = str(ROOT / "assets/generated/isaac" / fingerprint)
