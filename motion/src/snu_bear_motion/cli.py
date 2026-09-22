import argparse
import importlib.util
import json
import shutil
import sys
from .contract import CONTRACT, SKILLS, fingerprint
from .registry import Registry

def main():
    parser = argparse.ArgumentParser(description="SNU Bear motion library")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("contract")
    ls = sub.add_parser("list")
    ls.add_argument("--registry", default="policies/registry.json")
    reg = sub.add_parser("register")
    reg.add_argument("skill", choices=SKILLS)
    reg.add_argument("onnx")
    reg.add_argument("--registry", default="policies/registry.json")
    reg.add_argument("--contract-sha256", required=True)
    args = parser.parse_args()
    if args.command == "doctor":
        print(json.dumps({"python": sys.version.split()[0], "nvidia_smi": shutil.which("nvidia-smi"),
            "packages": {n: importlib.util.find_spec(n) is not None
                         for n in ("isaaclab", "isaacsim", "torch", "gymnasium", "onnxruntime")},
            "training_api_target": "Isaac Lab 2.3.0 / Isaac Sim 5.1.0 / Python 3.11",
            "contract_sha256": fingerprint()}, indent=2))
    elif args.command == "contract":
        print(json.dumps({**CONTRACT, "sha256": fingerprint()}, indent=2))
    elif args.command == "list":
        for name, s in Registry(args.registry).data["skills"].items():
            print(f"{name:16} {s['status']:22} {s['task_id']}")
    else:
        Registry(args.registry).register(args.skill, args.onnx, args.contract_sha256)
        print(f"Registered {args.skill} as trained_unverified. Run simulation evaluation next.")

if __name__ == "__main__":
    main()
