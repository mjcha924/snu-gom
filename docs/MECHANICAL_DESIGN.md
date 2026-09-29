# Mechanical design / 기구 설계

The detailed prototype keeps the original bear face and uses the supplied XL/XC-330 STEP with its output horns, rear idlers, screws and connectors. Each leg has five XL330-M288-T motors; a separate neck-pitch motor raises the head. **11 motors overall; arms fixed.**

기존 곰 얼굴을 유지하고 제공된 XL/XC-330 STEP의 혼·아이들러·나사·커넥터를 사용합니다. 다리당 XL330-M288-T 5개와 목 피치 1개로 **전체 11개**, 팔은 고정입니다.

| Feature / 항목 | Prototype / 시안 |
| --- | --- |
| Leg chain / 다리 축 순서 | Hip roll → hip pitch → knee pitch → ankle pitch → ankle roll |
| Hip spacing / 고관절 간격 | 88 mm |
| Thigh / shin axis spacing / 축간 | 48 / 48 mm |
| Foot sole / 발판 | 88 × 66 mm, rounded outline / 둥근 외곽 |
| Torso / 몸통 | 92 × 124 × 102 mm |
| Camera / 카메라 | Straight ahead in nose; head pitch controls gaze / 정면 코 카메라·목 피치로 시선 변경 |
| Custom shells / 외장 | About 1.6 mm nominal wall; local details differ / 주요 구간 1.6 mm, 국부 형상은 다름 |
| Supplied motor case / 제공 케이스 | 20 × 34 × 23 mm measured geometry / 형상 치수 |
| Horn interface / 혼 인터페이스 | 29 mm between outer mating faces; four holes on Ø12 mm circle / 체결면 간 29 mm·Ø12 원주 4공 |

The custom saddle and dual-sided yoke use measured hole centres. Case-hole thread/fastener suitability, printed tolerances and load capacity still need physical verification. Electronics other than the supplied motors are packaging envelopes. The first full-body assembly is for fit review; neck travel, cable slack, service-cover retention and actual head load remain development tasks.

자체 새들·양면 요크는 실측 구멍 중심을 사용하지만 케이스 체결부의 나사·사용 가능 여부, 출력 공차·하중은 실물 검증이 필요합니다. 모터 외 전자부품은 공간 배치 형상입니다. 전체 조립체는 검토용이며 목 가동 범위·배선 여유·커버 고정·머리 하중을 검증해야 합니다.

Print one joint fit specimen before building a leg. Measure current, heating and deflection under representative load. The previous 0.600 kg assumption is not a current complete-robot mass estimate. Material volume, purchased components and measured prints must be combined into a new mass budget.

한 관절 시편을 먼저 출력하고 한쪽 다리에서 대표 하중의 전류·발열·변형을 측정합니다. 기존 0.600 kg은 현재 완성 로봇의 질량이 아닙니다. CAD 체적·구입 부품·출력 실측값으로 질량을 갱신합니다.

**Simulation mismatch / 모델 차이:** `robot/config.json` and its URDF are still an earlier ten-leg-joint primitive model. They do not yet contain this detailed geometry, offset axes or neck joint. Update frames, collision geometry, masses and inertia before using the new CAD for learning. / 기존 도형 URDF는 상세 형상·오프셋·목 관절을 아직 반영하지 않았습니다.

[CAD handoff](../hardware/mechanical/README.md) · [HRI](HRI.md) · [Simulation](SIMULATING_MOTION.md)
