"""Small static home scene built entirely from inexpensive primitive shapes."""

import isaaclab.sim as sim_utils


def build_home(path):
    parts = [
        ("back_wall", (0.08, 3.0, 1.2), (2.8, 0.0, 0.6), (0.65, 0.68, 0.70)),
        ("side_wall", (4.0, 0.08, 1.2), (0.8, 1.5, 0.6), (0.65, 0.68, 0.70)),
        ("sofa_seat", (1.2, 0.45, 0.3), (1.2, -1.15, 0.15), (0.22, 0.38, 0.45)),
        ("sofa_back", (1.2, 0.12, 0.45), (1.2, -1.36, 0.35), (0.22, 0.38, 0.45)),
        ("table_top", (0.8, 0.55, 0.05), (1.4, 1.05, 0.65), (0.45, 0.29, 0.16)),
        ("table_leg_1", (0.06, 0.06, 0.62), (1.07, 0.84, 0.31), (0.35, 0.23, 0.13)),
        ("table_leg_2", (0.06, 0.06, 0.62), (1.73, 0.84, 0.31), (0.35, 0.23, 0.13)),
        ("table_leg_3", (0.06, 0.06, 0.62), (1.07, 1.26, 0.31), (0.35, 0.23, 0.13)),
        ("table_leg_4", (0.06, 0.06, 0.62), (1.73, 1.26, 0.31), (0.35, 0.23, 0.13)),
    ]
    for name, size, position, color in parts:
        config = sim_utils.CuboidCfg(
            size=size,
            collision_props=sim_utils.CollisionPropertiesCfg(contact_offset=0.001, rest_offset=0.0),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color, roughness=0.9),
        )
        config.func(f"{path}/{name}", config, translation=position)
    rug = sim_utils.CuboidCfg(
        size=(1.8, 0.9, 0.001),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.34, 0.30, 0.24), roughness=1.0),
    )
    rug.func(f"{path}/visual_rug", rug, translation=(0.9, 0.0, -0.0005))
