"""Generate an explicitly unvalidated, primitive 10-DOF biped URDF."""
from pathlib import Path
import json
import math
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'robot/config.json'
OUTPUT = ROOT / 'robot/snu_gom.urdf'
ORDER = [f'{side}_{joint}' for side in ('left', 'right') for joint in
         ('hip_roll', 'hip_pitch', 'knee_pitch', 'ankle_pitch', 'ankle_roll')]


def load_config(path=CONFIG):
    config = json.loads(Path(path).read_text())
    validate_config(config)
    return config


def validate_config(config):
    joints = config['joints']
    if [j['name'] for j in joints] != ORDER:
        raise ValueError('Expected canonical 10-joint left-then-right order')
    ids = [j['logical_motor_id'] for j in joints]
    if any(type(i) is not int or not 1 <= i <= 252 for i in ids) or len(set(ids)) != 10:
        raise ValueError('Motor IDs must be ten unique integer IDs in 1..252')
    if config['motor'] != 'XL330-M288-T':
        raise ValueError('Change the design decision before changing actuator model')
    for key, value in config['dimensions_m'].items():
        if not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f'Invalid dimension {key}')
    if not math.isfinite(config['base_height_m']) or config['base_height_m'] <= 0:
        raise ValueError('Invalid base height')
    for value in config['simulation_only'].values():
        if not math.isfinite(value) or value <= 0:
            raise ValueError('Invalid simulation limit')
    for i, j in enumerate(joints):
        expected = [1, 0, 0] if i % 5 in (0, 4) else [0, 1, 0]
        if j['axis'] != expected:
            raise ValueError(f"Unexpected axis for {j['name']}")
        lo, hi = j['lower_rad'], j['upper_rad']
        if not all(math.isfinite(v) for v in (lo, hi)) or not lo < hi or not lo <= 0 <= hi:
            raise ValueError(f"Invalid limits for {j['name']}")


def xyz(values):
    return ' '.join(f'{v:.8g}' for v in values)


def build(config):
    validate_config(config)
    robot = ET.Element('robot', name=config['revision'])
    robot.append(ET.Comment('GEOMETRY PROXY ONLY. Coincident axes, masses, inertia and limits are assumptions. Not manufacturing CAD or a validated walking robot.'))

    def link(name, mass, size, center=(0, 0, 0), color='0.91 0.82 0.68 1'):
        node = ET.SubElement(robot, 'link', name=name)
        inertial = ET.SubElement(node, 'inertial')
        ET.SubElement(inertial, 'origin', xyz=xyz(center))
        ET.SubElement(inertial, 'mass', value=str(mass))
        x, y, z = size
        ET.SubElement(inertial, 'inertia', ixx=str(mass*(y*y+z*z)/12),
                      iyy=str(mass*(x*x+z*z)/12), izz=str(mass*(x*x+y*y)/12),
                      ixy='0', ixz='0', iyz='0')
        for kind in ('visual', 'collision'):
            element = ET.SubElement(node, kind)
            ET.SubElement(element, 'origin', xyz=xyz(center))
            ET.SubElement(ET.SubElement(element, 'geometry'), 'box', size=xyz(size))
            if kind == 'visual':
                material = ET.SubElement(element, 'material', name=name+'_color')
                ET.SubElement(material, 'color', rgba=color)
        return node

    def joint(name, parent, child, origin, spec=None):
        node = ET.SubElement(robot, 'joint', name=name, type='revolute' if spec else 'fixed')
        ET.SubElement(node, 'parent', link=parent)
        ET.SubElement(node, 'child', link=child)
        ET.SubElement(node, 'origin', xyz=xyz(origin), rpy='0 0 0')
        if spec:
            ET.SubElement(node, 'axis', xyz=xyz(spec['axis']))
            ET.SubElement(node, 'limit', lower=str(spec['lower_rad']), upper=str(spec['upper_rad']),
                          effort=str(config['simulation_only']['effort_Nm']),
                          velocity=str(config['simulation_only']['velocity_rad_s']))
            ET.SubElement(node, 'dynamics', damping='0.02', friction='0.01')

    dims = config['dimensions_m']
    # Mass budget: base 208g + head 60g + arms 20g + legs 312g = 600g.
    link('base_link', .208, (.07, .095, .07), (0, 0, .04))
    head = link('head', .06, (.085, .11, .08))
    # Ears are visual decorations; their estimated mass is included in the head.
    for side in (-1, 1):
        visual = ET.SubElement(head, 'visual')
        ET.SubElement(visual, 'origin', xyz=xyz((0, side*.041, .045)))
        ET.SubElement(ET.SubElement(visual, 'geometry'), 'sphere', radius='.015')
    joint('head_fixed', 'base_link', 'head', (0, 0, .13))
    for side, sign in [('left', 1), ('right', -1)]:
        link(side+'_arm', .01, (.035, .025, .05))
        joint(side+'_arm_fixed', 'base_link', side+'_arm', (0, sign*.064, .04))
        a, b = dims['thigh'], dims['shin']
        names = [side+'_hip_carrier', side+'_thigh', side+'_shin', side+'_ankle_carrier', side+'_foot']
        sizes = [(.02,.025,.02), (.028,.025,a), (.028,.025,b), (.02,.025,.02),
                 (dims['foot_length'],dims['foot_width'],dims['foot_height'])]
        centers = [(0,0,0), (0,0,-a/2), (0,0,-b/2), (0,0,0), (.01,0,-.015)]
        origins = [(0,sign*dims['hip_spacing']/2,0), (0,0,0), (0,0,-a), (0,0,-b), (0,0,0)]
        specs = [j for j in config['joints'] if j['name'].startswith(side+'_')]
        parent = 'base_link'
        for name, size, center, origin, mass, spec in zip(names,sizes,centers,origins,[.018,.04,.04,.018,.04],specs):
            link(name,mass,size,center)
            joint(spec['name'],parent,name,origin,spec)
            parent = name
    ET.indent(robot, space='  ')
    return ET.tostring(robot, encoding='unicode', xml_declaration=True)+'\n'


if __name__ == '__main__':
    OUTPUT.write_text(build(load_config()))
    print(f'Generated {OUTPUT.relative_to(ROOT)} (unvalidated geometry proxy)')
