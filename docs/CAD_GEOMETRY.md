# CAD geometry and mechanical layout / CAD 형상 및 기구 배치

## Current prototype: v0.6 taller body / 최신 시제품: v0.6 높인 몸통

The full shell measures **124.75 × 220 × 403 mm (X × Y × Z)**, so its current modeled height is **40.3 cm**. The internal skeleton measures 107 × 174 × 348.5 mm. Relative to v0.5, the torso, shoulder/arm and head packaging moved upward by 35 mm to enclose the upper hip motors at shoulder level. XL330 motor geometry was not scaled. The wider torso cavity gives additional clearance around those motors. This is a packaging-level prototype; dimensions may change after real part, fastener, wiring and print-fit checks.

전체 외장형 크기는 **124.75 × 220 × 403 mm(X × Y × Z)**이며 현재 모델의 높이는 **40.3 cm**입니다. 내부 골격은 107 × 174 × 348.5 mm입니다. v0.5보다 몸통·어깨/팔·머리 배치를 35 mm 위로 옮겨 상부 고관절 모터가 어깨 높이까지 올라오는 구성을 수용했습니다. XL330 모터 형상은 확대하지 않았으며 모터 주변 몸통 내부 공간을 넓혔습니다. 실제 부품·체결재·배선·출력 시험 전의 패키징 시제품입니다.

### v0.6 models

See the [mechanical CAD index](../hardware/mechanical/README.md) and [`hardware/mechanical/cad/v0.6/`](../hardware/mechanical/cad/v0.6/) for shell-on, skeleton, paired-leg and single-leg STEP models, source parameters, joint frames, exact supplied motor/horn reference STEP and hashes.

### Leg kinematics and hip packaging

Each leg uses five serial XL330-M288-T joints: **hip pitch → hip roll → hip yaw → knee pitch → ankle pitch**. No ankle-roll motor is included. P-R-Y are arranged as a compact triangle: hip roll is rearward, while pitch and yaw stay near the frontal/central plane. Thigh and shin pitch-axis spacing are 65 mm. The right side mirrors the left side across the robot center plane, including case and connector offsets. A separate neck-pitch XL330 adds one degree of freedom (11 motors total).

다리당 XL330-M288-T 5개를 직렬로 사용합니다: **고관절 피치 → 롤 → 요 → 무릎 피치 → 발목 피치**. 발목 롤 모터는 없습니다. 고관절 P-R-Y는 삼각형으로 가깝게 배치하며 롤은 뒤쪽, 피치와 요는 정면/중앙면에 가깝게 둡니다. 허벅지·종아리 피치축 간격은 각각 65 mm입니다. 오른쪽은 케이스와 커넥터 편심을 포함해 왼쪽을 중앙면 기준으로 대칭 배치했습니다. 목 피치 XL330 1개를 더해 총 11축입니다.

### Loading and review limits

The taller torso carries more mass above the hip pitch axis and may increase its static and dynamic torque. The previous motor-only R/Y inertia comparison does not answer whether P has enough margin for this taller assembly. Weigh the assembled torso, head, electronics and battery; measure their centers of mass; then recalculate static gravity torque and walking acceleration cases using the XL330’s practical torque-speed/current limits. Do not size motion from stall torque alone.

높아진 몸통은 고관절 피치축 위쪽의 질량을 늘려 정적·동적 토크를 키울 수 있습니다. 과거 R/Y 모터만 비교한 관성 계산으로는 높아진 조립체에서 P축 여유 토크가 충분한지 알 수 없습니다. 몸통·머리·전장·배터리 조립체 질량과 무게중심을 실측하고 XL330의 실제 토크-속도/전류 한계로 중력 및 보행 가속 조건을 다시 계산하세요. 정지 토크만으로 동작을 정하지 마세요.

## Design history

The original v0.5 geometry, P-R-Y spacing, electronics envelope assumptions and preliminary motor-only comparison remain below as historical context. They should not be taken as v0.6 load validation.

---

# CAD geometry and assembly / CAD 형상과 조립 구조

**Current revision: v0.5 · triangular serial P-R-Y hip · units mm**

The current CAD is a bipedal SNU GOM prototype with five XL330-M288-T joints per leg and one neck-pitch motor. The hips use a **serial pitch → roll → yaw chain**. P and Y sit forward on the leg centerline; R is offset 18 mm rearward, making the triangular side-view layout requested by the team. The layout remains a serial chain: each motor carries the downstream joints.

최신 CAD는 다리마다 XL330-M288-T 관절 5개와 목 피치 모터 1개가 있는 이족보행 SNU GOM 시제품입니다. 고관절은 **피치 → 롤 → 요 직렬 연결**입니다. P와 Y는 다리 중심선 전방에, R은 뒤로 18 mm 이동해 측면 삼각형을 이룹니다. 병렬 구조가 아니라 각 모터가 다음 관절을 지지하는 직렬 구조입니다.

![Triangular P-R-Y shell prototype / P-R-Y 삼각 배치 외장 시제품](images/cad-v05/PRY_TRI_full_shell.png)

![Triangular skeleton / 삼각형 배치 골격형](images/cad-v05/PRY_TRI_full_skeleton.png)

[Leg side profile / 다리 측면](images/cad-v05/PRY_TRI_leg_profile.png)

