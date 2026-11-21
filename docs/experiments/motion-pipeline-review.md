# Branch review / 브랜치 검토 결과

2026-11-21 KST · `feature/urdf-motion-pipeline`

[실행 안내](../MOTION_PIPELINE_KO.md) · [개발·AI 인수인계](../MOTION_PIPELINE_HANDOFF.md) · [기계 판독 결과](motion-pipeline-review.json)

The public motion pipeline was reviewed, corrected, documented and exercised
on CPU. The functional revision is `66bca7e`; the previous pushed revision was
`54f248b`. The current supplied robot assets were not edited. No new Isaac,
GPU training or hardware run was performed.

공개 브랜치의 모션 생성·검증·학습 연결 코드를 검토했습니다. 다른 사람이
새로 받아 실행할 때 발생할 수 있는 문제를 수정하고 실행 순서·데이터 규격·
코드 위치·결과 해석을 정리했습니다. 원본 로봇 자산은 변경하지 않았으며,
로컬 쉘 CAD·관련 모션·영상은 이번 코드 변경에 포함하지 않았습니다.

## Corrected problems / 수정한 문제

| Problem | Change |
| --- | --- |
| Windows CRLF checkout changed authoring fingerprints, rejecting equivalent data elsewhere | Normalize only Python-source newlines for authoring hashes and use LF checkout attributes. Robot assets, datasets and reports retain byte-exact hashes. |
| Relative output directory could fail after generation while writing `latest.json` | Resolve output paths once in the library as well as the CLI. |
| State reached the final frame while discrete contacts remained at the previous frame | Correct both Torch and CPU samplers at the finite endpoint and after clamping. |
| Inverse-dynamics LP could fail numerically after model mass/inertia changes | Normalize forces, torques and equations; bounded solver retries; distinguish infeasible balance from numerical errors. Numerical errors never become a reference pass. |
| Missing fields or unsupported time/contact conventions could reach the bank | Validate NPZ shapes, required fields, start time, fps, quaternion order/norm, finite values and binary supported contacts before loading. Check exported root velocities and body-frame foot coordinates during full validation. |
| Invalid/partial motor curves and joint-override typos were ambiguous | Reject them early and use one validated curve representation for CPU/Torch interpolation. |
| Training preflight differed from the CPU handoff's root-frame checks | Share joint/body/root-datum checks across train-plan, training, playback and the environment. |
| Bounded retries could leave missing kind/split pairs without a clear incomplete status | Write `complete` and missing pairs in the summary; incomplete CLI runs exit unsuccessfully. Kinematic and reference counts are separate. |
| A data ZIP could depend on external or absolute-path model assets | Reject nonportable model references at export; normalize in-repository package-root paths. |

새 코드의 밀집된 한 줄 표현을 일반적인 Python 형식으로 정리했습니다.
`AGENTS.md`와 인수인계 문서에는 원본 모델·과거 프록시의 구분, 수정 위치,
NPZ 좌표·단위 규격, 재생성 규칙, CPU/GPU 검증의 경계를 명시했습니다.
CPU CI는 Linux와 Windows를 모두 실행하도록 구성했습니다. 이 문서의
로컬 결과 자체는 Windows에서 수행한 검사입니다.

## Reproduction / 재현

Use Python 3.11 with `requirements-motion-pipeline.txt` and CPU Torch in a
personal environment. Run from the repository root:

```bash
python -m unittest discover -s tests/motion_pipeline -v
python -m unittest discover -s tests/walking -v
python -m unittest discover -s tests -v
python tools/check_project.py
python -m compileall -q snu_gom_walk scripts
python scripts/motion_pipeline.py run --output reports/review-verification --count 4 --seconds 4 --fps 50
```

The last command uses the default seed `20261121` and the unchanged supplied
1.192507 kg model. All four clips contain 201 frames at 50 Hz over 4 seconds,
with a separate 1-second physics warmup. The run and source fingerprints are in
the accompanying JSON. Generated datasets remain local/ignored; regenerate them
or transfer the exporter ZIP separately using the same source/model revision.

**81 CPU tests passed:** 32 pipeline, 41 walking, and 8 project tests.
The separate project/budget check and syntax compilation also passed. Project
tests cover the older proxy/budget; they are not physical-robot qualification.

Additional handoff checks passed:

- Default `train-plan` for stand and walk, including both train and val.
- Stand with `--require-dynamics`; walking with the same strict flag was
  correctly rejected for missing passing physics.
- Exported 22-file data ZIP passed archive integrity and whitelist checks.
- Extracted that ZIP into a separate checkout of `66bca7e`; stand/walk handoffs
  both passed without reauthoring the data.
- Repeated both handoffs after converting that checkout's authoring Python
  files from LF to CRLF. Hash checks still passed; actual code-content changes
  remain detectable in a regression test.
- Formatting-only changes in `generate.py` and `review.py` were compared at
  Python AST level and preserved their behavior. No new browser test is claimed.

## Reference outcomes / 모션 결과

| Clip | Split | Kinematics | Reference use | Tracking physics | Motor-screen solved frames | Peak utilization in solved frames |
| --- | --- | --- | --- | --- | --- | --- |
| `stand_000_a0` | train | Pass | Eligible | Pass | 201/201 | 12.8% |
| `walk_001_a0` | train | Pass | Conditional | Fail | 192/201 | 77.8% |
| `stand_002_a0` | val | Pass | Eligible | Pass | 201/201 | 12.8% |
| `walk_003_a0` | val | Pass | Conditional | Fail | 191/201 | 78.6% |

All four required kind/split pairs were admitted with no retries. The walking
references remain conditional because contact balance is unresolved in 9/10
frames. Even solved frames use optimistic outer-sole support; the percentages
are not a guarantee of real contact feasibility or continuous motor capability.

보행 물리 시험은 두 경우 모두 4초를 유지하고 목표 전진의 약 58.8%/56.7%를
진행했지만, 접촉 일정 일치·한 발 하중 지지·충분히 들고 번갈아 착지하는
조건을 통과하지 못했습니다. 검증된 번갈아 착지는 0회입니다. 따라서
자연스러운 보행 성공으로 처리하지 않았습니다. 기본 설정은 이 후보를
기구학·모터 검사를 거친 **조건부 학습 레퍼런스**로 허용하며, 엄격한
`--require-dynamics`는 거부합니다.

The next runtime check belongs on a suitable GPU machine using the pinned Isaac
environment and the small commands printed by `train-plan`. CPU tests validate
data, math and preflight contracts; they do not execute the new Isaac path.
Online command blending, periodic clip transitions, measured actuator/pad
identification and hardware transfer remain open work.
