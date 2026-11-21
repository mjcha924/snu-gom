# URDF 변경부터 기준 보행·검증·Isaac 학습까지

[English](MOTION_PIPELINE.md) · [기존 Isaac 설치 안내](../HEADLESS_TRAINING.md) · [로컬 실행 기록](experiments/motion-pipeline-local.md)

이 브랜치는 기존 `snu_gom_walk`와 `scripts/train.py`에 모션 라이브러리를 연결합니다. 기존 로컬 Open Duck 폴더나 다른 브랜치를 수정하는 방식이 아닙니다. 원본 URDF·메시·질량·관절 축도 덮어쓰지 않습니다.

**부드러운 기구학 보행 후보와 실제 물리 보행 성공을 구분합니다.** 기립은 CPU 물리 검사로 확인했지만 자연스러운 동역학 보행·Isaac의 새 학습 경로·실물 운전은 아직 검증하지 않았습니다. 이 작업에서 GPU 학습이나 GPU 서버 접속은 하지 않았습니다.

## 1. 로컬 설치

Python 3.11을 권장합니다. 현재 작업 PC에는 저장소 안의 `.venv-motion`을 준비했습니다. 다른 PC에서는 다음처럼 만듭니다.

```powershell
python -m venv .venv-motion
.\.venv-motion\Scripts\python.exe -m pip install -r requirements-motion-pipeline.txt
# Torch가 없는 CPU 검사용 환경에서만 추가합니다. 서버의 CUDA Torch를 바꾸지 마세요.
.\.venv-motion\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Linux에서는 `.venv-motion/bin/python`을 사용합니다. 모션 생성·MuJoCo 검사는 GPU나 Isaac을 설치하지 않아도 됩니다. Torch는 학습 입력 보간 검사에 사용합니다.

## 2. URDF 선택과 변경

설정 파일은 [`configs/motion_pipeline/gom.json`](../configs/motion_pipeline/gom.json)입니다.

```powershell
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py inspect
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py inspect --urdf path/to/revised.urdf
```

`urdf`, 관절 순서, 몸통·발 이름, 초기 자세, 작업 범위, 모터 가정, 생성 매개변수, 합격 기준을 한곳에 둡니다. 바뀐 형상·질량·관성·관절 범위·속도는 URDF에서 다시 읽습니다. 상대 메시 경로를 지원하며 `package://` 경로는 `package_roots`에 패키지의 로컬 경로를 명시합니다.

URDF **내용**, 참조하는 시각/충돌 메시 **내용**, 프로파일을 함께 해시합니다. 파일명만 같고 내용이 바뀌어도 다른 모델입니다. 생성·검증 코드가 바뀐 경우도 기존 모션을 학습 입력으로 그대로 쓰지 못하게 합니다. USD 캐시도 선택한 모델의 지문에 따라 분리됩니다. 화면 표시 코드 수정은 물리 결과를 무효화하지 않습니다.

현재 Isaac 어댑터는 SNU GOM의 다리 10축+목 2축 계약을 사용합니다. 같은 관절 구성의 CAD·질량·관성·한계 갱신은 새 프로파일/URDF로 다시 실행하면 됩니다. 관절 이름·자유도·트리를 바꾸면 `joint_order`와 Isaac 관측·행동 어댑터를 명시적으로 수정해야 합니다. 모르는 로봇에 기존 관절 매핑을 임의 적용하지 않습니다.

한 개의 박스형 발은 바닥면 중심을 자동으로 계산합니다. 충돌 메시를 가진 발이나 여러 충돌체가 있는 발은 접촉 기준을 명시하세요. 예시 값은 실제 CAD의 발 좌표계로 바꿔야 합니다.

```json
"sole_frames": {
  "left_foot_link": {"xyz": [0.0, 0.0, -0.02], "rpy": [0.0, 0.0, 0.0]},
  "right_foot_link": {"xyz": [0.0, 0.0, -0.02], "rpy": [0.0, 0.0, 0.0]}
}
```

STL/OBJ 충돌 발은 실제 볼록 껍질 정점을 사용합니다. 발 링크의 기준점과 바닥 접촉면을 혼동하지 않도록 기준을 추측하지 않습니다. 원기둥·구 등의 다른 발 모델은 별도 sole 어댑터가 필요합니다. 비볼록 메시 충돌은 MuJoCo의 볼록 표현이라는 한계가 있습니다.

기본 충돌 정책은 엄격합니다. CAD 수정 예정인 쌍을 허용하려면 `allowed_collision_pairs`에 `{"links":["링크A","링크B"],"max_penetration_m":0.003}`처럼 명시합니다. 기구학 보고서는 이 깊이까지만 허용합니다. 현재 물리 엔진과 Isaac의 충돌을 통째로 끄지 않으므로, 단순 허용 설정만으로 동역학 합격이 보장되지는 않습니다.