## Joints and dimensions / 관절과 치수

| Chain / 연결 순서 | Function / 역할 |
|---|---|
| Hip pitch (P) / 고관절 피치 | Swings the whole leg forward and back / 다리 전체를 앞뒤로 움직임 |
| Hip roll (R) / 고관절 롤 | Moves the leg side-to-side / 다리를 좌우로 기울임 |
| Hip yaw (Y) / 고관절 요 | Turns the leg about vertical / 다리 방향을 수평 회전 |
| Knee pitch / 무릎 피치 | Bends the leg / 다리를 굽힘 |
| Ankle pitch / 발목 피치 | Tilts the foot toe-up/toe-down / 발끝을 위아래로 기울임 |

`+X` is forward, `+Y` is robot-left and `+Z` is up. Left-side joint centers are P `(0, 54, 230)`, R `(-18, 54, 194)`, Y `(0, 54, 158)`, knee `(0, 54, 93)`, ankle `(0, 54, 28)` mm. The right side is mirrored about the robot center plane. Hip spacing is 108 mm; P-R and R-Y axis distances are 40.2 mm each; thigh and shin pitch-axis distances are 65 mm each. The lower-leg chain has no ankle-roll joint.

`+X`는 전방, `+Y`는 로봇 왼쪽, `+Z`는 위쪽입니다. 왼쪽 관절 중심은 P `(0, 54, 230)`, R `(-18, 54, 194)`, Y `(0, 54, 158)`, 무릎 `(0, 54, 93)`, 발목 `(0, 54, 28)` mm입니다. 오른쪽은 로봇 중앙면 기준으로 대칭입니다. 고관절 간격은 108 mm, P-R 및 R-Y 축 간격은 각각 40.2 mm, 허벅지 및 종아리 피치축 간격은 각각 65 mm입니다. 발목 롤 관절은 없습니다.

The P axis carries the downstream hip joints and the entire leg. A supplier-CAD motor-assembly estimate in [`hardware/mechanical/cad/v0.5/PRY_TRIANGULAR_LAYOUT.md`](../hardware/mechanical/cad/v0.5/PRY_TRIANGULAR_LAYOUT.md) finds only a small added load from moving R rearward, but this is not a motor sizing result: it excludes links, feet, shell, wiring, impacts and thermal duty. XL330 stall torque must not be treated as continuous torque.

P축은 그 아래의 고관절 관절과 다리 전체를 지지합니다. R을 뒤로 옮겨 추가되는 하중은 R/Y 모터 본체만 고려하면 작게 추정되지만, 이는 모터 선정 결과가 아닙니다. 링크, 발, 외장, 배선, 충격과 발열 부하가 제외되어 있습니다. XL330 정지 토크를 연속 사용 토크로 간주하면 안 됩니다.

## Motors, links, covers / 모터·링크·외장

Each motor instance uses the provided XL330-M288-T case, output horn, opposite idler, fasteners and connector geometry. Printed/custom components form the carriers, hip deck, thigh and shin links, ankle yoke, paw structure and wire shrouds. The outer bear shell is cosmetic and serviceable; the internal frame carries the joint loads. The CAD uses nominal purchased-part envelopes for electronics, not exact board models.

각 모터는 제공된 XL330-M288-T 케이스, 출력 혼, 반대쪽 아이들러, 체결부와 커넥터 형상을 사용합니다. 출력 부품은 모터 캐리어, 골반 데크, 허벅지·종아리 링크, 발목 요크, 발 구조와 배선 커버입니다. 곰 외장은 외형·정비용이고 관절 하중은 내부 프레임이 받습니다. 전자부품은 실물 상세 모델이 아닌 구매품 외형 치수를 사용했습니다.

The torso and head include packaging envelopes for the listed compute, motor-control, camera, microphone, speaker, IMU, battery and regulator components. This is a neutral-pose packaging study. Connector access, cable bend, cooling, mounting and the full motion range remain to be checked with purchased parts.

몸통과 머리에는 부품표의 컴퓨팅 보드, 모터 제어기, 카메라, 마이크, 스피커, IMU, 배터리와 전압 변환기 외형을 배치했습니다. 중립 자세에서의 패키징 검토이며 실제 부품의 커넥터 접근, 배선 굽힘, 냉각, 체결과 전체 관절 가동 범위는 추가 확인해야 합니다.

## Files and verification / 파일과 검증

See [the CAD file index and downloads](../hardware/mechanical/README.md). STEP imports passed geometry validity checks for the exported leg variants and full skeleton. Neutral electronics envelopes have no pairwise or torso/head shell intersections. Full motion collision, structural strength, stable walking and fabrication readiness have not been validated. Older v0.3 documentation is retained under [`docs/legacy/`](legacy/README.md) and `hardware/mechanical/cad/v0.3/` as design history.

[CAD 파일 목록과 다운로드](../hardware/mechanical/README.md)를 참고하세요. 양쪽 다리 STEP 변형들과 전체 골격은 재가져오기 형상 유효성 검사를 통과했습니다. 중립 자세에서 전자부품 외형끼리 또는 몸통·머리 쉘과 겹치지 않습니다. 전체 가동 범위 간섭, 구조 강도, 안정 보행과 제작 준비 상태는 검증되지 않았습니다. 이전 v0.3 문서는 설계 이력으로 보관합니다.
