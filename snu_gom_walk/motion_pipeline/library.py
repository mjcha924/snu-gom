"""Versioned procedural library, strict provenance and bounded retries."""

import hashlib
import json
from pathlib import Path

import numpy as np

from .model import RobotModel, ROOT, digest, fingerprint, write_json
from .contract import validate_contract


def source_hashes(directory=None):
    """Hash Python contents with checkout line endings normalized to LF.

    Report, data and robot-asset hashes remain byte-exact. Python's parser also
    normalizes source newlines, so CRLF/LF alone must not invalidate a dataset.
    """
    directory = Path(directory) if directory is not None else Path(__file__).parent
    return {
        p.name: hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for p in sorted(directory.glob("*.py"))
        if p.name not in ("bank.py", "review.py")
    }


def build(
    robot, output, count=4, seconds=4.0, fps=50, seed=20261121, physics_seconds=None
):
    from .generate import generate
    from .validate import validate_file
    from .physics import rollout
    from .feasibility import screen_reference
    from .review import render

    if count < 4:
        raise ValueError(
            "At least four clips are required for stand/walk train/val separation"
        )
    config = dict(
        count=count,
        seconds=seconds,
        fps=fps,
        seed=seed,
        physics_seconds=physics_seconds,
    )
    revision = fingerprint(dict(config=config, sources=source_hashes()))
    output = Path(output).resolve()
    run = output / f"{robot.model_id[:12]}-{revision[:10]}"
    run.mkdir(parents=True, exist_ok=True)
    manifest = dict(
        schema="gom_motion_library_v1",
        model_id=robot.model_id,
        profile=robot.profile,
        asset_hashes=robot.hashes,
        generator_hashes=source_hashes(),
        config=config,
        clips=[],
        rejected=[],
        hardware_ready=False,
    )
    rng = np.random.default_rng(seed)
    review = []
    for i in range(count):
        kind = "stand" if i % 2 == 0 else "walk"
        split = "val" if i >= count - 2 else "train"
        parameters = dict(robot.profile["generation"])
        for key in ["period_s", "speed_m_s", "torso_roll_deg", "neck_yaw_deg"]:
            parameters[key] *= float(rng.uniform(0.92, 1.08))
        accepted = False
        for attempt in range(3):
            name = f"{kind}_{i:03d}_a{attempt}"
            path = run / (name + ".npz")
            arrays, metadata = generate(robot, kind, seconds, fps, parameters)
            np.savez_compressed(path, **arrays)
            validation, preview = validate_file(robot, path)
            metadata.update(
                clip_sha256=digest(path),
                model_id=robot.model_id,
                kind=kind,
                split=split,
            )
            write_json(path.with_suffix(".metadata.json"), metadata)
            physical = None
            trace = []
            screen = None
            if validation["passed"]:
                screen = screen_reference(robot, arrays)
                screen["clip_sha256"] = digest(path)
                write_json(path.with_suffix(".screen.json"), screen)
                physical, trace = rollout(robot, arrays, physics_seconds)
                physical["clip_sha256"] = digest(path)
                write_json(path.with_suffix(".physics.json"), physical)
                write_json(
                    path.with_suffix(".trace.json"),
                    dict(frames=trace, joint_names=robot.names),
                )
                if trace:
                    np.savetxt(
                        path.with_suffix(".torque.csv"),
                        np.c_[
                            [r["time_s"] for r in trace],
                            np.array([r["torque_nm"] for r in trace]),
                        ],
                        delimiter=",",
                        header="time_s," + ",".join(robot.names),
                        comments="",
                    )
            entry = dict(
                id=name,
                kind=kind,
                split=split,
                file=path.name,
                sha256=digest(path),
                validation_sha256=digest(path.with_suffix(".validation.json")),
                kinematic_verified=validation["passed"],
                dynamics_verified=bool(physical and physical["passed"]),
                reference_eligible=bool(
                    validation["passed"] and screen and screen["reference_eligible"]
                ),
                duration_s=float(arrays["time"][-1]),
                fps=fps,
                parameters=parameters.copy(),
            )
            if physical:
                entry["physics_sha256"] = digest(path.with_suffix(".physics.json"))
            if screen:
                entry["screen_sha256"] = digest(path.with_suffix(".screen.json"))
                entry["motor_status"] = screen["motor_status"]
            review.append(
                dict(
                    entry=entry,
                    kinematic=validation,
                    screen=screen,
                    physics=physical,
                    preview=preview,
                    trace=trace,
                )
            )
            if entry["reference_eligible"]:
                manifest["clips"].append(entry)
                accepted = True
            else:
                manifest["rejected"].append(
                    dict(
                        id=name,
                        checks=[k for k, v in validation["checks"].items() if not v],
                        motor_status=screen["motor_status"] if screen else None,
                    )
                )
            write_json(run / "manifest.json", manifest)
            print(
                f'{name}: kinematic={validation["passed"]}; reference={entry["reference_eligible"]}; motor={entry.get("motor_status")}; physics={entry["dynamics_verified"]}',
                flush=True,
            )
            if accepted:
                break
            # Smaller/slower authored tasks, never a relaxation of the gates.
            parameters["speed_m_s"] *= 0.7
            parameters["clearance_m"] *= 0.85
            parameters["torso_roll_deg"] *= 0.5
            parameters["torso_pitch_deg"] *= 0.5
        if not accepted:
            print(f"No eligible reference clip for {kind}/{split}", flush=True)
    render(run / "review.html", review, manifest)
    required = {
        (kind, split) for kind in ("stand", "walk") for split in ("train", "val")
    }
    present = {(entry["kind"], entry["split"]) for entry in manifest["clips"]}
    missing = [f"{kind}/{split}" for kind, split in sorted(required - present)]
    summary = dict(
        schema="gom_pipeline_summary_v1",
        model_id=robot.model_id,
        config=config,
        complete=not missing,
        missing_required_splits=missing,
        accepted_kinematic=sum(r["kinematic"]["passed"] for r in review),
        accepted_physics=sum(c["dynamics_verified"] for c in manifest["clips"]),
        accepted_reference=sum(c["reference_eligible"] for c in manifest["clips"]),
        rejected_attempts=len(manifest["rejected"]),
        isaac_runtime_verified=False,
        gpu_training_run=False,
        clips=[
            dict(
                id=r["entry"]["id"],
                kind=r["entry"]["kind"],
                split=r["entry"]["split"],
                kinematic=r["kinematic"]["passed"],
                physics=bool(r["physics"] and r["physics"]["passed"]),
                failed_kinematic_checks=[
                    k for k, v in r["kinematic"]["checks"].items() if not v
                ],
                physics_checks=r["physics"]["checks"] if r["physics"] else None,
            )
            for r in review
        ],
    )
    write_json(run / "summary.json", summary)
    write_json(
        output / "latest.json",
        dict(
            run=(
                run.relative_to(ROOT).as_posix()
                if run.is_relative_to(ROOT)
                else str(run)
            )
        ),
    )
    print("RUN_DIRECTORY=" + str(run.resolve()), flush=True)
    return run, summary


