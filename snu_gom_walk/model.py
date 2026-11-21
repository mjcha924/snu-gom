"""Read the supplied URDF without changing its kinematic or inertial data."""

import hashlib
import itertools
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation


ROOT = Path(__file__).resolve().parents[1]
URDF = Path(os.environ.get('SNU_GOM_URDF',str(ROOT / "snu_gom_description/urdf/snu_gom_preview_relative.urdf"))).resolve()


def asset_key(path):
    path=Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else 'external/'+os.path.relpath(path,URDF.parent).replace('\\','/')


def mesh_path(uri):
    if uri.startswith('package://'):
        import json
        package,relative=uri[len('package://'):].split('/',1)
        roots=json.loads(os.environ.get('SNU_GOM_PACKAGE_ROOTS','{}'))
        if package not in roots:raise ValueError('Select the matching motion profile package_roots for '+package)
        return ((ROOT/roots[package])/relative).resolve()
    return (URDF.parent/uri).resolve()


LEG_JOINTS = [
    f"{side}_{joint}_joint"
    for side in ["left", "right"]
    for joint in ["hip_yaw", "hip_roll", "hip_pitch", "knee_pitch", "ankle_pitch"]
]
ALL_JOINTS = LEG_JOINTS + ["neck_yaw_joint", "neck_pitch_joint"]
FOOT_LINKS = ["left_foot_link", "right_foot_link"]


def origin_matrix(element):
    matrix = np.eye(4)
    origin = element.find("origin")
    if origin is not None:
        matrix[:3, 3] = np.fromstring(origin.get("xyz", "0 0 0"), sep=" ")
        matrix[:3, :3] = Rotation.from_euler(
            "xyz", np.fromstring(origin.get("rpy", "0 0 0"), sep=" ")
        ).as_matrix()
    return matrix


def forward_kinematics(positions):
    robot = ET.parse(URDF).getroot()
    frames = {"base_reference": np.eye(4)}
    pending = list(robot.findall("joint"))
    while pending:
        progressed = False
        for joint in pending[:]:
            parent = joint.find("parent").get("link")
            if parent not in frames:
                continue
            motion = np.eye(4)
            if joint.get("type") == "revolute":
                axis = np.fromstring(joint.find("axis").get("xyz"), sep=" ")
                axis /= np.linalg.norm(axis)
                motion[:3, :3] = Rotation.from_rotvec(axis * positions.get(joint.get("name"), 0.0)).as_matrix()
            frames[joint.find("child").get("link")] = frames[parent] @ origin_matrix(joint) @ motion
            pending.remove(joint)
            progressed = True
        if not progressed:
            raise ValueError("URDF joint tree is disconnected or cyclic")
    return frames


def stance_configuration(knee_angle, model):
    positions = {name: 0.0 for name in ALL_JOINTS}
    for side, knee_sign in [("left", 1), ("right", -1)]:
        positions[f"{side}_hip_pitch_joint"] = knee_angle / 2
        positions[f"{side}_knee_pitch_joint"] = knee_sign * knee_angle
        positions[f"{side}_ankle_pitch_joint"] = -knee_angle / 2
    frames = forward_kinematics(positions)
    feet = {
        name: np.array(model["foot_corners"][name]) @ frames[name][:3, :3].T + frames[name][:3, 3]
        for name in FOOT_LINKS
    }
    height = -min(corners[:, 2].min() for corners in feet.values())
    centers = {name: corners.mean(axis=0).tolist() for name, corners in feet.items()}
    return positions, float(height), centers


def audit_model():
    robot = ET.parse(URDF).getroot()
    frames = {"base_reference": np.eye(4)}
    pending = list(robot.findall("joint"))
    joints = {}
    while pending:
        progressed = False
        for joint in pending[:]:
            parent = joint.find("parent").get("link")
            if parent not in frames:
                continue
            child = joint.find("child").get("link")
            frames[child] = frames[parent] @ origin_matrix(joint)
            if joint.get("type") == "revolute":
                axis = np.fromstring(joint.find("axis").get("xyz"), sep=" ")
                limits = {key: float(value) for key, value in joint.find("limit").attrib.items()}
                joints[joint.get("name")] = {
                    **limits,
                    "axis_at_neutral": (frames[child][:3, :3] @ axis).tolist(),
                }
            pending.remove(joint)
            progressed = True
        if not progressed:
            raise ValueError("URDF joint tree is disconnected or cyclic")
    if not np.allclose(frames['base_link'],np.eye(4),atol=1e-9):
        raise ValueError('Changed root datum: the current Isaac adapter requires identity base_reference -> base_link; update the adapter explicitly')
    masses = {}
    inertias = {}
    foot_corners = {}
    hashes = {asset_key(URDF): hashlib.sha256(URDF.read_bytes()).hexdigest()}
    for link in robot.findall("link"):
        name = link.get("name")
        inertial = link.find("inertial")
        if inertial is not None:
            masses[name] = float(inertial.find("mass").get("value"))
            values = {key: float(value) for key, value in inertial.find("inertia").attrib.items()}
            matrix = np.array([
                [values["ixx"], values["ixy"], values["ixz"]],
                [values["ixy"], values["iyy"], values["iyz"]],
                [values["ixz"], values["iyz"], values["izz"]],
            ])
            moments = np.linalg.eigvalsh(matrix)
            if masses[name] <= 0 or moments.min() <= 0 or moments[-1] > moments[:2].sum() + 1e-10:
                raise ValueError(f"Invalid mass/inertia for {name}")
            inertias[name] = {"principal_moments": moments.tolist()}
        for mesh in link.findall(".//mesh"):
            path = mesh_path(mesh.get("filename"))
            hashes[asset_key(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        if name in FOOT_LINKS:
            points=[]
            for collision in link.findall('collision'):
                box=collision.find('geometry/box');mesh=collision.find('geometry/mesh')
                if box is not None:
                    half=np.fromstring(box.get('size'),sep=' ')/2
                    corners=np.array(list(itertools.product([-1,1],repeat=3)))*half
                elif mesh is not None:
                    from .motion_pipeline.model import mesh_vertices
                    corners=mesh_vertices(mesh_path(mesh.get('filename')))*np.fromstring(mesh.get('scale','1 1 1'),sep=' ')
                else:raise ValueError('Unsupported foot collision: provide a box or STL/OBJ contact hull')
                transform=origin_matrix(collision);points.extend(corners@transform[:3,:3].T+transform[:3,3])
            foot_corners[name]=np.asarray(points).tolist()
    assert set(joints) == set(ALL_JOINTS)
    for path in sorted((ROOT / "snu_gom_description/config").glob("*.csv")):
        hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    lowest = min(
        (np.array(foot_corners[name]) @ frames[name][:3, :3].T + frames[name][:3, 3])[:, 2].min()
        for name in FOOT_LINKS
    )
    return {
        "mass_kg": sum(masses.values()),
        "body_masses": masses,
        "inertias": inertias,
        "joints": joints,
        "policy_joint_order": LEG_JOINTS,
        "observation_joint_order": ALL_JOINTS,
        "foot_corners": foot_corners,
        "initial_height": float(-lowest + 0.003),
        "hashes": hashes,
    }
