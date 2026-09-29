[English](#english) | [한국어](#한국어)

<a id="english"></a>

# SNU GOM · 스누곰

A small bipedal bear robot for the SNU SHAPE-UP project. Short legs and large paws support standing, short walks, waddling and expressive body tilts. Camera/audio and API-connected human–robot interaction are now part of the design; the camera is in the nose. See [HRI architecture](docs/HRI.md).

**Confirmed: five XL330-M288-T motors per leg, ten in total.** Hip roll/pitch → knee pitch → ankle pitch/roll is the proposed arrangement. The initial head and arms are fixed; a two-axis neck is optional.

### Start here

1. Read the [five-person team guide](docs/TEAM.md) and choose an area.
2. Review the [project goals](docs/PROJECT_BRIEF.md) and [design decisions](docs/DECISIONS.md).
3. Run the checks below and choose a starter task from [Issues](https://github.com/mjcha924/snu-gom/issues).

```bash
git clone https://github.com/mjcha924/snu-gom.git
cd snu-gom
python -m venv .venv
source .venv/bin/activate
python tools/check_project.py
python -m unittest discover -s tests -v
```

Python 3.11 is recommended. These checks need no external Python packages or GPU. On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

### Current status

| Item | Status |
| --- | --- |
| Ten-joint specification and logical motor IDs | Draft; order and duplicate IDs checked in CI |
| Primitive URDF and joint viewer | Runnable model for inspecting the proposed layout |
| Roles, task templates and budget | Ready to use; individual team members not yet assigned |
| Motor brackets and manufacturing CAD | Still to be designed |
| Electronics and firmware | Specifications/interfaces drafted; implementation pending |
| Isaac Lab training and real walking | Not implemented or validated |

```bash
python -m pip install -r requirements-gom-viewer.txt
python tools/view_robot.py --mode pose
python tools/view_robot.py --mode sweep
```

The viewer inspects joints with a fixed base. It does not demonstrate walking or control hardware. See the [simulation guide](docs/SIMULATING_MOTION.md).

### Research

Start with the [Research / 자료조사 page](docs/RESEARCH.md) for papers, official videos, motor documentation and a five-person reading plan.

### Repository map

| Path | Purpose |
| --- | --- |
| `robot/` | Current biped configuration and generated URDF |
| `hardware/` | CAD handoff, electronics and purchasing CSVs |
| `firmware/` | MCU implementation plan and interfaces |
| `simulation/` | Simulation and learning plan |
| `tools/`, `tests/` | Generator, viewer and CPU checks |
| `docs/` | Goals, team workflow, schedule, decisions and experiments |
| `motion/`, `assets/v06_meshes/`, `scripts/` | [Previous nine-joint design](docs/legacy/README.md) |

[Mechanical design](docs/MECHANICAL_DESIGN.md) · [Electronics](docs/ELECTRONICS.md) · [Interfaces](docs/INTERFACES.md) · [Budget](hardware/bom/README.md) · [Roadmap](docs/ROADMAP.md) · [Contributing](CONTRIBUTING.md)

The repository is now **mjcha924/snu-gom**. For an existing clone, run `git remote set-url origin https://github.com/mjcha924/snu-gom.git`. Existing legacy package/CLI names remain `snu-bear` to preserve compatibility. The [MIT license](LICENSE) covers project code; it does not imply university endorsement or official mascot status.

---

<a id="한국어"></a>

# SNU GOM · 스누곰

서울대 SHAPE-UP 소형 이족보행 곰 로봇 프로젝트. 짧은 다리와 큰 발의 곰 외형을 유지하면서 기립·보행·표현 동작을 개발합니다. 코 카메라·음성 입출력·API 기반 HRI를 추가합니다. [HRI 구성](docs/HRI.md)을 참고하세요.

**확정: XL330-M288-T를 다리당 5개, 총 10개 사용.** 고관절 롤/피치 → 무릎 피치 → 발목 피치/롤은 검토 중인 축 배치입니다. 기본안의 머리와 팔은 고정이며 목 2축은 선택 사항입니다.

## 처음 참여한다면

1. [팀 5명 역할과 협업 절차](docs/TEAM.md)를 읽고 담당 영역을 정합니다.
2. [프로젝트 목표·완료 기준](docs/PROJECT_BRIEF.md)과 [설계 결정 기록](docs/DECISIONS.md)을 확인합니다.
3. 아래 검사를 실행한 뒤 [Issues](https://github.com/mjcha924/snu-gom/issues)에서 첫 작업을 맡습니다.

```bash
git clone https://github.com/mjcha924/snu-gom.git
cd snu-gom
python -m venv .venv
source .venv/bin/activate
python tools/check_project.py
python -m unittest discover -s tests -v
```

Python 3.11 권장. 위 검사는 외부 Python 패키지나 GPU가 필요 없습니다. Windows PowerShell에서는 `.venv\Scripts\Activate.ps1`로 환경을 활성화합니다.

## 현재 가능한 것

| 항목 | 상태 |
| --- | --- |
| 10축 관절 명세와 논리 모터 ID | 초안, CI로 중복·순서 검사 |
| 기본 도형 URDF와 관절 시각화 | 실행 가능한 기구 검토용 모델 |
| 팀 역할·작업 양식·예산 | 협업 시작용 구성 완료, 담당자 이름 미배정 |
| 모터 브래킷과 제조용 CAD | 설계 필요 |
| 실물 전장·펌웨어 | 사양 및 인터페이스 초안, 구현 필요 |
| Isaac Lab 학습·실제 보행 | 미구현·미검증 |

```bash
python -m pip install -r requirements-gom-viewer.txt
python tools/view_robot.py --mode pose
python tools/view_robot.py --mode sweep
```

시각화는 고정 베이스의 관절 검토입니다. 보행 영상이나 실물 제어가 아닙니다. [시뮬레이션 안내](docs/SIMULATING_MOTION.md)를 참고하세요.

## 자료조사

[Research / 자료조사 페이지](docs/RESEARCH.md)에 논문·공식 영상·모터 문서와 5인 조사 분담안을 모았습니다.

## 작업 위치

| 경로 | 용도 |
| --- | --- |
| `robot/` | 현재 biped 설정 및 생성된 URDF |
| `hardware/` | CAD 인수인계, 전장, 구매 BOM CSV |
| `firmware/` | MCU 구현 계획과 인터페이스 |
| `simulation/` | 시뮬레이션·학습 계획 |
| `tools/`, `tests/` | 생성기·시각화·CPU 검사 |
| `docs/` | 프로젝트 목표·팀·일정·결정·실험 기록 |
| `motion/`, `assets/v06_meshes/`, `scripts/` | [이전 9축 설계의 코드·자산](docs/legacy/README.md) |

[기구](docs/MECHANICAL_DESIGN.md) · [전장](docs/ELECTRONICS.md) · [공통 인터페이스](docs/INTERFACES.md) · [구매 예산](hardware/bom/README.md) · [일정](docs/ROADMAP.md) · [기여 방법](CONTRIBUTING.md)

저장소 주소는 `mjcha924/snu-gom`으로 변경되었습니다. 기존 clone은 `git remote set-url origin https://github.com/mjcha924/snu-gom.git`으로 갱신합니다. 이전 코드의 `snu-bear` 패키지·CLI 이름은 호환성을 위해 유지합니다. [MIT 라이선스](LICENSE)는 프로젝트 코드에 적용되며 대학의 공식 승인·마스코트 지위를 뜻하지 않습니다.
