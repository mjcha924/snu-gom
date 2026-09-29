# Research / 자료조사

[English](#english) | [한국어](#한국어) · [Home / 홈](../README.md) · [Team / 팀](TEAM.md)

Checked / 확인일: **2026-09-29**. Primary sources are linked below. Priority and suggested experiments are our project recommendations, not claims made by the authors. Links were inspected; external code, CAD and policies have not been validated on SNU GOM.
공식·원저자 자료를 아래에 연결합니다. 우선순위와 제안 실험은 우리 프로젝트에 대한 추천이며 원저자의 주장이 아닙니다. 링크는 확인했지만 외부 코드·CAD·정책을 SNU GOM에서 실행·검증하지는 않았습니다.

<a id="english"></a>

## English

### Start with these three

1. **M1/M2/M3: XL330 manual (R4)** — establish the physical mounting and motor-control constraints before finalizing a leg.
2. **M4: Microduck RL (R2)** — inspect the observation/action/reward and actuator-model design before creating our learning task.
3. **Everyone: Disney biped paper/video (R8)** — discuss how movement can express a bear character while maintaining balance.

### Hardware and working robot references

| ID / priority | Resource | Why it matters to SNU GOM | Next task and limitation |
| --- | --- | --- | --- |
| R1 / First | [Microduck official demo / launch film](https://pollen-robotics.com/microduck/) · [runtime source](https://github.com/pollen-robotics/microduck) | Direct reference for waddling, expressive motion and skating demonstrations. | M1/M5: list three behaviors achievable with our ten leg motors and fixed head/arms. Microduck has different hardware and more motors; its demonstrations do not prove our geometry can perform them. |
| R2 / First | [Microduck RL — training source](https://github.com/pollen-robotics/microduck_rl) | MuJoCo/mjlab, PPO, actuator modeling, randomization and deployment provide an inspectable learning pipeline. | M4: make a table of observations, actions, rate, reward and termination rules. Map each to our joint contract; its policy is not directly compatible with SNU GOM or automatically portable to Isaac. |
| R3 / Next | [Open Duck Mini v2 — CAD, build references and videos](https://github.com/apirrone/Open_Duck_Mini) | A separate project with CAD/build links and sim-to-real demonstration clips. Useful for comparing assembly and model handoff. | M1/M4: compare one hip/ankle arrangement and cable route against our XL330 dimensions. Do not confuse Open Duck Mini with Pollen Microduck; check each referenced version. |
| R4 / First | [ROBOTIS XL330-M288 manual](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/) | Dimensions, control table, operating modes, feedback, watchdog and limits for our selected motor. | M1/M3: make a mounting checklist and one-axis register/unit map; validate limits on the bench. Stall figures are not continuous-load ratings. |
| R5 / First | [OpenRB-150 manual](https://emanual.robotis.com/docs/en/parts/controller/openrb-150/) · [DYNAMIXEL SDK](https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/) | Controller power paths, communication and SDK examples for a candidate implementation. | M2/M3: draw the actual power/data wiring and record one-motor read/write timing. Board and cable current limits still govern our external distribution design. |
| R6 / Next | [Rhoban BAM — actuator identification](https://github.com/Rhoban/bam) | Tools for identifying and simulating extended servo friction models. | M3/M4: design an XL330 position-response/load experiment and compare simulation. Do not assume another motor's fitted parameters apply to ours. |

### Papers, learning and simulation

| ID / priority | Resource | Why it matters to SNU GOM | Next task and limitation |
| --- | --- | --- | --- |
| R7 / First for M4 | [Isaac Lab: importing an asset](https://isaac-sim.github.io/IsaacLab/main/source/how-to/import_new_asset.html) · [official repository](https://github.com/isaac-sim/IsaacLab) | Official starting point for bringing the URDF into the learning stack. | M4: pin a compatible release, import the model and check axes, units, collisions and actuator settings. The linked main docs can change; installation/import is not yet verified for our robot. |
| R8 / First | [Grandia et al., Design and Control of a Bipedal Robotic Character — RSS 2024; paper and official video](https://la.disneyresearch.com/publication/design-and-control-of-a-bipedal-robotic-character/) | Combines character-oriented mechanics, expressive motion and RL control. | M4/M5: propose a small torso-sway or bowing reference while retaining a balance objective. Different morphology and hardware mean no direct controller transfer. |
| R9 / Next | [Rudin et al., Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning — CoRL / PMLR 2022](https://proceedings.mlr.press/v164/rudin22a.html) | Parallel training and curriculum design for legged locomotion. | M4: extract one curriculum idea and one evaluation protocol for flat-ground standing/walking. Results are on ANYmal; the title does not promise our robot will train in minutes. |
| R10 / Later | [Peng et al., DeepMimic — SIGGRAPH 2018; paper, code and videos](https://xbpeng.github.io/projects/DeepMimic/index.html) | Example-guided imitation and task objectives address the idea of learning human-like or authored motions. | M4/M5: author a low-amplitude ten-joint sway reference before trying human-motion retargeting. Simulated character skills are not evidence of physical XL330 feasibility. |
| R11 / Next | [MIT Underactuated Robotics — Russ Tedrake](https://underactuated.mit.edu/) | Dynamics, contact and walking foundations for interpreting controller failures. | M1/M4: sketch support/contact changes and center-of-mass motion during one proposed step. Use this to explain a failure case in the experiment log. |

### Videos to watch together

- **Microduck official page (R1):** watch the launch film and behavior clips. Note foot contact, body sway and which behavior needs extra hardware.
- **Disney paper page (R8):** open the official video under “Additional Content.” Note how expressive commands and locomotion coexist.
- **DeepMimic project page (R10):** watch the author-provided videos. Separate reference-motion style from physical feasibility on our motor/geometry limits.
- **Open Duck Mini README (R3):** inspect its real-robot and simulation clips. Record robot/version and visible support or intervention; a clip alone is not a repeatability metric.

These link to the original pages hosting or linking the videos; no video files are copied into this repository.

### Suggested five-person reading split

| Slot | Start with | Bring to the next meeting |
| --- | --- | --- |
| M1 mechanical | R3, R4 | One leg-layout sketch with packaging constraints |
| M2 electronics | R4, R5 | Power path and unresolved current limits |
| M3 firmware | R4, R5, R6 | One-axis measurement and telemetry plan |
| M4 simulation/RL | R2, R7, R9 | Observation/action/reward table and import plan |
| M5 integration | R1, R8, R10 | Two measurable expressive-motion proposals |

Create a note from [research/TEMPLATE.md](research/TEMPLATE.md), then link an issue if it changes our design. Record an upstream commit/version, a short summary, applicability, limitations, and one proposed experiment. Add findings to [DECISIONS.md](DECISIONS.md) only after team review. Link to papers rather than uploading copies; check the upstream license before reusing code or CAD.

---

<a id="한국어"></a>

## 한국어

### 먼저 볼 자료 세 가지

1. **M1/M2/M3: XL330 매뉴얼(R4)** — 다리를 확정하기 전에 모터 체결·제어 제약을 정리합니다.
2. **M4: Microduck RL(R2)** — 학습 환경을 만들기 전에 관측·행동·보상·모터 모델 구성을 확인합니다.
3. **전원: Disney 이족 로봇 논문·영상(R8)** — 균형을 유지하면서 곰 캐릭터를 동작으로 표현하는 방법을 논의합니다.

### 하드웨어와 실제 로봇 참고 자료

| ID / 우선순위 | 자료 | SNU GOM에 도움이 되는 점 | 다음 작업과 한계 |
| --- | --- | --- | --- |
| R1 / 먼저 | [Microduck 공식 데모·출시 영상](https://pollen-robotics.com/microduck/) · [런타임 소스](https://github.com/pollen-robotics/microduck) | 뒤뚱거림·표현 동작·스케이팅 데모의 직접 참고 자료입니다. | M1/M5: 다리 10축과 고정 머리·팔로 가능한 행동 후보 3개를 정리합니다. 다른 하드웨어와 더 많은 모터를 쓰므로 그 데모가 우리 기구의 가능성을 입증하지는 않습니다. |
| R2 / 먼저 | [Microduck RL 학습 소스](https://github.com/pollen-robotics/microduck_rl) | MuJoCo/mjlab, PPO, 모터 모델, 무작위화와 배포까지 살펴볼 수 있습니다. | M4: 관측·행동·주기·보상·종료 조건 표를 만들고 우리 관절 계약에 대응시킵니다. 정책을 SNU GOM에 바로 사용하거나 Isaac으로 자동 이식할 수는 없습니다. |
| R3 / 다음 | [Open Duck Mini v2 — CAD·제작 자료·영상](https://github.com/apirrone/Open_Duck_Mini) | CAD·제작 링크와 sim-to-real 영상을 제공하는 별도 프로젝트입니다. 조립과 모델 인수인계를 비교하기 좋습니다. | M1/M4: 고관절·발목 배치와 케이블 경로를 XL330 치수와 비교합니다. Pollen Microduck과 혼동하지 말고 자료별 버전을 확인합니다. |
| R4 / 먼저 | [ROBOTIS XL330-M288 매뉴얼](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/) | 선택한 모터의 치수·제어 테이블·모드·피드백·watchdog·제한값 자료입니다. | M1/M3: 체결 체크리스트와 1축 레지스터·단위 표를 만들고 벤치에서 검증합니다. 스톨 수치는 연속 부하 정격이 아닙니다. |
| R5 / 먼저 | [OpenRB-150 매뉴얼](https://emanual.robotis.com/docs/en/parts/controller/openrb-150/) · [DYNAMIXEL SDK](https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/) | 후보 제어기의 전원 경로·통신·SDK 예제입니다. | M2/M3: 실제 전원·데이터 배선도와 1축 읽기·쓰기 시간을 기록합니다. 외부 분배 설계에서도 보드·케이블 전류 정격을 지켜야 합니다. |
| R6 / 다음 | [Rhoban BAM — 모터 특성 식별](https://github.com/Rhoban/bam) | 서보의 확장 마찰 모델을 식별·시뮬레이션하는 도구입니다. | M3/M4: XL330 위치 응답·부하 시험을 설계하고 시뮬레이션과 비교합니다. 다른 모터의 식별값을 그대로 쓰지 않습니다. |

### 논문·학습·시뮬레이션

| ID / 우선순위 | 자료 | SNU GOM에 도움이 되는 점 | 다음 작업과 한계 |
| --- | --- | --- | --- |
| R7 / M4 먼저 | [Isaac Lab asset import 문서](https://isaac-sim.github.io/IsaacLab/main/source/how-to/import_new_asset.html) · [공식 저장소](https://github.com/isaac-sim/IsaacLab) | URDF를 학습 환경으로 가져오는 공식 출발점입니다. | M4: 호환 버전을 고정하고 축·단위·충돌·actuator 설정을 검사합니다. main 문서는 바뀔 수 있으며 우리 로봇의 설치·import는 아직 미검증입니다. |
| R8 / 먼저 | [Grandia 외, Design and Control of a Bipedal Robotic Character — RSS 2024; 논문·공식 영상](https://la.disneyresearch.com/publication/design-and-control-of-a-bipedal-robotic-character/) | 캐릭터를 위한 기구·표현 동작·RL 제어를 함께 다룹니다. | M4/M5: 균형 목표를 유지하는 작은 몸통 흔들기·인사 참조 동작을 제안합니다. 형태와 하드웨어가 달라 제어기를 바로 옮길 수는 없습니다. |
| R9 / 다음 | [Rudin 외, Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning — CoRL / PMLR 2022](https://proceedings.mlr.press/v164/rudin22a.html) | 다리 로봇의 병렬 학습과 커리큘럼 설계 참고 자료입니다. | M4: 평지 기립·보행에 적용할 커리큘럼과 평가 방법을 하나씩 추출합니다. ANYmal 결과이며 우리 로봇도 몇 분 만에 학습된다는 뜻은 아닙니다. |
| R10 / 나중 | [Peng 외, DeepMimic — SIGGRAPH 2018; 논문·코드·영상](https://xbpeng.github.io/projects/DeepMimic/index.html) | 사람처럼 움직이거나 직접 만든 동작을 배우는 아이디어에 관련된 모방·과제 목표입니다. | M4/M5: 사람 모션을 옮기기 전에 작은 진폭의 10축 흔들기 참조를 만듭니다. 시뮬레이션 캐릭터의 기술이 실물 XL330의 가능성을 입증하지는 않습니다. |
| R11 / 다음 | [MIT Underactuated Robotics — Russ Tedrake](https://underactuated.mit.edu/) | 제어 실패를 이해하기 위한 동역학·접촉·보행 기초입니다. | M1/M4: 한 걸음의 접촉 변화와 무게중심 이동을 그려 실험 실패 사례를 설명합니다. |

### 함께 볼 영상

- **Microduck 공식 페이지(R1):** 출시 영상과 행동 클립에서 발 접촉·몸통 흔들림·추가 하드웨어가 필요한 동작을 구분합니다.
- **Disney 논문 페이지(R8):** “Additional Content”의 공식 영상을 보고 표현 명령과 보행이 어떻게 함께 작동하는지 기록합니다.
- **DeepMimic 프로젝트 페이지(R10):** 원저자 영상을 보고 참조 동작의 스타일과 우리 모터·기구의 실현 가능성을 구분합니다.
- **Open Duck Mini README(R3):** 실물·시뮬레이션 클립에서 로봇 버전과 외부 지지·개입 여부를 기록합니다. 영상 하나는 반복 성공률 측정이 아닙니다.

영상이 포함되거나 연결된 원본 페이지를 사용하며 저장소에 영상 파일을 복사하지 않습니다.

### 5인 자료조사 분담 제안

| 슬롯 | 시작 자료 | 다음 미팅에 가져올 결과 |
| --- | --- | --- |
| M1 기구 | R3, R4 | 패키징 제약이 표시된 다리 배치 스케치 |
| M2 전장 | R4, R5 | 전원 경로와 미확정 전류 제한 |
| M3 펌웨어 | R4, R5, R6 | 1축 측정·텔레메트리 계획 |
| M4 시뮬레이션/RL | R2, R7, R9 | 관측·행동·보상 표와 import 계획 |
| M5 통합 | R1, R8, R10 | 측정 가능한 표현 동작 제안 2개 |

[research/TEMPLATE.md](research/TEMPLATE.md)를 복사해 조사 노트를 작성하고 설계 변경이 필요하면 Issue를 연결합니다. 원본 commit·버전, 짧은 요약, 적용점, 한계, 제안 실험 하나를 기록합니다. 팀 검토 후에만 [DECISIONS.md](DECISIONS.md)에 결정을 반영합니다. 논문은 복사 업로드 대신 링크하고 코드·CAD를 재사용하기 전에 원본 라이선스를 확인합니다.
