# CAD v0.2 verification / CAD v0.2 검사

2026-09-29 · fit prototype / 조립 검토 시안

| Check / 검사 | Result / 결과 |
| --- | --- |
| Full STEP re-import / 전체 STEP 재가져오기 | 250 solids, all valid / 솔리드 250개 모두 유효 |
| Supplier geometry / 공급 형상 | 165 components: 15 × 11 motors; original file and joint coordinates unchanged / 원본·관절 좌표 유지 |
| Custom components / 자체 부품 | Every exported component is one valid solid / 각 부품은 유효 단일 솔리드 |
| Revised neutral interfaces / 수정 중립 형상 | 123 exact candidate-pair checks, 0 overlaps above 0.05 mm³ / 후보 쌍 123개 정밀 검사, 기준 초과 간섭 0 |
| Discrete rigid motion / 이산 강체 자세 | 14 samples, 0 detected overlaps in tested scope / 검사 범위 14자세, 검출 간섭 0 |
| Approx. outside D×W×H / 대략 외곽 깊이×폭×높이 | 124.8 × 223.3 × 364.3 mm |
| Planning mass / 계획용 질량 | 1.05 kg, not measured / 실측 아님 |

## What was checked / 검사 범위

The neutral test compares every changed/new part with nearby supplied motor assemblies, custom parts, electronics and neutral soft sleeves. Unchanged interfaces inherit the v0.1 report's 116 candidate-pair checks and its documented head-carrier construction check. The former nose-bezel overlap has been removed. Exact records are in `fit_report.json`, `baseline_v01_fit_report.json` and `step_roundtrip.json` in the CAD package.

중립 검사는 변경·추가 부품과 주변 실제 모터·자체 부품·전장 외곽·중립 유연 커버를 비교합니다. 변경하지 않은 부위는 v0.1의 후보 쌍 116개 검사와 머리 캐리어의 형상 구성 검사를 계승합니다. 이전 코 베젤 간섭은 제거했습니다. 상세 결과는 CAD 패키지의 JSON에 기록합니다.

The motion screen checks the left leg and neck using actual rigid custom geometry and conservative solid 20×34×23 mm motor-case boxes. Samples: neutral; hip roll ±8°; hip pitch ±15°; knee ±25°; ankle pitch ±15°; ankle roll ±8°; a −15°/+30°/−15° hip/knee/ankle crouch; neck pitch −20° and −35°. These are sampled CAD poses, **not approved operating limits**. The final battery-tray change only removed material. Soft-sleeve changes are outside the rigid screen.

동작 검사는 왼쪽 다리·목의 실제 경질 자체 부품과 보수적인 20×34×23 mm 모터 케이스 박스를 사용합니다. 중립, 고관절 롤 ±8°, 피치 ±15°, 무릎 ±25°, 발목 피치 ±15°·롤 ±8°, 고관절/무릎/발목 −15°/+30°/−15° 굽힘, 목 −20°·−35°를 검사했습니다. 이는 **허용 가동 한계가 아닙니다**. 마지막 배터리 트레이 수정은 재료 제거만 수행했습니다. 유연 커버 변경은 강체 검사 범위 밖입니다.

## Still to establish / 남은 확인

- **Flexible sleeves and wires:** pattern/material, folding, retention, snagging, slack, connector passage and bend radius. The sleeve STEP is a neutral envelope. / **유연 커버·배선:** 패턴·소재·접힘·고정·끼임·여유 길이·커넥터·곡률. STEP는 중립 외곽입니다.
- **Full motion:** continuous sweep, exact moving horns, both legs crossing and ground contact. / **전체 가동:** 연속 궤적·정밀 혼 동작·양다리 교차·지면 접촉.
- **Physical fit:** factory mounting suitability, screw engagement, 3D-print tolerances, cover straps and small grille holes. / **실물 조립:** 모터 체결 용도·나사 깊이·출력 공차·외장 타이·작은 그릴 구멍.
- **Loads and electronics:** torque/current/temperature, neck load, structural deflection, cooling, actual PCB mounts, camera field of view and audio. / **하중·전장:** 토크·전류·발열·목 하중·변형·냉각·실제 기판 고정·카메라 시야·음향.
- **Simulation:** rebuild collision geometry, frames, masses and inertia; the repository's old ten-leg-joint primitive URDF is not synchronized. / **시뮬레이션:** 충돌·좌표·질량·관성을 갱신해야 하며 기존 10축 도형 URDF는 미동기화입니다.

The mass estimate uses 466.59 cm³ of custom geometry at a common reference density of 1.24 g/cm³ (578.6 g), plus rough component allowances. This includes neutral flexible envelopes at the same density; real fabric/elastomer and print settings change the mass. Covers add about 93.1 g to the previous custom-geometry estimate. Walking has not been demonstrated by these checks.

질량은 자체 형상 466.59 cm³에 공통 기준 밀도 1.24 g/cm³를 적용한 578.6 g과 부품 추정값의 합입니다. 유연 커버도 같은 밀도로 계산하므로 실제 천·탄성체·출력 설정에 따라 달라집니다. 이전 자체 형상 추정보다 약 93.1 g 증가했습니다. 이 검사로 보행 성공이 입증된 것은 아닙니다.

**Next build:** one motor fit coupon → one covered leg on a supported fixture → cable/folding tests → representative load tests → updated simulation. / **다음 제작:** 모터 시편 → 지지 지그 위 외장 포함 한쪽 다리 → 배선·접힘 → 대표 하중 → 시뮬레이션 갱신.
