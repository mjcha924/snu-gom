# SNU Bear CAD workspace

**[Open the shared SNU Bear Onshape document](https://cad.onshape.com/documents/70e60901c3f0fdac6b9cd14a/w/8da76927eccdd278710924b6/e/0a419943727577ede2a57301)**

Use this document for CAD inspection and team refinement. Access follows the document's existing sharing settings. The supplied URL points to a mutable workspace, not a frozen version; no changes to the Onshape document were made during this GitHub upload.

STEP, STL, BREP and other geometry files are omitted from this repository. The saved V0.6 [dimensions](MECHANICAL_DESIGN.md) and [joint registry](../motion/src/snu_bear_motion/data/robot/joint_registry.json) are reference metadata, not a verification of the current Onshape workspace.

## Assembly relationships

1. Ground the torso. Root motor cases, battery and torso-mounted electronics belong to that rigid group.
2. Each upper carrier is a separate moving link.
3. Each paw, pads and elbow/knee motor case form one lower moving link.
4. Use eight limb revolute mates and one neck pitch mate. A positioned STEP import does not provide these mates automatically.
5. Use the joint registry to inspect axis locations and neutral-frame offsets. Physical motor zeros and allowable travel must come from hardware calibration.

Work in millimeters for mechanical design, with +X forward, +Y left and +Z up. Simulation uses meters and link-local mesh frames.

For each mechanical revision, create an Onshape version, record its link in the related PR, and explain which dimensions, masses, joint frames and motion assumptions changed. Check swept motion and ground contact before declaring a new revision feasible. Coordinate any later geometry upload separately; this release uses the Onshape link in place of CAD files.
