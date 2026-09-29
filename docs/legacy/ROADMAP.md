# Development roadmap

## 1. Establish the hardware baseline

- Select the exact Dynamixel models and obtain their current mechanical drawings.
- Detail paw-mounted bend-motor retention, upper carriers, horns and bearings.
- Resolve tight neck/paw clearances and define manufacturing tolerances.
- Detail the battery, power distribution, controller, IMU and cable routing.
- Measure or update mass, center of mass, inertia, travel and motor direction.

Deliverable: an assembled and serviceable mechanical revision with a matching simulation model.

## 2. Validate the simulator model

- Install the targeted Isaac Lab / Isaac Sim environment.
- Import the URDF and inspect collision shapes, inertia, contact and joint axes.
- Run both hold-skill smoke checks.
- Compare simulated motor response with measured servo behavior.

Deliverable: reproducible import and physics checks with recorded software versions.

## 3. Train and evaluate the five initial skills

Train hold sitting, hold low, sit to low, low to sit and crawl forward. Record success rates, falls, contact behavior, tracking, torque/speed limits and robustness to parameter variation. Establish whether the current nine-joint hardware supports each goal before assuming an additional motor is needed or unnecessary.

Deliverable: actual trained checkpoints and evaluation records tied to a robot revision.

## 4. Integrate the robot

- Implement the transport for the selected servos.
- Fill the calibration template from measurements.
- Validate observation timing, coordinate conventions and policy outputs.
- Evaluate individual skills and then skill handoffs on the assembled robot.

Deliverable: repeatable demonstrations and an updated policy registry.

Turning, recovery, expressive gestures and broader autonomous behavior follow the initial five-skill baseline.
