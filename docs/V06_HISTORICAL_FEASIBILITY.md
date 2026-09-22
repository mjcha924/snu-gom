# SNU Bear V0.6 — teddy proportions and motion study

**This revision gets substantially closer to the short-limb, big-paw target and supports a sampled short crawl. It does not yet establish a sitting-to-crawling transition.**

The key architecture change places each elbow/knee motor case in its paw, with the output horn attached to the upper carrier. The paw and case move as one lower link. The system still has exactly two pitch joints per limb, plus one neck pitch joint. There are no added passive ankles or wheels.

## Proportions and appearance

| Feature | V0.5 | V0.6 candidate |
|---|---:|---:|
| Shoulder-to-elbow spacing | 44 mm | 40 mm |
| Hip-to-knee spacing | 46 mm | 34 mm |
| Main head width | 128 mm | 138 mm |
| Torso W × D × H | 88 × 74 × 104 mm | 94 × 82 × 104 mm |
| Fore-paw outer envelope before local relief | 34 mm wide | 50 mm wide, 48 mm deep, 62 mm long |
| Hind-paw outer envelope before local relief | 42 mm wide | 60 mm wide, 52 mm deep, 66 mm long |
| Overall lateral envelope | — | About 188 mm |

The 60 mm hind-paw blank becomes approximately 55 mm wide after its inboard relief. The large paw encloses the lower mechanism, so exposed limb length is shorter than the complete kinematic chain. Lower-link reference distances of 28/30 mm locate a mathematical reference point, not an extra joint or the centre of the paw shell. The paw shell centre is 14 mm along its local Z axis from the bend axis.

A 32 mm front-link trial failed to solve the tested hand-placement paths. Increasing that spacing to 40 mm improved reach while retaining the large enclosing paw. Shoulder motor envelopes and service openings remain visible. This is actual CAD, not a cosmetic image substituted for the mechanism.

## What passed

- All ten rigid-link STL meshes have zero boundary or nonmanifold edges in the topology check.
- All 44 named CAD parts load as valid shapes. Endpoint STEP files contain the selected seated and low poses.
- Exact OpenCascade intersection checks found no interpenetration between different rigid links at either endpoint, and no endpoint ground penetration beyond the 0.05 mm numerical tolerance.
- A prescribed crawl cycle advances **3 mm**, lifting each paw **3 mm**. All **83 full-STL samples** have no detected surface intersections. Worst sampled floor error is -0.00096 mm, within the numerical floor tolerance.
- The body's pitch stays at **55°**, with no commanded body roll or yaw during the crawl. The maximum joint excursion is **11.69° peak-to-peak** during that cycle.
- Estimated mass is **664.8 g**. The smallest nominal support margin is **5.93 mm**. A vertical-reaction static equilibrium solution exists at all 83 crawl samples under the model assumptions.

These checks do not establish continuous swept-volume clearance, dynamic tracking or hardware performance. Full-mesh intersection checks test surfaces and are not a universal containment test. Exact solid checks cover the two endpoint configurations only.

## Sit-to-crawl result

**No connected, collision-free, statically supported path was found in the tested search families.** Both endpoint postures exist, but that does not prove a feasible connection.

The tests varied grounded seated hind-paw placement, hand landing position, body lean, and hand-height detours. The recurring failures were forepaws intersecting the large hind paws during lowering, or the projected centre of mass leaving the seated support region before the forepaws landed. Some target poses were unreachable. The stored search failures are evidence about these particular candidates, not a proof that the architecture is impossible.

The animation **starts in the low stance**. It does not depict a transition from sitting. The V0.5 transition validation must not be carried into this revision.

## Margins that prevent a build-ready claim

- **Neck clearance is too tight for a hardware design:** the smallest exact endpoint separation is only **0.107 mm**, between the torso and head in the low posture. It requires more clearance before manufacturing.
- **Balance remains sensitive:** 200 independent ±20% rigid-link mass trials at each crawl pose produced a smallest support margin of only **0.221 mm**. These random trials are not a worst-case uncertainty bound and do not vary mass placement, friction or pad compression.
- The peak of the optimistically allocated static gravity torque is **0.097 N·m**. This is not a continuous actuator rating or an actuator selection result.
- The base pose is prescribed. Friction, slip, contact compliance, disturbances, thermal limits and free-body dynamics were not simulated or tested on hardware.
- Motor cases are 26 × 20 × 34 mm envelopes. Manufacturer-specific mounting holes, output geometry, connectors, supported bearings, wire clearance, shell joints and structural strength remain unqualified. Paws currently need real motor retention and load-bearing interfaces.

## Files and reproduction

See README.md for file units and source commands. `poses.json` identifies the two exported endpoint configurations. `endpoint_exact_checks.json` records their exact solid checks. `crawl_full_mesh_checks.json`, `crawl_checks.json`, and `crawl_statics.json` document the short gait. `transition_search_result.json` and `transition_search_detour.json` record failed bounded searches. `SHA256SUMS.txt` records release bytes.

The most direct next mechanical problem is the forepaw landing phase with the hind paws already planted. Solve that together with the neck clearance before treating this candidate as a complete robot architecture.
# Historical record — V0.6 full CAD bundle

The following report is preserved from the earlier full geometry bundle. Its relative source/output paths refer to that bundle, whose CAD and evidence files are not included in this GitHub upload. These earlier sampled results are not a new validation of the live Onshape workspace or proof of dynamic motion. See [current repository scope](VALIDATION.md).
