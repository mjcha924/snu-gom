# SNU GOM 검증 범위

2026-09-29, revision `snu-gom-biped-v0.1-proxy`.

| 검사 | 결과 |
| --- | --- |
| `python tools/check_project.py` | 통과, 관절 10개, 도형 모델 질량 합계 0.600 kg |
| `python -m unittest discover -s tests -v` | 8개 통과 |
| `python -m compileall -q tools tests` | 통과 |
| 기본 예산 재계산 | 834,412원, 선택·대여 장비 분리 |
| 제조 CAD·가동 범위·모터 응답 | 미검증 |
| Isaac Sim import·학습·실물 기립/보행 | 미검증 |

0.600 kg은 링크별 가정 질량의 합이며 측정값이 아닙니다. 관절 검사는 명세 일치 검사이지 모터 배치 가능성이나 보행 검증이 아닙니다. 실제 모델·실험 결과는 `docs/experiments/`에 commit과 실행 환경을 함께 기록합니다.
