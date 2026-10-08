# CAD geometry and mechanical layout / CAD 형상 및 기구 배치

## Current prototype: v0.7 / 최신 시제품: v0.7

The shell-covered prototype is **124.75 × 220 × 403 mm (X × Y × Z)**, or **40.3 cm tall**. The internal skeleton is 107 × 174 × 348.5 mm. Relative to v0.5, the torso, shoulder/arm and head package moved up by 35 mm so the proximal leg motors fit up to shoulder level. The XL/XC motor geometry was not scaled.

외장형 시제품은 **124.75 × 220 × 403 mm(X × Y × Z)**이며 높이는 **40.3 cm**입니다. 내부 골격은 107 × 174 × 348.5 mm입니다. v0.5보다 몸통·어깨/팔·머리 배치를 35 mm 높여 다리 근위부 모터를 어깨 높이까지 배치했습니다. XL/XC 모터 형상은 확대하지 않았습니다.

## Joint layout / 관절 배치

Each leg has five serial joints: **XC330 hip pitch → XL330 hip roll → XL330 hip yaw → XC330 knee pitch → XL330 ankle pitch**. One XL330 neck-pitch joint raises the head. Total: **4 XC330 + 7 XL330 = 11 motors**. There is no ankle-roll motor. The right leg mirrors the left across the center plane, including case and connector offsets.

다리마다 직렬 관절 5개를 사용합니다: **XC330 고관절 피치 → XL330 고관절 롤 → XL330 고관절 요 → XC330 무릎 피치 → XL330 발목 피치**. 목 피치 XL330 1개가 머리를 움직입니다. 전체 **XC330 4개 + XL330 7개 = 11개**입니다. 발목 롤 모터는 없습니다. 오른쪽 다리는 모터 케이스와 커넥터 편심까지 왼쪽을 중앙면 기준으로 대칭 배치했습니다.

| Axis / 축 | Purpose / 기능 | Motor / 모터 |
|---|---|---|
| Hip pitch / 고관절 피치 | Forward/back leg swing / 다리 앞뒤 스윙 | XC330-M288-T |
| Hip roll / 고관절 롤 | Side-to-side balance / 좌우 균형 | XL330-M288-T |
| Hip yaw / 고관절 요 | Rotate leg about vertical / 수직축 방향 전환 | XL330-M288-T |
| Knee pitch / 무릎 피치 | Bend and extend leg / 다리 굽힘·펴기 | XC330-M288-T |
| Ankle pitch / 발목 피치 | Toe-up/down and foot placement / 발끝 위아래·발 위치 | XL330-M288-T |
| Neck pitch / 목 피치 | Tilt head and camera view / 머리·카메라 시선 기울이기 | XL330-M288-T |

## Why place XC330 at P and knee? / XC330을 P와 무릎에 둔 이유

Hip pitch carries the upper-body gravity and stride demand, so it is the first priority for the stronger motor. Knee pitch is the other likely high-load sagittal joint during crouch and stance. This is a first-pass actuator allocation, not a torque proof; final sizing needs the complete robot mass, center of mass, desired motion and actuator torque-speed/current data. At 5 V ROBOTIS lists 0.93 N·m stall torque for XC330-M288 and 0.52 N·m for XL330-M288. Both have a 20 × 34 × 26 mm listed envelope; nominal motor masses are 23 g and 18 g. Four XC motors add 20 g compared with using XL for all eleven positions. Stall torque is not continuous walking torque.

고관절 피치는 상체 중력과 보행 부하를 받으므로 강한 모터를 우선 배치합니다. 무릎 피치도 웅크림/지지 자세에서 다음으로 큰 부하가 예상되는 시상면 관절입니다. 이는 초기 배치이며 토크 검증은 아닙니다. 최종 선정에는 완성 로봇 질량·무게중심·목표 동작과 모터 토크-속도/전류 자료가 필요합니다. 5 V 기준 ROBOTIS 표시 정지 토크는 XC330-M288 0.93 N·m, XL330-M288 0.52 N·m입니다. 두 모터의 표기 외형은 20 × 34 × 26 mm이며 명목 모터 질량은 각각 23 g, 18 g입니다. XC 4개는 11개 모두 XL일 때보다 20 g을 추가합니다. 정지 토크는 지속 보행 토크가 아닙니다.

At 5 V, the listed stall-current sum is about **17.5 A** for 4 XC330 + 7 XL330. This is not expected walking current, but the proposed 10/11 A converter and motor wiring need transient and current-limit tests. Keep motor power off the controller board; the TTL DYNAMIXEL control bus can remain the same. Details are in [electronics and power](ELECTRONICS.md).

