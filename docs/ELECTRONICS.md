# Electronics development plan

The current architecture uses nine Dynamixel actuators, an onboard battery, a controller, joint feedback and an IMU. Exact parts have not been selected. Camera-free proprioceptive motion is the initial target.

| Subsystem | Intended responsibility | Open decision |
| --- | --- | --- |
| Battery and power distribution | Supply the actuator rail and logic power | Chemistry, cell count, capacity, regulator and current budget after actuator selection |
| Dynamixel communication | Send targets; receive position, velocity and available status | Exact model, TTL/RS-485 interface, IDs, bus rate and host adapter |
| Controller | Timestamp observations, run inference and supervise motion | Compute platform and interface to the motor bus |
| IMU | Body angular velocity and gravity-direction estimate | Sensor, mounting orientation, sampling/filtering and calibration |
| Actuator mounting/wiring | Fit motors, horns and cables into the compact limbs | Manufacturer geometry, cable travel and service access |

Do not infer supply voltage or torque capability from the CAD placeholder. The 22 × 40 × 26 mm battery box is reserved packaging space, not a selected battery. The simulation's 0.2 Nm effort cap, 1 rad/s slew limit and 50 Hz policy rate are exploratory settings, not hardware ratings.

The repository provides a transport interface and an unfilled [calibration template](../motion/examples/hardware_calibration.template.json). It does not include a verified Dynamixel driver for a selected model. Follow the [deployment contract](../motion/docs/DEPLOYMENT.md) after the mechanical and electrical baseline is measured.
