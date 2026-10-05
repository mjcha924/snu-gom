# SNU GOM · 스누곰

[English](#english) · [한국어](#한국어)

<a id="english"></a>

## English

**A small bear-shaped biped that walks, looks at people and responds through voice and movement.** SNU GOM combines a ten-joint lower body with a tilting head, a camera in its nose, microphones and a speaker.

### The design

| Part | Current design |
| --- | --- |
| Legs | Five XL330-M288-T motors per leg: hip roll/pitch, knee pitch, ankle pitch/roll |
| Head | One XL330 neck-pitch motor to look up and down; 11 motors overall |
| Nose | Camera faces straight ahead within the head; the neck changes its viewing angle |
| Arms | Fixed bear-shaped arms |
| Electronics | Proposed Pi 4 for camera/audio/API work; OpenRB-150 for motor communication; torso IMU |
| Interaction | Voice input/output, camera perception and external APIs; implementation in progress |

Walking, waddling and expressive responses are development goals. They have not been demonstrated on the physical robot.

### Explore the project

| I want to… | Open |
| --- | --- |
| Understand the robot | [Project overview](docs/PROJECT_BRIEF.md) |
| See or import the mechanical CAD | [CAD geometry and layout](docs/CAD_GEOMETRY.md) · [CAD files and status](hardware/mechanical/README.md) · [Onshape import and joint setup](docs/ONSHAPE.md) |
| Understand camera, voice and APIs | [HRI design](docs/HRI.md) |
| Check wiring and parts | [Electronics](docs/ELECTRONICS.md) · [BOM and costs](hardware/bom/README.md) |
| Run the existing model | [Simulation guide](docs/SIMULATING_MOTION.md) |
| Find papers and videos | [Research](docs/RESEARCH.md) · [BD-X / Olaf design changes](docs/PAPER_DESIGN.md) |
| Make a change | [Branch, commit and PR guide](CONTRIBUTING.md) |
| See what comes next | [Roadmap](docs/ROADMAP.md) · [Open tasks](https://github.com/mjcha924/snu-gom/issues) |

### Try the existing model

```bash
git clone https://github.com/mjcha924/snu-gom.git
cd snu-gom
python -m venv .venv
source .venv/bin/activate
python tools/check_project.py
python -m pip install -r requirements-gom-viewer.txt
python tools/view_robot.py --mode pose
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. Python 3.11 is recommended. The current viewer is an earlier **ten-leg-joint proxy** with a fixed base. It has not yet been updated to the detailed CAD or moving neck, and it does not simulate validated walking. See [validation status](docs/GOM_VALIDATION.md).

### Current work

**CAD v0.3:** shell-on and skeleton STEP prototypes are available for the full robot and leg pair; the bilateral variants use five XL330 joints per leg. [Design and limits](docs/PAPER_DESIGN.md) · [Onshape import and joint setup](docs/ONSHAPE.md).

The fit-prototype archive and exact supplier motor/horn geometry have been shared with the project owner. The repository keeps the CAD manifest and import instructions; a new Onshape document and fabrication-qualified CAD have not been created. Next: verify one joint, test one leg under load, complete wiring, update the simulation model and bench-test conversation. The HRI API design exists; an HRI runtime is not implemented yet.

---

<a id="한국어"></a>

## 한국어

**CAD v0.3:** 전체 로봇과 양쪽 다리의 외장형·골격형 STEP 시제품을 준비했습니다. 양쪽 다리는 XL330 5개씩 사용합니다. [설계·한계](docs/PAPER_DESIGN.md) · [Onshape 가져오기와 관절 설정](docs/ONSHAPE.md).

**걷고, 사람을 바라보고, 말과 동작으로 반응하는 작은 곰 모양 이족보행 로봇입니다.** 다리 10축에 위아래로 움직이는 머리, 코 카메라, 마이크와 스피커를 결합합니다.

### 기본 구성

| 부분 | 현재 설계 |
| --- | --- |
| 다리 | 다리당 XL330-M288-T 5개: 고관절 롤/피치, 무릎 피치, 발목 피치/롤 |
| 머리 | 목 피치 XL330 1개로 위아래 보기; 전체 11개 모터 |
| 코 | 머리 기준 정면 카메라; 목 움직임으로 시선 각도 변경 |
| 팔 | 고정된 곰 모양 팔 |
| 전장 | 카메라·음성·API용 Pi 4, 모터 통신용 OpenRB-150, 몸통 IMU 후보 |
| 상호작용 | 음성 입출력·영상 인식·외부 API; 구현 진행 전 설계 단계 |

보행·뒤뚱거림·표현 동작은 개발 목표이며 실물에서 검증된 기능은 아닙니다.

### 원하는 내용 찾기

| 궁금한 내용 | 문서 |
| --- | --- |
| 로봇의 목표와 구성 | [프로젝트 개요](docs/PROJECT_BRIEF.md) |
| 기구 CAD 가져오기 | [CAD 형상·기구 배치](docs/CAD_GEOMETRY.md) · [CAD 상태](hardware/mechanical/README.md) · [Onshape 가져오기와 관절 설정](docs/ONSHAPE.md) |
| 카메라·음성·API | [HRI 설계](docs/HRI.md) |
| 전장·구매·가격 | [전장](docs/ELECTRONICS.md) · [BOM과 예산](hardware/bom/README.md) |
| 모델 실행 | [시뮬레이션 안내](docs/SIMULATING_MOTION.md) |
| 논문·영상 | [자료조사](docs/RESEARCH.md) |
| GitHub에 변경 올리기 | [브랜치·커밋·PR 안내](CONTRIBUTING.md) |
| 앞으로 할 일 | [개발 순서](docs/ROADMAP.md) · [작업 목록](https://github.com/mjcha924/snu-gom/issues) |

위 실행 명령은 기존 다리 10축 도형 모델을 보여줍니다. 상세 CAD·목 피치는 아직 반영하지 않았으며 고정 베이스의 관절 확인용입니다. 보행 검증은 아닙니다. [검증 상태](docs/GOM_VALIDATION.md)를 확인하세요.

시제품 STEP 패키지와 제공 모터/혼 형상을 프로젝트 소유자에게 전달했습니다. 저장소에는 CAD manifest와 Onshape 안내를 기록했으며 새 Onshape 문서나 제작 검증 CAD는 아직 없습니다. 다음은 관절 시편 → 한쪽 다리 하중 시험 → 배선 → 모델 갱신 → 정지 상태 대화 시험입니다. HRI API 설계는 있지만 실행 서버는 아직 없습니다.

---

`robot/` model · `hardware/` CAD/electronics/BOM · `firmware/` communication · `simulation/` learning · `docs/` project notes. Earlier nine-joint material is kept under [legacy documentation](docs/legacy/README.md). / 이전 9축 자료는 별도 보관합니다.
