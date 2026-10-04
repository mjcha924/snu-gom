# Character motion design / 캐릭터 동작 설계

These JSON files are design inputs for **CAD v0.3**, with eleven joint names. They are **not loaded by the existing ten-joint motion runtime** and contain no executable hardware policy.

두 JSON은 **11축 CAD v0.3 설계 입력**이며 기존 10축 모션 런타임이 읽는 설정이 아닙니다. 실물 정책이 포함되어 있지 않습니다.

- `character_motion_spec.json`: behavior families, RL objectives, HRI boundary, unknown calibration and CAD collision findings. / 행동 종류·학습 목표·HRI 경계·미확정 교정값·CAD 간섭 기록.
- `reference_clips.json`: look, coordinated sway and small greeting-dip visual keyframes in degrees. Omitted joints are zero. These are unbalanced kinematic sketches, not validated trajectories. A full bow needs torso orientation and contact design. / 도 단위 올려다보기·좌우 흔들림·낮춤 인사 시각 참조. 생략한 축은 0이며 균형 검증된 궤적이 아닙니다. 전신 인사는 몸통 기울기·접촉 설계가 더 필요합니다.

In the delivered CAD package, after rebuilding its cache with `python source/build.py`, render a reference with:

전달된 CAD 패키지에서 위 명령으로 캐시를 만든 후 참조를 렌더링합니다.

```bash
python source/render_reference.py --clip curious_look --phase 0.5
python source/render_reference.py --clip gentle_sway --phase 0.25
```

This produces a PNG under the package's `previews/` folder; it performs no hardware I/O and no dynamics simulation. Continuous paths and intermediate poses are not certified by endpoint checks. / `previews/`에 PNG를 만들며 모터 통신·동역학 시뮬레이션은 수행하지 않습니다. 끝 자세 검사는 연속 경로·중간 자세를 보장하지 않습니다.

[Paper-to-design rationale / 논문 반영](../../docs/PAPER_DESIGN.md) · [CAD verification / CAD 검사](../../docs/CAD_VERIFICATION.md)
