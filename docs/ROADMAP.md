# Development steps / 개발 순서

| Step / 단계 | Result / 결과 | Needed first / 선행 조건 |
| --- | --- | --- |
| 1. Joint fit / 관절 체결 | Print one saddle/yoke and verify the real XL330 hardware / 시편과 실물 모터 체결 확인 | Supplied CAD and actual motor / 원본 CAD·실물 |
| 2. One leg / 한쪽 다리 | Load, current, temperature and cable-clearance records / 하중·전류·온도·배선 기록 | Reliable joint mounting / 관절 체결 |
| 3. Head and HRI / 머리·HRI | Neck pitch, straight nose camera, microphone and speaker bench test / 목 피치·코 카메라·음성 시험 | Head mass and wiring allowance / 머리 질량·배선 |
| 4. Complete model / 전체 모델 | Matching CAD, URDF, mass and inertia / CAD·URDF·질량·관성 일치 | Measured dimensions and masses / 실측 |
| 5. Supported standing / 지지 기립 | Eleven-motor wiring and fault behavior / 11축 배선·오류 대응 | Power and control checks / 전원·제어 |
| 6. Walking and expression / 보행·표현 | Repeatable baseline, then learning and HRI integration / 반복 가능한 기준 제어 후 학습·HRI | Reliable model and hardware / 모델·실물 검증 |

Project period: 2026-09-15 to 2027-01-30. Schedule each step around actual motor delivery and test results. Track concrete tasks in [Issues](https://github.com/mjcha924/snu-gom/issues); use [commit and PR guidelines](../CONTRIBUTING.md) for all changes.

활동 기간은 2026-09-15~2027-01-30이며 실제 납기와 시험 결과에 맞춰 순서를 진행합니다. 작업은 Issues, 변경 절차는 공통 커밋·PR 안내를 사용합니다.
