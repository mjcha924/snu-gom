# Policy interface and hardware integration

Policies are fixed learned weights at deployment, but recompute actions from feedback every cycle. Only selection, signal processing, coordinate conversion and limits are conventional software. There is no baked-in sit-to-crawl motor trajectory.

## Observation contract

One frame has 34 float32 values. Stack four frames, oldest first, to produce 136 inputs. On startup or a policy switch, repeat the first fresh frame four times. Preserve the last commanded target across policy switches.

| Indices within a frame | Signal | Preprocessing |
|---|---|---|
| 0–8 | Joint position, URDF radians | `(q - midpoint) / half_range` |
| 9–17 | Joint velocity, rad/s | Multiply by 0.5 |
| 18–20 | Angular velocity in torso frame, rad/s | Multiply by 0.25 |
| 21–23 | Unit gravity direction in torso frame | Normalize; upright sitting is `[0,0,-1]` |
| 24–32 | Previous commanded joint target | Same midpoint/half-range normalization |
| 33 | Forward speed request, m/s | Divide by 0.03; use zero for non-crawl skills |

Joint order: neck, right fore root/bend, left fore root/bend, right hind root/bend, left hind root/bend. The exact strings appear in `contract.json`. IMU orientation must be transformed into the torso frame (+X forward, +Y left, +Z up). Gravity is an attitude-estimator output; raw accelerometer readings include motion and use different units.

No camera, global position, base linear velocity estimate or paw force sensor is required by this initial actor interface. Training does use simulator contact and velocity information for rewards. The encoder/IMU posture guard therefore cannot independently certify contact support on hardware.

## Action contract

Each of nine outputs is clipped to `[-1, 1]`. Convert it to an absolute URDF position target with the shared joint midpoint and half-range, then apply the 1 rad/s target slew limit at 50 Hz. This exact mapping runs in simulation and `PolicyController`. It is not an offset around the current pose.

The envelope was taken from the earlier kinematic candidate plus 15° margin. It must be replaced by measured collision-free mechanical travel as the robot is finalized. Changes require retraining/re-evaluation. The original URDF ±π limits are placeholders; they are not servo travel calibration.

## Selection behavior

`SkillSelector.request("sit" | "low" | "crawl")` sets the requested behavior. `update()` returns the skill to run. Switching away from a hold posture requires 0.5 seconds within the measured joint/attitude/velocity region. A crawl-to-sit request first selects `hold_low`, waits for settling, then selects `low_to_sit`. A request during a transition takes effect after that transition settles. A transition timeout raises a fault instead of selecting an incompatible pose.

`PolicyController` checks missing policies, finite values, basic joint envelope, sensor freshness, increasing timestamps and timing. It maintains observation history and bounded targets. These software checks have CPU tests. They do not constitute robot-level fault protection.

## Connect the actual motors

Fill `examples/hardware_calibration.template.json` using the installed servo model and measurements. `zero_tick` is the encoder coordinate corresponding to URDF joint position zero; it can be an extrapolated calibration intercept if that neutral pose is outside usable travel. `direction` must be +1 or −1. Tick resolution and travel depend on the selected servo and operating mode.

Implement `Transport.read_state`, `write_goal_ticks`, and `stop` for that servo's SDK and IMU. The transport must map positions and velocities to the specified units, enforce the measured current/effort/profile limits, timestamp synchronized sensor samples using the controller's monotonic clock, and implement the robot's tested fault response. No serial protocol or motor register addresses are guessed here.

`examples/controller_loop.py` shows where the transport, selector and policies connect. It opens no hardware by itself. The included calibration template is intentionally unfilled, and the registry refuses missing checkpoint files. The example expects all five policies to exist; for isolated supervised tests, instantiate `PolicyController` with only the needed skill.

Bench-measure the servo's response before relying on the simulated delayed-PD model. A position-controlled Dynamixel is not guaranteed to reproduce ideal PD effort clipping, regardless of matching position commands. Use measured response, communication timing, limits and total mass distribution in the training model.