def load_library(
    path,
    *,
    split="train",
    kind=None,
    allow_kinematic=None,
    require_dynamics=False,
    urdf=None,
    check_sources=True,
):
    """Recompute all live asset fingerprints before exposing any training target."""
    path = Path(path).resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    robot = RobotModel(manifest["profile"], urdf=urdf, with_physics=False)
    if manifest.get("schema") != "gom_motion_library_v1":
        raise ValueError("Unsupported motion library schema")
    entries = manifest["clips"]
    if len({e["id"] for e in entries}) != len(entries) or len(
        {e["file"] for e in entries}
    ) != len(entries):
        raise ValueError("Duplicate clip IDs/files across splits")
    if {e["sha256"] for e in entries if e["split"] == "train"} & {
        e["sha256"] for e in entries if e["split"] == "val"
    }:
        raise ValueError("Identical motion files leaked across train/val")
    if (
        robot.model_id != manifest["model_id"]
        or robot.hashes != manifest["asset_hashes"]
    ):
        raise ValueError(
            "URDF/profile/mesh changed. Regenerate and revalidate the motion library."
        )
    if check_sources and manifest["generator_hashes"] != source_hashes():
        raise ValueError(
            "Generator/validator changed. Rebuild the library before training."
        )
    loaded = []
    for entry in manifest["clips"]:
        if entry["split"] != split or (kind and entry["kind"] != kind):
            continue
        clip = (path.parent / entry["file"]).resolve()
        if not clip.is_relative_to(path.parent):
            raise ValueError("Motion file escapes run directory")
        if digest(clip) != entry["sha256"]:
            raise ValueError("Motion file modified: " + entry["id"])
        validation = clip.with_suffix(".validation.json")
        if digest(validation) != entry["validation_sha256"]:
            raise ValueError("Validation report modified")
        report = json.loads(validation.read_text(encoding="utf-8"))
        if (
            not report["passed"]
            or report["clip_sha256"] != entry["sha256"]
            or report["model_id"] != robot.model_id
            or report["geometry_frame_stride"] != 1
        ):
            raise ValueError("Missing/stale full-frame validation")
        screen = clip.with_suffix(".screen.json")
        if not screen.exists() or digest(screen) != entry.get("screen_sha256"):
            raise ValueError("Missing/modified motor reference screen; rebuild library")
        assessment = json.loads(screen.read_text(encoding="utf-8"))
        if (
            not entry.get("reference_eligible")
            or not assessment["reference_eligible"]
            or assessment["model_id"] != robot.model_id
            or assessment["clip_sha256"] != entry["sha256"]
        ):
            raise ValueError(
                "Reference exceeds motor planning envelope or has a stale screen"
            )
        physics = clip.with_suffix(".physics.json")
        if entry.get("physics_sha256"):
            if not physics.exists() or digest(physics) != entry["physics_sha256"]:
                raise ValueError("Physics report modified")
            result = json.loads(physics.read_text(encoding="utf-8"))
            if (
                result["clip_sha256"] != entry["sha256"]
                or result["model_id"] != robot.model_id
            ):
                raise ValueError("Stale physics result")
        if require_dynamics or allow_kinematic is False:
            if (
                not entry["dynamics_verified"]
                or not physics.exists()
                or digest(physics) != entry.get("physics_sha256")
            ):
                raise ValueError(
                    "No passing physics validation for --require-dynamics. Default reference mode uses kinematic and motor screens independently of tracking success."
                )
            result = json.loads(physics.read_text(encoding="utf-8"))
            if (
                not result["passed"]
                or result["clip_sha256"] != entry["sha256"]
                or result["model_id"] != robot.model_id
            ):
                raise ValueError("Stale physics result")
        with np.load(clip, allow_pickle=False) as raw:
            a = {k: raw[k].copy() for k in raw.files}
        validate_contract(a, robot.names, robot.model_id)
        loaded.append((entry, a))
    if not loaded:
        raise ValueError(f'No eligible {kind or "all"}/{split} clips')
    return robot, manifest, loaded


