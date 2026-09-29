[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Validation scope

September 29, 2026; revision `snu-gom-biped-v0.1-proxy`.

| Check | Result |
| --- | --- |
| `python tools/check_project.py` | Passed; ten joints, assumed primitive-model mass 0.600 kg |
| `python -m unittest discover -s tests -v` | Eight tests passed |
| `python -m compileall -q tools tests` | Passed |
| Budget recalculation | KRW 1,137,412 with proposed HRI hardware; optional and borrowed equipment separated |
| PyBullet headless joint viewer | Passed in [PR #6 CI](https://github.com/mjcha924/snu-gom/actions/runs/36562738762) |
| Manufacturing CAD, joint clearance, motor response | Not validated |
| Isaac import, training, physical standing/walking | Not validated |

The HRI hardware and detailed CAD are a newer design proposal; the existing URDF has not been regenerated to match them. Camera/audio/API runtime and assembled power/thermal behavior are not implemented or validated.

0.600 kg is the sum of assumed link masses, not a measurement. Contract checks do not prove motor packaging or walking. Record actual results in `docs/experiments/` with the commit and execution environment.

---

<a id="한국어"></a>

# SNU GOM 검증 범위

2026-09-29, revision `snu-gom-biped-v0.1-proxy`.

| 검사 | 결과 |
| --- | --- |
| `python tools/check_project.py` | 통과, 관절 10개, 도형 모델 질량 합계 0.600 kg |
| `python -m unittest discover -s tests -v` | 8개 통과 |
| `python -m compileall -q tools tests` | 통과 |
| 기본 예산 재계산 | HRI 후보 포함 1,137,412원, 선택·대여 장비 분리 |
| PyBullet headless 관절 viewer | [PR #6 CI](https://github.com/mjcha924/snu-gom/actions/runs/36562738762) 통과 |
| 제조 CAD·가동 범위·모터 응답 | 미검증 |
| Isaac Sim import·학습·실물 기립/보행 | 미검증 |

HRI 전장과 상세 CAD는 새로운 설계안이며 기존 URDF는 아직 이에 맞춰 재생성하지 않았습니다. 카메라·오디오·API 실행부와 조립 상태 전원·발열은 미구현/미검증입니다.

0.600 kg은 링크별 가정 질량의 합이며 측정값이 아닙니다. 관절 검사는 명세 일치 검사이지 모터 배치 가능성이나 보행 검증이 아닙니다. 실제 모델·실험 결과는 `docs/experiments/`에 commit과 실행 환경을 함께 기록합니다.
