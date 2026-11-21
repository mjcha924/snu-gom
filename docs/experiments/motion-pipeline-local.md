# Motion pipeline: local CPU validation / 로컬 검증

2026-11-21 KST · `feature/urdf-motion-pipeline` · [한국어 실행 안내](../MOTION_PIPELINE_KO.md) · [English guide](../MOTION_PIPELINE.md) · [Machine-readable evidence](motion-pipeline-local.json)

The URDF-to-reference-to-training-input path was exercised locally. **No new Isaac run, GPU training or hardware test was performed.** Kinematic references are available for both standing and walking; dynamic walking remains unqualified.

URDF 변경 감지부터 기준 생성·전 프레임 검사·물리 검사·확인 화면·학습 입력 연결까지 로컬에서 확인했습니다. **Isaac의 새 경로 실행·GPU 학습·실물 검증은 하지 않았습니다.** 보행 후보를 만든 것과 안정적인 물리 보행 성공을 구분합니다.

## Results / 결과

Each reference contains 201 frames at 50 Hz over 4 seconds, with a separate one-second physical settling interval. The source model mass is approximately 1.193 kg; parameters remain provisional.

| Clip | Split | Full-frame kinematics | Free-base dynamics |
| --- | --- | --- | --- |
| `stand_000_a0` | train | Pass / 통과 | Pass / 통과 |
| `walk_001_a0` | train | Pass / 통과 | Fail / 미통과 |
| `stand_002_a0` | val | Pass / 통과 | Pass / 통과 |
| `walk_003_a0` | val | Pass / 통과 | Fail / 미통과 |

Standing tracking RMSE was about 0.047° for train and 0.046° for val, with maximum torso tilt about 2.00°. These numbers describe the current model and short test, not hardware accuracy or robustness.

기립은 train/val 모두 4초 시험을 유지했습니다. 관절 추종 RMSE는 약 0.047°/0.046°, 최대 몸통 기울기는 약 2.00°입니다. 현재 모델의 짧은 시험 수치이며 실물 정확도나 외란 강인성의 검증은 아닙니다.

The training walk survived the interval but had zero qualified alternating landings and only approximately 22.5% of the intended path progress; it also exceeded a provisional joint-speed limit. The held-out walking rollout lost balance. Neither was accepted as dynamically verified walking. Low joint error or survival alone did not qualify it.

보행 train 후보는 시험 구간을 유지했지만 명확한 번갈아 착지가 0회, 목표 대비 전진은 약 22.5%였고 임시 관절 속도 한계를 넘었습니다. val 보행은 균형을 잃었습니다. 둘 다 물리 합격으로 처리하지 않았습니다. 기본 학습은 이 데이터를 거부하며, 기구학 모방 실험에는 `--allow-kinematic`이 필요합니다.

## Checks / 확인 범위

- **62 CPU tests passed:** 8 project checks, 41 walking checks, 13 pipeline checks. These include URDF/mesh-content invalidation, original mass/FK/physical-stop preservation, an explicit root-datum guard, STL sole handling, full-frame kinematics, nonfinite/body-ground rejection, train/val separation, tamper rejection, name-mapped interpolation, observation features and inverse/forward contact derivatives.
- Stand and provisional walk `train-plan` commands were checked without importing Isaac. The default walk gate rejected unverified dynamics. Both train and val references were integrity-checked.
- The data ZIP passed archive integrity and whitelist checks: 18 manifest/summary/motion/metadata/validation files, no credentials or environments.
- A real browser exercised clip selection, pause, timeline seeking and joint-angle/torque selection. The selected walking clip remained selected; JavaScript errors: 0.

프로젝트·보행·파이프라인 CPU 테스트 62개가 통과했습니다. 모델/메시 변경과 파일/보고서 변조를 감지하고, 관절 순서 매핑·구간 끝 보간·접촉 역동역학 미분을 확인했습니다. 실제 브라우저에서 선택 유지·일시정지·구간 이동·관절 그래프를 확인했으며 JavaScript 오류는 0개였습니다.

![Offline authored-reference and physical-rollout review / 모션과 물리 검사 비교](media/motion-pipeline/review.png)

The image displays URDF collision geometry rather than photorealistic CAD visuals. Its explicit walking failure label is intentional. GPU validation must start with the small smoke commands in the guide before a long learning run. Online command blending, infinite-cycle transitions and identified actuator/pad models remain future work.

화면은 사진이나 CAD 외관 대신 검사용 충돌 형상을 표시합니다. 보행의 “물리 미통과” 표시는 의도된 검사 결과입니다. 서버에서는 안내 문서의 작은 실행부터 확인해야 하며, 실시간 명령 전환·무한 주기 연결·실측 액추에이터/패드 모델은 후속 작업입니다.