## 3. 생성 → 전 프레임 검사 → 물리 검사

```powershell
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py run --count 4 --seconds 4 --fps 50
# 다른 URDF를 선택할 때
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py run --urdf path/to/revised.urdf --count 4 --seconds 4
```

출력은 `reports/motion_pipeline/<모델지문>-<실행지문>/`입니다. `latest.json`은 최신 실행 위치를 가리킵니다. 다른 모델/설정/생성 코드의 결과를 같은 성공 파일로 덮어 재사용하지 않습니다. 같은 실행 설정을 다시 실행하면 그 실행 폴더의 결과를 새로 계산합니다.

기립·보행을 최소 두 개씩 만들고 종류별로 마지막 클립을 검증용으로 분리합니다. seed와 제한된 균등 범위에서 주기·속도·상체·시선을 바꾸며, 관절에 무작위 잡음을 더하는 방식이 아닙니다. 각 후보의 재시도는 최대 세 번이고, 실패하면 목표를 작게 바꿉니다. 합격 기준을 자동 완화하지 않습니다.

1. **부드러운 발 궤적:** 이륙/착지에서 속도와 가속도가 0인 다항 곡선을 사용합니다. 처음·끝에는 양발 지지 시간을 둡니다.
2. **무게중심/압력중심 계획:** 유한 구간 LIPM QP로 지지 영역과 미래 발 배치를 고려합니다. 이 계획은 명목 CoM 높이 근사입니다. 실제 전신 CoM 높이는 고정하지 않고, 골반 곡선과 IK 결과에 따라 바뀝니다.
3. **전신 IK:** 분석 Jacobian으로 발·CoM·골반·목을 맞추고, 관절 범위와 프레임 간 속도 제한을 강제합니다. 발목 roll이 없으므로 발의 수동 구름을 허용하되 실제 충돌 형상의 최저점이 바닥에 박히지 않도록 계산합니다.
4. **기구학 검사:** 모든 프레임의 FK, ROM, 속도, 저장된 속도의 일치, 발/CoM 오차, 바닥 침투, 몸통의 바닥 접촉과 자기충돌을 검사합니다. AABB 지지 여유는 진단값이며 동역학 안정성 증명은 아닙니다.
5. **물리 검사:** MuJoCo에서 부유 기저·중력·마찰·접촉을 켜고 관절 토크만 적용합니다. 동일한 접촉 법칙의 역동역학 미분으로 토크를 탐색하고 실제 전진 계산에서 다시 확인합니다. 루트에 보조 힘을 주거나 매 프레임 위치를 강제하지 않습니다.

물리 합격에는 전체 구간 생존뿐 아니라 관절 한계·속도·토크, 자기/몸통 바닥 접촉, 몸통 기울기, 접촉 일정, 실제 한 발 지지, 충분히 들고 반대 발이 지지한 상태에서의 번갈아 착지, 목표 대비 전진을 확인합니다. 짧게 검사하는 `--physics-seconds`는 진단용이며 전체 클립의 물리 합격을 만들지 않습니다. 이 문턱값은 프로젝트의 임시 공학 기준이며 Disney 논문 수치가 아닙니다.