5 V에서 XC330 4개와 XL330 7개의 표시 정지전류 합은 약 **17.5 A**입니다. 보행 예상 전류는 아니지만 10/11 A 변환기 후보와 모터 배선의 과도응답·전류 제한 시험이 필요합니다. 모터 전원을 제어기 보드에 통과시키지 마세요. TTL DYNAMIXEL 제어 버스는 그대로 사용할 수 있습니다. 자세한 내용은 [전장·전원 문서](ELECTRONICS.md)를 참고하세요.

## Motor CAD source and head horn / 모터 CAD 원본과 머리 혼

The uploaded XL,XC-330 STEP is byte-identical to the M288 case/horn STEP already used in v0.6 (SHA-256 e2f7b060801a1d1a21f23bca2554f29a402f7d73b8498cb201c9e6adf3139eb6). It provides the same exterior case, horn, idler, screws and connectors for both motor instances; it does not model XC coreless versus XL cored internal parts. v0.7 identifies the motor type in assembly names, colors, and joint metadata without fabricating hidden internals.

첨부 XL,XC-330 STEP은 v0.6에서 사용한 M288 케이스/혼 STEP과 바이트 단위로 동일합니다(SHA-256 e2f7b060801a1d1a21f23bca2554f29a402f7d73b8498cb201c9e6adf3139eb6). 공통 외부 케이스·혼·아이들러·나사·커넥터를 제공하지만 XC 코어리스와 XL 코어드 모터 내부는 모델링하지 않습니다. v0.7은 내부를 임의로 만들지 않고 부품 이름·색·조인트 메타데이터로 모터를 구분합니다.

The neck horn looked partly cut because the earlier boolean clipped the complete head carrier against an ellipsoid. v0.7 preserves the full two-sided output yoke and trims only the surrounding internal support frame. Check horn fastener access and head-shell clearance with a printed fit sample.

목 모터 혼이 일부 잘려 보인 것은 이전 Boolean이 머리 캐리어 전체를 타원체로 잘랐기 때문입니다. v0.7은 양쪽 출력 요크 전체를 보존하고 주변 내부 지지 프레임만 다듬습니다. 출력 시편에서 혼 체결 접근성과 머리 쉘 간격을 확인해야 합니다.

## Geometry and verification / 형상 및 검증

+X is forward, +Y left, +Z up. Hip spacing is 108 mm. Left hip axis centers are P (0,54,230), R (-18,54,194), Y (0,54,158) mm; knee pitch is (0,54,93), ankle pitch (0,54,28). R sits 18 mm rearward, with 40.2 mm P-R and R-Y distances. Thigh and shin pitch-axis spacing are each 65 mm. Each foot outline is 88 × 66 mm. The full shell STEP round-trips with 244 valid solids; the internal assembly with 203. Variant solid counts, bounds and hashes are in [the v0.7 manifest](../hardware/mechanical/cad/v0.7/PRY_variant_manifest.json).

+X는 전방, +Y는 왼쪽, +Z는 위쪽입니다. 고관절 간격은 108 mm입니다. 왼쪽 고관절 중심은 P (0,54,230), R (-18,54,194), Y (0,54,158) mm이며 무릎 피치는 (0,54,93), 발목 피치는 (0,54,28)입니다. R은 18 mm 뒤쪽이며 P-R, R-Y 간격은 각각 40.2 mm입니다. 허벅지·종아리 피치축 간격은 각각 65 mm이고 발 외곽은 88 × 66 mm입니다. 전체 외장 STEP는 244개, 내부 조립체는 203개 유효 솔리드로 재가져오기됩니다. 변형별 솔리드 개수·외곽·해시는 [v0.7 매니페스트](../hardware/mechanical/cad/v0.7/PRY_variant_manifest.json)에 있습니다.

These are packaging and STEP-integrity checks only. They do not establish structural strength, fastener suitability, current/thermal margin, full-motion clearance, balance or walking. Verify electronics against purchased hardware, measure the assembled mass/COM, run both-leg motion sweeps, and test one supported leg before setting gait limits.

이 검사는 패키징 및 STEP 형상 유효성만 확인합니다. 구조 강도·체결재 적합성·전류/발열 여유·전체 가동 간섭·균형·보행을 검증하지 않습니다. 구매한 전장 부품과 실물 크기를 대조하고, 조립 질량/무게중심을 측정하며, 양다리 동작 간섭 검사와 지지 상태의 한쪽 다리 시험 후 보행 제한을 정하세요.
