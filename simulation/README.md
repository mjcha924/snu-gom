[English](#english) | [한국어](#한국어)

<a id="english"></a>

# modeling and RL

The new model is `robot/snu_gom.urdf`. It currently uses primitive geometry and estimated dynamics for joint-layout inspection. Old nine-joint tasks and checkpoint formats under `motion/` are incompatible.

Sequence: frame/unit checks → manufacturing CAD → motor-response/contact verification → baseline locomotion → learning environment → training with measured uncertainty → repeated hardware comparisons. Human-motion imitation remains an extension. Record model/environment versions, seed, training conditions, evaluation counts and failures in experiment records.

---

<a id="한국어"></a>

# 모델과 RL

새 모델은 `robot/snu_gom.urdf`입니다. 현재 기본 도형·추정 동역학으로 관절 구조를 확인하는 단계입니다. 기존 `motion/`의 9축 task와 checkpoint 형식은 호환되지 않습니다.

순서: 좌표/단위 검사 → 제조 CAD 반영 → 모터 응답 및 접촉 확인 → 기준 보행 → 학습 환경 → 실측 오차를 반영한 학습 → 실물 반복 비교. 사람 동작 모방은 확장 연구로 남깁니다. 모델 버전·환경 버전·seed·학습 조건·평가 횟수와 실패 사례를 실험 기록에 남깁니다.
