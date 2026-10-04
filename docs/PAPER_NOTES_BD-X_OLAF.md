# BD-X and Olaf: paper guide / BD-X·Olaf 논문 읽기 안내

Use this guide to understand what the robots did, how they were controlled, what the experiments establish, and which lessons transfer to SNU GOM. The numbers describe the authors' robots and tests; they are not SNU GOM specifications.

원문 전체를 읽지 않아도 두 로봇의 설계·제어·실험 결과와 SNU GOM에 적용할 점을 파악할 수 있게 정리했습니다. 수치와 성능은 논문 저자들의 로봇·시험 조건에 해당하며 SNU GOM의 사양이 아닙니다.

## At a glance / 한눈에 보기

| | BD-X | Olaf |
| --- | --- | --- |
| The creative brief / 목표 | Invent a new expressive bipedal robot character. | Bring an existing animated, non-robotic character into the physical world. |
| Appearance / 외형 | Purpose-built robot with painted outer shells. | Snowman silhouette; a stretch-fabric costume and compliant foam skirt hide the legs. |
| Leg layout / 다리 | 5 axes per leg: hip yaw, hip roll, hip pitch, knee pitch, ankle pitch. No active ankle roll; rounded foam soles allow passive roll. | 6 axes per leg, asymmetrically packaged so the legs can work inside a tight body envelope. |
| Learning contribution / 학습 | Shows why phase, contacts and motion references matter for characterful walking. | Adds measured temperature and impact reduction to animation tracking; tests quieter steps and thermal limits on hardware. |
| Human interaction / 상호작용 | Human puppeteer chooses commands and animations; no autonomous perception/dialogue demonstration. | Human puppeteer selects animations and walking/head commands; no autonomous perception/dialogue demonstration. |

The papers complement each other. **BD-X is the closer reference for designing a new robotic character and its motions together. Olaf is the closer reference for concealing mechanisms and treating fabric, sound and heating as part of the robot.** Neither paper is a controlled user study comparing exterior styles.

두 논문은 서로 보완적입니다. **새 캐릭터의 기구와 동작을 함께 설계하는 점은 BD-X**, **기구 은폐·천·발소리·발열을 함께 다루는 점은 Olaf**가 SNU GOM에 더 직접적입니다. 외형 선호도를 비교한 통제 사용자 실험은 두 논문 모두 하지 않았습니다.

## 1. BD-X — Design and Control of a Bipedal Robotic Character

