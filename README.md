# SNU GOM · 스누곰

서울대 SHAPE-UP 소형 이족보행 곰 로봇 프로젝트. 짧은 다리와 큰 발의 곰 외형을 유지하면서 기립, 짧은 보행, 뒤뚱거림과 몸 기울이기 같은 표현 동작을 개발합니다.

**확정: XL330-M288-T를 다리당 5개, 총 10개 사용.** 고관절 롤/피치 → 무릎 피치 → 발목 피치/롤은 검토 중인 축 배치입니다. 기본안의 머리와 팔은 고정이며 목 2축은 선택 사항입니다.

## 처음 참여한다면

1. [팀 5명 역할과 협업 절차](docs/TEAM.md)를 읽고 담당 영역을 정합니다.
2. [프로젝트 목표·완료 기준](docs/PROJECT_BRIEF.md)과 [설계 결정 기록](docs/DECISIONS.md)을 확인합니다.
3. 아래 검사를 실행한 뒤 [Issues](https://github.com/mjcha924/snu-bear/issues)에서 첫 작업을 맡습니다.

```bash
git clone https://github.com/mjcha924/snu-bear.git
cd snu-bear
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

기존 저장소 주소 `snu-bear`는 팀 링크 호환성을 위해 유지합니다. 프로젝트 이름은 SNU GOM입니다. [MIT 라이선스](LICENSE)는 프로젝트 코드에 적용되며 대학의 공식 승인·마스코트 지위를 뜻하지 않습니다.
