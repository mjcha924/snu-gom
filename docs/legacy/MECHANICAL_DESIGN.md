# Mechanical architecture and V0.6 parameters

The design target is a compact teddy bear with a large low head, rounded torso, stubby visible limbs, and broad paws. Keep two mechanical joints per limb. The lower motor cases sit inside the paws; the corresponding horns connect to the upper carriers. No waist motor or passive ankle is part of this baseline.

The source for these dimensions is the saved V0.6 parameter file and construction code. They are a design reference, not approved manufacturing dimensions or measurements from the live [Onshape workspace](ONSHAPE.md). The old larger-width and rolling-paw candidates are not the intended appearance.

## Units and principal dimensions

CAD uses millimeters: +X forward, +Y left, +Z up. Listed X/Y/Z envelopes are local design dimensions; a posed assembly has different global bounds.

| Parameter | Value | Meaning |
| --- | --- | --- |
| `torso_xyz` | 82, 94, 104 mm | Outer rounded torso box |
| Torso inner box | 76, 88, 98 mm | Nominal 3 mm wall before openings |
| Torso outer/inner fillet radii | 31 / 28 mm | Construction radii |
| `head_xyz` | 112, 138, 114 mm | Main hollow ellipsoid; ears and muzzle extend it |
| Head inner ellipsoid | 106, 132, 108 mm | Axis radii reduced by 3 mm; not uniform normal wall thickness |
| `fore_lengths` | 40, 28 mm | Root-to-bend axis distance; model's lower-link reference length |
| `hind_lengths` | 34, 30 mm | Root-to-bend axis distance; model's lower-link reference length |
| `fore_paw_xyz` | 48, 50, 62 mm | Nominal paw envelope after the sole truncation, before inserts/cutouts |
| `hind_paw_xyz` | 52, 60, 66 mm | Nominal paw envelope after the sole truncation, before inserts/cutouts |
| Paw ellipsoid construction lengths | 68 mm front; 72 mm rear | Uncut local Z extent; topmost sole-side 6 mm is removed |
| Paw cavity radius reduction | 2.5 mm | Ellipsoid axis reduction, not uniform wall thickness |
| Paw sole slab | 4 mm | Nominal local slab before shape operations |
| Paw center local Z | +14 mm from bend axis | Rotates with the lower link |
| Motor case placeholder | 26 × 20 × 34 mm | Generic envelope, not a selected Dynamixel specification |
| Paw motor pocket | 27 × 21 × 35 mm | Nominal 0.5 mm per-side gap around that placeholder |
| Battery placeholder | 22 × 40 × 26 mm | Center at torso coordinates (−20, 0, +6) mm |

The lower-link reference length is not an ankle-to-toe distance: there is no ankle joint, and actual reach depends on the fixed paw surface and orientation. Paw pads, flattened soles, carrier slots and local cutouts affect contact and final bounds. Do not infer printing tolerances from these envelopes.

Machine-readable dimensions: [parameters.json](../motion/src/snu_bear_motion/data/robot/parameters.json).

## Joint origins

All nine revolute axes are pitch axes about local Y. Coordinates below are translations in each named parent frame, converted from the saved registry. The URDF also has nonzero origin rotations; translations alone do not define a complete joint frame.

| Joint | Parent | Origin X, Y, Z (mm) |
| --- | --- | --- |
| Neck pitch | Torso | 0, 0, +52 |
| Right shoulder pitch | Torso | +28, −40, +30 |
| Left shoulder pitch | Torso | +28, +40, +30 |
| Right hip pitch | Torso | −5, −38, −32 |
| Left hip pitch | Torso | −5, +38, −32 |
| Each elbow pitch | Corresponding front upper link | 0, 0, +40 |
| Each knee pitch | Corresponding hind upper link | 0, 0, +34 |

The head center is locally (0, 0, +57) mm from the neck frame. See the [joint registry](../motion/src/snu_bear_motion/data/robot/joint_registry.json) and [URDF](../motion/src/snu_bear_motion/data/robot/snu_bear_v06.urdf) for exact rotations and frame conventions. URDF zeros are not calibrated Dynamixel encoder zeros. Joint limits, motor efforts and inertias are provisional.

## Motion requirements and unresolved work

Everyday movement should use short lift-and-place steps, with a low body and modest weight shifts. The recorded V0.6 shuffle used 3 mm travel and 3 mm lift. A transition out of sitting may require larger joint excursions than the everyday shuffle.

The intended transition is to brace the hind paws, lean using the hips/knees, establish front contact and transfer support, then reach the low stance. A fixed-torso animation does not establish this process. The earlier V0.6 search did not establish a clear, statically supported sit-to-low path; later prescribed motion references also do not prove free-body dynamics. See the [historical feasibility report](V06_HISTORICAL_FEASIBILITY.md).

Before manufacturing, select actual motors/horns and bearings; detail fasteners, shaft support, covers, cable passages and assembly access; resolve tight neck/paw clearances; and validate loaded transitions with the revised masses, contacts and friction. Preserve the teddy silhouette when revising these relationships.