**Grandia et al., Robotics: Science and Systems (RSS), 2024.** [Official paper and video](https://la.disneyresearch.com/publication/design-and-control-of-a-bipedal-robotic-character/) · [RSS proceedings page](https://www.roboticsproceedings.org/rss20/p103.html) · [Proceedings PDF](https://www.roboticsproceedings.org/rss20/p103.pdf).

### The problem they solve

A robot can walk dynamically and still fail to read as a character. The authors therefore make **expressive, artist-directed movement and robust balance joint goals**. Their central design idea is a loop: explore the character's proportions and motion in animation; build a mechanism that can reach those poses; simulate that mechanism and its actual actuators; train policies to track the authored motion while retaining the ability to balance and recover.

This makes animation references part of the engineering process. They are not simply decoration placed on a finished robot, and the learned controller is not a movie of fixed joint angles: it can depart from the reference when the simulated robot needs to recover.

### What they built

The robot is about **0.66 m tall and 15.4 kg**. It has five active axes per leg—**hip yaw, hip roll, hip pitch, knee pitch and ankle pitch**—and a four-axis neck/head. Actuators sit at the joints, with custom 3D-printed connectors between them. The knees bend backward to fit the intended character. The ankles have no active roll motors; rounded urethane-foam soles permit some passive roll and soften contact. Painted shells cover the mechanism. It also has actuated antennas, illuminated eyes, a headlamp and speakers.

That five-axis count is easy to misread for SNU GOM. **SNU GOM's proposed chain is hip roll, hip pitch, knee pitch, ankle pitch and ankle roll. It omits hip yaw and actively rolls the foot.** Those layouts have different turning, balance and packaging behavior even though each has five actuators.

### How its motion system works

The authors separate movement into three useful families:

1. **Perpetual:** ongoing standing, balance and continuous posture/gaze commands.
2. **Periodic:** walking driven by a gait phase and path/velocity commands.
3. **Episodic:** timed expressive clips such as a nod, jump, excited motion or dance.

For walking, animators provide gait examples at several speeds. A trajectory tool combines them and a model-based planner turns torso and foot paths into whole-body joint references. An animation engine blends an always-on idle layer, triggered clips, and joystick input. The operator can steer the gaze while adjusting posture, or trigger a stylized response while the robot stays balanced.

The policy observes the robot's body pose and velocity, joint positions and velocities, previous actions, motion phase and commands. It outputs **joint-position targets**; lower-level PD controllers drive the motors. The reward combines tracking of torso and joint motion, foot contact, survival, and penalties for torque and abrupt actions. During training, they perturb mass, friction, actuator parameters, sensor state, pushes and walking terrain so the controller does not see one perfect simulation only.

Their learned policy runs at 50 Hz and actuator communication at 600 Hz on that robot. The authors interpolate and filter between policy updates. These are implementation details for their hardware, **not rates to copy for XL330s**.

### The most useful experiment: why style needs a reference

The walking ablation is a useful lesson for SNU GOM. A policy rewarded mainly for matching commanded torso velocity, without gait phase, leg tracking and foot-contact reward, rapidly shuffles its feet. Giving it phase and expected contacts produces a clearer step pattern, but the torso remains stiff and upright because velocity tracking still dominates. Tracking authored kinematic references yields the intended whole-body style while preserving the balance objective.

The practical point is not that imitation alone solves walking. **A reference says what the movement should feel like; contact and dynamics say what the robot can do; the controller needs both.** During disturbances the paper's controller can deviate from the reference and contact schedule to recover. The paper also delays walking-to-standing transitions until both feet are on the ground (double support), avoiding a switch halfway through a swing step.

On the authors' robot they report walking up to 0.7 m/s forward, 0.4 m/s lateral and 1.8 rad/s turning, plus several timed expressive behaviors. They show pushes and small obstacles. Those results use their 15.4 kg robot and stronger actuators; they do not show that SNU GOM's XL330 design can reach those speeds or jump. Their deployed performances were puppeteered. The paper reports roughly ten hours of public runtime without a fall, but does not establish autonomous social intelligence or a controlled audience-preference result.

### What to take to SNU GOM

- Author simple bear-specific references before training: relaxed stand/look, a small weight shift, and a short step with a deliberate touchdown.
- Track torso orientation and feet as well as joint angles; keep balance/contact objectives able to override style when needed.
- Treat standing, periodic walking and a greeting clip as separate behavior types. Blend commands safely and transition near double support where the gait allows it.
- Identify XL330 actuator behavior first. BD-X's identified Dynamixel example is **XH540-V150**, not XL330-M288-T; its gains and torque model cannot be assigned to our motors.
- Don't use five joints as a reason to copy its hip-yaw/no-ankle-roll topology. Compare both chains in a matching SNU GOM simulator first.

## 2. Olaf — Bringing an Animated Character to Life in the Physical World

**Müller et al., arXiv:2512.16705v2, revised 2 April 2026.** [Paper (version 2)](https://arxiv.org/abs/2512.16705v2) · [HTML version](https://arxiv.org/html/2512.16705v2).

### The problem they solve

Olaf's cartoon proportions, snowball body and implied hidden legs do not fit a conventional biped. The team deliberately puts character resemblance ahead of compact engineering or energy efficiency. They first design the core articulated system—legs and neck—then add lower-inertia expressive parts such as eyes, jaw and arms with separate classical controls. They iterate the design and motion together.

### How the mechanism fits inside the character

The published robot is **88.7 cm tall without hair, 14.9 kg and 25 DoF**. Each leg has six DoF. To pack the legs and avoid hip-roll and knee collisions as the legs yaw, the left and right mechanisms are asymmetric: one side places the hip-roll actuator rearward and knee forward, the other reverses those directions. The legs are built as identical part designs in different orientations rather than mirrored part sets. This is a packaging solution for Olaf's bounded snowball silhouette, not a universal improvement to biped legs.

The skirt is not just an opaque plastic shell. A flexible polyurethane-foam skirt keeps a rounded lower silhouette while deflecting for larger steps and recovery movements. Foam feet soften contact. A four-way stretch fabric costume follows body motion; snaps and magnets retain removable costume features. Arms, facial parts and other details use remote linkages or breakaway magnetic attachments. The team explicitly manages forces from the fabric on moving parts.

### What changes in their reinforcement learning

Like BD-X, the policy tracks animation-derived target motion and sends joint-position targets to PD controllers. The task is divided into standing and phase-conditioned walking. The observations include body/joint state, previous actions and motor temperatures; the walking controller also receives gait phase. Rewards cover imitation, smoothness/effort, joint limits, foot-foot collisions and impact reduction.

Two additions matter for our design:

- **Foot-impact reward:** penalize rapid changes in foot vertical velocity at contact. In the authors' five-minute hardware test, it reduced mean sound level by **13.5 dB**, while most of the reference tracking was preserved. This is a result for Olaf's foam feet, speed, microphone setup and test environment—not a promise that our pads will make SNU GOM 13.5 dB quieter.
- **Thermal-aware neck control:** the large head and slim costumed neck caused overheating. They fit a simple first-order temperature model, approximately `temperature change = cooling toward ambient + heating proportional to torque²`. They add temperature to the policy state and penalize predicted violation of a control-barrier condition as a reward term. In plain language, as a motor approaches its chosen temperature bound, the policy learns to ease effort or tracking to let it cool.

For their neck setup, the chosen target bound was **80°C**. The thermal model's mean absolute error was reported as 1.87°C on a ten-minute validation rollout. In a one-hour run with thermal reward, the final-minute mean was 77.3°C, with 0.14 rad mean absolute joint-tracking error. The comparison without the thermal reward heated the neck rapidly and the authors stopped it. **The 80°C setting and fitted model belong to Olaf's actuators and costume. They must not be used as XL330 limits.** A reward penalty also is not a hard hardware safety cutoff by itself.

Their learning runs used thousands of parallel Isaac Sim environments and a high-end GPU for about two days in the reported setup. That demonstrates their workflow, not a training-time guarantee for a different robot or simulator.

### What to take to SNU GOM

- Keep a removable serviceable shell; if a continuous soft layer is desired, model it as fabric/foam with slack and test its pull, fold, ventilation and cable interactions. A neutral STEP envelope cannot predict those forces.
- Choose foot-pad material by measuring slip, compression, wear and sound. Couple the pad experiment with a controlled walking-speed/contact test.
- Record each motor's temperature and current during head holds and expressive movement. Identify the XL330's own heating/cooling response and enforce a local stop/warning limit based on the manual and bench tests.
- Add foot-foot collision checks and smooth touchdown objectives to simulation, but keep explicit geometry clearance. A reward cannot make two CAD parts occupy the same space safely.
- Separate dynamic balance/locomotion from low-inertia HRI show functions. A dialogue/API layer can request a bounded greeting or look behavior; it should not directly stream arbitrary leg angles or set gait timing over a network.
- Olaf's asymmetric six-DoF legs are not copied into the current five-motor SNU GOM. They solve a different silhouette and workspace problem.

## How to read the two papers selectively / 빠르게 읽는 순서

- **BD-X:** p. 3 for co-design and mechanism; pp. 4–6 for motion types, rewards, policy and actuator simulation; pp. 8–9 for walking ablation, deployment and puppeteering. Appendix B explains why actuator identification matters.
- **Olaf:** pp. 2–3 for project goal and asymmetric legs/costume; pp. 4–5 for policy, impact and thermal method; pp. 6–7 for training and hardware results.
- When watching either video, ask: which motions are authored, which are generated online, what state feedback keeps the robot upright, and who decides when to act? In both papers an operator puppeteers the performances. This is not a demonstration of autonomous camera-and-microphone conversation.

## 한국어 요약

### BD-X

BD-X는 **새 로봇 캐릭터를 만드는 프로젝트**입니다. 약 66 cm·15.4 kg이며 다리마다 고관절 요·롤·피치, 무릎 피치, 발목 피치의 5축과 4축 목/머리를 가집니다. 발목 롤 모터는 없고 둥근 우레탄 폼 발이 수동 기울어짐과 충격 완화를 맡습니다. 페인트된 외장이 내부 기구를 가립니다.

저자들은 애니메이션에서 비율과 동작을 먼저 탐색하고, 기구 설계와 보행 참조를 반복해서 맞춘 다음 시뮬레이터와 실제 모터 응답을 포함해 RL을 학습합니다. 정책은 몸통·관절 상태와 동작 참조·보행 위상·발 접촉을 보고 관절 위치 목표를 출력하며 PD 제어기가 모터를 움직입니다. 서기·주기 보행·일회성 표현 동작을 별도 유형으로 다루고, 애니메이션 엔진이 배경 동작·트리거 클립·조종 입력을 합칩니다.

핵심 보행 실험은 **빠른 걸음만 보상하면 발을 셔플하고, 위상/접촉만 더하면 걸음은 생기지만 몸통이 굳고, 전체 동작 참조를 추적해야 캐릭터 스타일을 얻는다**는 점입니다. 외란이 오면 균형을 위해 참조에서 벗어날 수도 있습니다. 보행 종료는 양발이 지면에 닿는 이중 지지 시점까지 기다립니다. 영상 시연은 조종자가 수행했으며 자율 시각·음성 인식은 구현하지 않았습니다.

SNU GOM에는 표정 있는 참조 동작과 접촉·균형 목표를 같이 두는 방법이 유용합니다. 다만 BD-X의 고관절 요/수동 발목 롤과 SNU GOM의 능동 발목 롤은 서로 다른 축 구성입니다. BD-X에서 식별한 XH540 모터 모델을 XL330에 복사해서는 안 됩니다.

### Olaf

Olaf는 **기존 애니메이션 캐릭터를 현실에 옮기는 프로젝트**입니다. 88.7 cm·14.9 kg·25축이며 다리당 6축입니다. 좁은 몸통 안에서 다리가 요 회전할 때 부딪히지 않도록 좌우 고관절 롤/무릎의 앞뒤 방향을 비대칭으로 배치했습니다. 양쪽은 서로 거울 부품으로 만들지 않고 같은 부품을 방향만 달리 조립합니다.

하체는 플라스틱 통이 아니라 **눌리고 휘는 PU 폼 스커트**, 폼 발, 신축성 4방향 천으로 가립니다. 의상과 움직이는 턱 등에 걸리는 힘을 고려합니다. 즉, 외피는 단순 미관 부품이 아니라 운동 공간·충격·마찰·발열 조건의 일부입니다.

제어는 애니메이션 모방·부드러운 동작·관절 한계에 **발 충격 저감과 온도 목표**를 추가합니다. 발의 수직 속도가 착지 순간 급변하지 않도록 보상해 실제 5분 시험에서 평균 소음을 13.5 dB 낮췄습니다. 큰 머리 때문에 목 액추에이터가 뜨거워져 온도를 관측에 넣고 간단한 발열/냉각 모델과 제어 장벽 조건 위반 보상을 사용합니다. 80°C는 Olaf 설정값입니다. 온도 보상 없는 비교는 빠르게 과열되어 시험을 중단했고, 보상이 있을 때 1시간 후 마지막 1분 평균은 77.3°C, 관절 추종 오차는 0.14 rad였습니다. XL330에 이 임계값이나 모델을 그대로 옮기면 안 됩니다.

SNU GOM에는 패드·폼·천을 실제로 측정하고, 모터 온도·전류를 기록하며, 기구 간섭은 보상뿐 아니라 CAD에서 해결하는 교훈이 있습니다. API는 `greet` 같은 제한된 행동만 요청하고, 보행 균형·정지·모터 안전은 로컬 제어기가 맡아야 합니다. Olaf 역시 자율 대화 로봇이 아니라 조종자가 애니메이션과 보행을 선택한 캐릭터 시연입니다.

### 논문 정보와 주의 / Paper versions and caveats

- BD-X: Grandia et al., *Design and Control of a Bipedal Robotic Character*, RSS 2024. The authors introduce a new character; this is not the paper's robot name. / 새 캐릭터를 설계한 논문이며 BD-X는 제목 속 로봇 이름이 아닙니다.
- Olaf: Müller et al., *Olaf: Bringing an Animated Character to Life in the Physical World*, arXiv v2, 2026-04-02. / 기존 캐릭터 Olaf의 현실 구현 논문입니다.
- Figures and numbers are the authors' robot results. The papers did not compare exterior preference in a controlled user study, and neither provides SNU GOM's XL330 design limits. / 수치는 저자들의 로봇 결과입니다. 외형 선호 통제 실험이나 SNU GOM XL330 한계를 제공하지 않습니다.
