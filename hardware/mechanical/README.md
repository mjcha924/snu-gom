# Mechanical CAD / 기구 CAD

**v0.3 · paper-informed shell and skeleton prototypes · units mm**

The full CAD delivery archive is `SNU_GOM_CAD_Shell_Skeleton_v03.zip` (SHA-256 recorded in [`cad_manifest.json`](cad_manifest.json)). It was shared with the project owner in the project conversation; this public repository currently contains the design documentation and kinematic frames, not the large binary STEP archive.

## Start here / 먼저 볼 파일

| Need / 목적 | File / 파일 |
| --- | --- |
| Understand the joints and geometry / 축·기구 이해 | [CAD geometry / CAD 형상](../../docs/CAD_GEOMETRY.md) |
| Compare shell and skeleton / 외장형·골격형 비교 | [Paper-informed design / 논문 반영](../../docs/PAPER_DESIGN.md) |
| Check STEP round-trip and collisions / STEP·간섭 검사 | [CAD verification / CAD 검사](../../docs/CAD_VERIFICATION.md) |
| Machine-readable axes / 기계 판독 관절 좌표 | [`joint_frames_v03.json`](joint_frames_v03.json) |

## Models in the delivery archive / 전달 패키지 모델

| Model | STEP file | Valid solids | Neutral bounds X × Y × Z (mm) |
| --- | --- | ---: | ---: |
| Full shell / 전체 외장형 | `SNU_GOM_full_shell_assembly.step` | 249 | 123.346 × 222 × 366 |
| Full skeleton / 전체 골격형 | `SNU_GOM_skeleton_assembly.step` | 183 | 107 × 154 × 309.5 |
| Paired legs, shell / 양쪽 다리 외장형 | `SNU_GOM_leg_pair_shell.step` | 193 | 94 × 158 × 204.85 |
| Paired legs, skeleton / 양쪽 다리 골격형 | `SNU_GOM_leg_pair_skeleton.step` | 161 | 88 × 154 × 202.85 |
| One left leg, shell / 왼쪽 한 다리 외장형 | `SNU_GOM_left_leg_5DOF_shell.step` | 96 | 94 × 70 × 198.5 |
| One left leg, skeleton / 왼쪽 한 다리 골격형 | `SNU_GOM_left_leg_5DOF_skeleton.step` | 80 | 88 × 66 × 196.5 |

Both legs use five supplied XL330-M288-T motor/horn assemblies in this order: **hip roll → hip pitch → knee pitch → ankle pitch → ankle roll**. The shell model adds link-mounted removable panels, neutral sleeve envelopes across joint gaps, rear cable-channel space and replaceable paw-pad samples. The skeleton exposes the bracket/link load path. The full-body models retain the additional neck-pitch motor.

The geometry follows lessons from BD-X (design character motion and mechanics together) and Olaf (cover motion, impact, service and temperature matter). The neutral sleeves are not a validated flexible cover, actual wires are not modeled, and neither model is fabrication-qualified or a walking validation.

**Checks:** all six exported STEP files re-imported with valid solids. The 26-pose bilateral screen identified two isolated inward hip-roll samples with foot intersections. Planning mass is estimated, not weighed. See the verification note before using any pose or load estimate.

**Current constraints:** The existing URDF is still an earlier ten-leg-joint proxy and is not synchronized with this eleven-motor CAD. Do not infer servo limits or command directions from STEP geometry.
