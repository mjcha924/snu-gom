# Mechanical design / 기구 설계

**Current prototype: v0.7 / 최신 기구 시제품: v0.7**

SNU GOM is a teddy-bear biped with a 403 mm (40.3 cm) full-shell height. The shoulders and upper body are tall enough to house the proximal leg motors at shoulder level. Full-shell size is 124.75 × 220 × 403 mm; the internal skeleton is 107 × 174 × 348.5 mm. The CAD uses the supplied XL/XC-330 STEP motor exterior and horn geometry.

SNU GOM은 외장형 기준 높이 403 mm(40.3 cm)의 곰 인형형 이족보행 로봇입니다. 어깨와 상부 몸통을 높여 다리의 근위부 모터가 어깨 높이까지 올라오는 배치를 수용합니다. 외장형 전체 크기는 124.75 × 220 × 403 mm, 내부 골격은 107 × 174 × 348.5 mm입니다. 제공된 XL/XC-330 STEP의 모터 외형과 혼 형상을 사용합니다.

| Feature / 항목 | v0.7 design / 설계 |
|---|---|
| Joint chain / 관절 순서 | Hip pitch → hip roll → hip yaw → knee pitch → ankle pitch / 고관절 피치 → 롤 → 요 → 무릎 피치 → 발목 피치 |
| Leg actuators / 다리 모터 | XC330-M288 at hip pitch + knee pitch; XL330-M288 at hip roll, hip yaw + ankle pitch / 피치·무릎 XC, 롤·요·발목 XL |
| Neck / 목 | One XL330 pitch joint / XL330 피치 1축 |
| Total actuators / 전체 모터 | 4 XC330 + 7 XL330 = 11 / 4 XC + 7 XL = 11 |
| Hip topology / 고관절 배치 | Serial P-R-Y triangle; R 18 mm rearward / 직렬 P-R-Y 삼각형, R 18 mm 후방 |
| Thigh/shin axis spacing / 허벅지·종아리 축간 | 65 mm each / 각각 65 mm |
| Feet / 발 | 88 × 66 mm sole outline with replaceable pads / 88 × 66 mm 발판, 교체형 패드 |
| Camera / 카메라 | Straight-facing nose camera; head pitch changes gaze / 정면 코 카메라, 목 피치로 시선 변경 |
| Arms / 팔 | Fixed cosmetic arms / 고정 외장 팔 |

## Why these motor locations / 모터 위치 선정 이유

Hip pitch is the first priority for the higher-torque XC because it carries trunk/head/electronics gravity and stride acceleration. Knee pitch is the second likely high-load sagittal joint in crouching and stance. Hip roll/yaw and ankle pitch remain XL for this prototype. This is a reasoned assignment, not a torque proof; calculate from measured mass and COM across the intended gait. At 5 V, official stall ratings are 0.93 N·m for XC330-M288 and 0.52 N·m for XL330-M288. Both use the same 20 × 34 × 26 mm exterior envelope; nominal masses are 23 g and 18 g. Stall ratings are momentary values, not continuous walking torque.

강한 XC 모터는 상체·머리·전장 중력과 보행 가속을 받는 고관절 피치에 우선 배치하고, 웅크림/지지 자세에서 높은 부하가 예상되는 시상면 무릎 피치에 두 번째 배치합니다. 이번 시제품에서는 고관절 롤·요와 발목 피치는 XL로 둡니다. 이는 계산 완료된 토크 설계가 아니므로 보행 목표 자세에서 실측 질량과 무게중심으로 계산해야 합니다. 5 V 공식 정지 토크는 XC330-M288 0.93 N·m, XL330-M288 0.52 N·m입니다. 두 모터의 외형은 모두 20 × 34 × 26 mm이고 명목 질량은 각각 23 g, 18 g입니다. 정지 토크는 순간값이며 지속 보행 토크가 아닙니다.

## Head motor horn and fit / 머리 모터 혼과 조립

The old head-carrier operation clipped the complete bracket to an ellipsoid, which could cut the printed yoke around the neck horn. v0.7 preserves the complete two-sided yoke/horn interface and trims only the surrounding support frame. The motor horn and purchased fasteners remain separate components. Check screw access, shell clearance and cable flex on a physical fit sample.

기존 머리 캐리어 작업은 브래킷 전체를 타원체로 잘라 목 혼 주변의 출력 요크가 잘릴 수 있었습니다. v0.7은 양쪽 요크/혼 인터페이스를 온전하게 유지하고 주변 지지 프레임만 다듬습니다. 모터 혼과 구매 체결재는 별도 부품입니다. 실제 출력 시편에서 나사 접근성·쉘 여유·케이블 굽힘을 확인하세요.

## Power and verification limits / 전원과 검증 한계

At 5 V, the four XC plus seven XL motors have a theoretical simultaneous-stall sum of about 17.5 A. This is not an average walking draw, but it means the existing 10/11 A converter candidate and harness need transient/current-limit testing. The TTL controller/bus can remain the same; rework the motor-power distribution if measurements require it. Do not feed motor current through the controller board.

5 V에서 XC 4개와 XL 7개의 동시 정지 전류 합은 이론상 약 17.5 A입니다. 보행 평균 소비전류는 아니지만 기존 10/11 A 변환기 후보와 배선의 과도응답/전류 제한을 시험해야 합니다. TTL 제어기/통신 버스는 그대로 사용할 수 있으나 측정 결과에 따라 모터 전원 분배를 수정해야 합니다. 모터 전류를 제어기 보드로 통과시키지 마세요.

The STEP exports re-import with valid B-rep solids (full shell 244; internal assembly 203). This confirms geometry serialization only; it does not establish fastener strength, manufacturing fit, current/thermal margin, full-range collision clearance, balance, or walking. Print one joint sample, weigh the whole robot, measure COM and current, then update the [CAD verification plan](CAD_VERIFICATION.md), [electronics notes](ELECTRONICS.md) and [simulation model](SIMULATING_MOTION.md).

전체 외장 STEP 244개, 내부 조립체 STEP 203개 솔리드가 유효하게 재가져오기 됩니다. 이는 형상 파일의 유효성만 확인한 것으로 체결 강도·출력 공차·전류/발열 여유·전체 가동 간섭·균형·보행을 검증하지 않았습니다. 관절 시편을 출력하고 전체 무게·무게중심·전류를 측정한 뒤 [CAD 검증 계획](CAD_VERIFICATION.md), [전장 문서](ELECTRONICS.md), [시뮬레이션 모델](SIMULATING_MOTION.md)을 갱신하세요.

[CAD handoff](../hardware/mechanical/README.md) · [HRI](HRI.md) · [Simulation](SIMULATING_MOTION.md)