BDX는 제작된 태스크 공간 보행 → CoM/CoP 계획 → 역동역학 → 미리 샘플링한 목표 보간이라는 역할 구성을 참고했습니다. Disney의 비공개 생성기와 같은 성능을 재현했다는 뜻은 아닙니다. 논문의 Gaussian 시간 기저/센서 잡음을 “가우시안에서 보행 클립 하나 추출”로 해석하지 않습니다. [원문 §V-A 및 부록](https://arxiv.org/html/2501.05204v1).

## 4. 확인 화면과 저장물

`모션_검토.cmd`를 두 번 클릭하거나 다음을 실행합니다.

```powershell
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py review
```

`review.html`은 인터넷·별도 서버 없이 열리는 파일입니다. 후보 선택, 3D 충돌 형상 회전, 재생/정지, 구간 탐색, 관절 각도·실제 적용 토크, 합격 조건을 확인합니다. 왼쪽은 제작된 기준이고 오른쪽은 실제 물리 계산입니다. 검토 화면의 반복 재생은 무한 주기 보행 검증을 의미하지 않습니다.

| 파일 | 내용 |
| --- | --- |
| `manifest.json` | 모델·코드·클립·검사 지문, 학습/검증 구분 |
| `*.npz` | 관절/루트/발/CoM 상태, 위상, 접촉, 목표 |
| `*.validation.json` | 전 프레임 기구학 결과, 속도·가속도 지표 |
| `*.physics.json` | 생존·착지·전진·충돌·토크 peak/RMS·추종 오차 |
| `*.trace.json`, `*.torque.csv` | 물리 재생 데이터와 관절별 토크 |
| `review.html`, `summary.json` | 사람용 비교 화면과 기계가 읽는 요약 |

## 5. 학습 입력 연결을 CPU에서 확인

```powershell
$motionRun = (Get-Content reports/motion_pipeline/latest.json -Raw | ConvertFrom-Json).run
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py train-plan --run $motionRun --kind stand
# 물리 미통과 보행을 모방하며 균형을 배우는 실험을 명시적으로 선택할 때만:
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py train-plan --run $motionRun --kind walk --allow-kinematic
.\.venv-motion\Scripts\python.exe -m unittest discover -s tests/motion_pipeline -v
```

이 단계는 Isaac·GPU 학습을 실행하지 않습니다. 라이브 모델과 모든 파일/보고서 지문을 확인하고 학습/검증 클립 및 서버 명령을 `train-plan.json`에 씁니다. 기본값은 물리 합격 데이터만 허용합니다. `--allow-kinematic`은 물리적으로 추종 가능한 보행이 검증됐다는 의미가 아닙니다.

## 6. 나중에 서버에서 학습

브랜치가 업로드된 후 서버의 **본인 작업 폴더**에 clone/check out합니다. 공용 IsaacLab·conda·다른 사용자 폴더를 수정하지 않습니다. 기존 [Isaac 설치 안내](../HEADLESS_TRAINING.md)의 고정 환경을 사용합니다. 새 모션 경로는 같은 저장소의 `scripts/train.py`와 `scripts/play.py`로 연결했으며 이 PC에서는 실제 Isaac 실행을 검증하지 못했습니다.

로컬에서 데이터만 내보낼 수 있습니다. 프로파일·URDF·메시는 Git 코드와 일치해야 합니다.

```powershell
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py export --run $motionRun
```

생성한 `*-data.zip`은 manifest와 명시된 NPZ/검사/메타데이터만 담습니다. 서버 저장소 루트에서 풀면 `reports/...` 경로가 복원됩니다. 키·VPN·로컬 가상환경·녹음은 포함하지 않습니다. 데이터/체크포인트는 팀이 정한 위치에 한 벌만 유지하세요. 서버에서는 CPU 모션 생성용 의존성을 Isaac 공용 환경에 전부 설치할 필요가 없습니다.

먼저 `nvitop`으로 사용 상태를 확인한 뒤 작은 실행부터 시작합니다. 아래 `<run>`은 실제 폴더 이름으로 바꿉니다.

```bash
python scripts/motion_pipeline.py train-plan --run reports/motion_pipeline/<run> --kind stand
python scripts/train.py --task stand --motion-manifest reports/motion_pipeline/<run>/manifest.json \
  --num-envs 32 --iterations 2 --memory-fraction .35 --headless

# 기구학 보행을 쓰는 명시적 실험
python scripts/train.py --task walk --motion-manifest reports/motion_pipeline/<run>/manifest.json \
  --allow-kinematic --num-envs 32 --iterations 2 --memory-fraction .35 --headless

# 분리해 둔 val 모션으로 평가
python scripts/play.py --checkpoint runs/<run>/model.pt --episodes 2 --seconds 4 --headless
```

라이브러리 모드는 10개 다리 행동과 12개 관절 상태를 사용합니다. 정책 관측 72개/critic 90개이며, 기준 관절·속도·접촉·높이·목·위상 정보를 포함합니다. 클립을 무작위로 선택하고 유한 구간 끝에서 reset합니다. 평가에서는 val 클립을 순서대로 순환합니다. 목은 기준 명령을 따릅니다. 50Hz 목표는 500Hz 물리 계산에 선형 보간하고, 명시적 PD effort와 같은 5V 토크/속도 외피를 적용합니다. 오프라인의 역동역학 제어기와 학습의 PD 제어기는 서로 다릅니다.

XL330/XC330의 공급 전압은 5V, 기본 상한은 stall의 20%와 URDF effort 중 작은 값입니다. 속도에 따른 상한도 보수적으로 적용합니다. **연속 정격·열·패드 물성·실측 서보 모델이 아닙니다.** `working_limits`는 IK 작업 범위이며 MuJoCo에 가짜 기계적 스토퍼로 추가하지 않습니다. 실제 관절 스토퍼는 원본 URDF 범위를 보존합니다.

Torch 메모리 비율은 기본 0.35, 최대 0.4로 제한하지만 PhysX·렌더러까지 제한하지 않으므로 전체 사용량을 확인해야 합니다. 장시간/대용량 실행은 팀 공유 규칙을 따르세요. 기존 체크포인트는 당시 소스/모델과 연결돼 있으므로 새 관측·모터 모델의 실험에는 새 학습을 시작합니다. 모델·소스·데이터가 다른 resume/replay를 강제로 허용하지 않습니다.

현재 범위는 유한 기립/직진 보행 참조입니다. 실시간 속도/회전 명령 블렌딩, 무한 주기 경계, 측정된 모터·폼 패드, 실제 GPU smoke test와 실물 전이는 후속 작업입니다.