def export_dataset(run, output=None):
    """Whitelist only versioned data; preserve repository-relative layout."""
    import zipfile

    run = Path(run).resolve()
    path = run / "manifest.json"
    robot = None
    for split in ["train", "val"]:
        robot, _, _ = load_library(path, split=split, allow_kinematic=True)
    # The ZIP carries data, not model assets. External or absolute mesh paths
    # cannot be resolved by another checkout even if this machine can load them.
    if not robot.urdf.is_relative_to(ROOT) or any(
        not mesh.is_relative_to(ROOT) for mesh in robot.meshes.values()
    ):
        raise ValueError(
            "Portable export requires URDF and meshes inside the repository"
        )
    if any(Path(uri).is_absolute() for uri in robot.meshes):
        raise ValueError("Portable export requires relative or package:// mesh URIs")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    files = [path, run / "summary.json"]
    for e in manifest["clips"]:
        clip = (run / e["file"]).resolve()
        if not clip.is_relative_to(run):
            raise ValueError("Dataset path escapes run")
        for suffix in [
            ".npz",
            ".validation.json",
            ".screen.json",
            ".physics.json",
            ".metadata.json",
        ]:
            candidate = clip.with_suffix(suffix)
            if candidate.exists():
                files.append(candidate)
    if not run.is_relative_to(ROOT):
        raise ValueError("Keep run inside repository for portable server export")
    output = Path(output) if output else run.parent / (run.name + "-data.zip")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(set(files)):
            archive.write(file, file.relative_to(ROOT).as_posix())
    return dict(file=str(output), sha256=digest(output), files=len(set(files)))
