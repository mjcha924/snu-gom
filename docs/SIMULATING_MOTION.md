# SNU GOM 모델 실행

## CPU 검사

```bash
python tools/check_project.py
python -m unittest discover -s tests -v
```

관절 명세, 10개 모터 ID, 생성 URDF 일치, 양의 질량/관성, 구매 합계를 검사합니다. 설정 변경 후에는 `python tools/generate_robot.py`로 URDF를 갱신합니다.

## 도형 모델 시각화

```bash
python -m pip install -r requirements-gom-viewer.txt
python tools/view_robot.py --mode pose
python tools/view_robot.py --mode sweep
python tools/view_robot.py --mode sweep --headless --seconds 2
```

pose는 중립 자세, sweep는 관절 하나씩 작은 각도 변화를 보여 줍니다. 모두 fixed-base, zero-gravity의 kinematic inspection이며 질량·접촉·보행을 검증하지 않습니다. 외형은 브래킷 없는 기본 도형입니다. 바닥에서 떠 보이거나 움직여도 동적 안정성을 뜻하지 않습니다.

## Isaac Sim과 RL 다음 단계

M4가 GPU 환경과 Isaac Sim/Isaac Lab 버전을 선정하고 `simulation/ENVIRONMENT.md`에 실제 성공한 버전을 기록합니다. URDF를 import해 축·스케일·collision·inertia를 확인하고 single-leg step response부터 실측과 비교합니다. 이후 기준 보행, 학습 환경, reward, domain randomization, 반복 평가를 구현합니다. 초기 작업은 기존 9축 `motion/`을 바로 실행하는 것이 아닙니다.

이전 모델을 재현하려면 [legacy 안내](legacy/README.md)를 따릅니다. `scripts/simulate.py`는 이전 9축 모델 전용입니다.
