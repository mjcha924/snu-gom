# Proposed hip-roll link extension

November 17, 2026. **CAD screening only; no model changes or training.**

Start the next CAD revision with **6 mm additional outward spacing per side**.
This is a prototype dimension, not a fabrication-qualified design or proof of
walking. The user is revising the CAD before further training.

## Exactly what this assumes

Keep the hip-roll pivot fixed. Move the outer hip-pitch motor and the complete
downstream thigh assembly 6 mm farther away from the robot centerline at neutral,
by lengthening the connecting hip-roll bracket. Mirror the change on both sides.
The offset rotates with hip roll. This is not a 6 mm vertical extension, a
thickness increase, or uniform scaling of the existing mesh. Neutral leg spacing
would increase by approximately 12 mm overall under this assumption.

The observed interference is the **hip-yaw-link motor housing against the inner
thigh side plate**, not merely two motor housings touching. Both the motor and
plate positions must be considered when revising the assembly. If the intended
CAD edit moves components in a different direction, these dimensions do not apply.

## Measured spacing screen

The script rigidly translates the existing thigh assembly, without changing any
URDF/STL file. It queries all visual meshes of each hip-yaw/thigh link pair on
both sides, with hip roll from −20° to +20° and hip pitch from −45° to +45°.
These are the existing provisional joint ranges, not validated hardware limits.

Coarse grid: 5° roll increments, 15° pitch increments, 126 poses per extension.

| Added outward spacing per side | Minimum sampled visual-surface gap | Intersecting samples |
| --- | ---: | ---: |
| 0 mm | Intersection | 26 |
| 3 mm | Intersection | 4 |
| 4 mm | 0.73 mm | 0 |
| 5 mm | 1.73 mm | 0 |
| **6 mm** | **2.73 mm** | **0** |
| 8 mm | 4.73 mm | 0 |

[Complete coarse results](media/hip-spacing/screen.json).
The 6 mm candidate also passes all **1,558 poses** on a finer 1° roll / 5° pitch
grid, with a **2.728 mm** minimum gap. The worst sample is the left side at
−20° roll / −25° pitch, between the hip-yaw bracket and inner thigh plate.
[Complete fine results](media/hip-spacing/6mm-fine.json) preserve every sample.

Use **at least 2 mm clearance throughout the intended motion** as a preliminary
design target for this revision, not as a universal manufacturing allowance.
Choose the final allowance after considering the actual print tolerances,
assembly alignment, fasteners, wiring, and deflection. The 6 mm choice adds margin
over the 4–5 mm candidates without jumping directly to the wider 8 mm layout.

## What must still be checked in CAD

1. Sweep the complete assembly through roll and pitch combinations, including
   inward roll at 20° with negative pitch. Check both sides, not just neutral.
2. Check the newly lengthened bracket itself, motor horns, fasteners, wiring,
   torso, and opposite leg. The query here only checks the original hip-yaw/thigh
   mesh pairs; it does not model the redesigned bracket or guarantee continuous
   clearance between the discrete sampled angles.
3. Check stiffness and servo/bearing loading: longer offsets change leverage.
   No strength, compliance, or actuator-load validation is supplied by this scan.
4. Export the new meshes and URDF with correct joint origins, collision shapes,
   mass, center of mass, and inertia. Do not just move visuals or reuse old boxes.
5. Re-run geometry, standing, and free-base unloading/lift/landing diagnostics
   before PPO. More clearance removes one blocker, not the reward, balance,
   actuator-tracking, or foot-unloading problems. Old policy performance is not
   automatically preserved on the new geometry.

## Reproduce

Use the workspace Python environment and optional dependencies from
`requirements-collision-audit.txt`, as described in [flat recovery](flat-recovery.md).

```bash
python scripts/audit_hip_extension.py --output reports/hip-extension-screen.json
python scripts/audit_hip_extension.py --extensions-mm 6 --roll-step-deg 1 --pitch-step-deg 5 --output reports/hip-extension-6mm-fine.json
```

The explicit hypothetical translation is hip-roll-link local +X on the left and
−X on the right, expressed in the currently supplied URDF frames. The results
record input model hashes and the script hash. No simulator or optimizer runs.
