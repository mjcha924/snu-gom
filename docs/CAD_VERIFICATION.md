# CAD verification / CAD 검사 결과

**v0.3 · 2026-10-04 · fit and kinematic prototype / 조립·운동학 시안**

## English

| Check | Result | Scope |
| --- | --- | --- |
| Full STEP re-import | **244 valid solids** | Every component is a single valid solid; not a strength or fit certification. |
| Supplier geometry | **165 supplier solids, 11 motors** | Original motor/horn STEP and joint frames preserved. |
| Neutral assembly | No overlap findings in the inherited/delta check | v0.2 baseline plus 35 material-removal operations and two exact new-pad candidate pair checks. This is not a newly repeated all-pairs inspection. |
| Bilateral motion samples | **24 clear; 2 with intersections, out of 26** | Actual selected custom shapes and sole pads, plus conservative 20×34×23 mm motor-case boxes. Both legs and selected torso/head components included. |
| Planning mass | **980.3 g** | Rigid CAD at 1.24 g/cm³, pads at assumed 0.30 g/cm³, and 471 g component allowances. Not measured. |
| Overall bounds | **124.8 × 223.3 × 366.3 mm (X/Y/Z)** | CAD bounding boxes; new pads extend 2 mm below the old sole. |

### Detected interference

With all other joints neutral, `left_hip_roll = −8°` or `right_hip_roll = +8°` moves a paw into the opposite foot. Each case has five intersecting part pairs, involving the cover, sole, bumper and new pad. These are actual custom-geometry intersections, not motor-box false positives. Do not treat these isolated poses as usable motions.

The previous v0.2 screen examined one leg and did not test the opposite foot. The wider v0.3 test reveals this existing packaging limitation. It does not mean the whole mechanism has approved ±8° hip-roll travel.

The coordinated ±4° sway samples, bilateral −15°/+30°/−15° crouch, individual pitch/ankle samples, and neck-up 20°/35° samples have no detected intersections in this screen. **Passing sample points do not certify the continuous path, balance or a full range of motion.** Motor horn motion details, electronics envelopes during motion, cable slack, joint-sleeve deformation, contact dynamics, ground penetration, torque and temperature are not validated by this test.

### Evidence and next decisions

- [`motion_screen_v03.json`](../hardware/mechanical/motion_screen_v03.json): all sample angles and detected pairs.
- [`engineering_summary_v03.json`](../hardware/mechanical/engineering_summary_v03.json): mass assumptions and bounds.
- CAD package: `fit_report.json`, `step_roundtrip.json`, `revision_changes.json`, baseline reports, original reference STEP and reproducible source.
- Print-test 1.2 mm cosmetic skin zones; they are non-structural, but retention and local stiffness still matter.
- Test pad friction/compression, joint fasteners, complete head load, thermal behavior and cable routing on supported hardware.
- Resolve foot collision through coordinated gait design or a later spacing/foot revision after simulation. Do not suppress collision checks to obtain a pass.
- The old ten-joint proxy URDF is **not synchronized** to v0.3. No RL policy or autonomous HRI runtime was added by this CAD update.

## 한국어

| 검사 | 결과 | 범위 |
| --- | --- | --- |
| 전체 STEP 재가져오기 | **유효한 단일 솔리드 244개** | 위상 형상 검사이며 강도·조립 인증이 아님 |
| 제공 모터 형상 | **11모터·공급 솔리드 165개 유지** | 원본 혼 포함 STEP·관절 좌표 유지 |
| 중립 조립체 | 계승/변경분 검사에서 간섭 없음 | v0.2 기준 + 재료 제거 35회 + 새 패드 후보 쌍 정밀 검사 2회. 전체 쌍을 새로 반복한 검사가 아님 |
| 양쪽 다리 자세 | **26개 중 24개 간섭 없음, 2개 간섭** | 실제 선택된 자체 부품·패드와 보수적인 모터 케이스 박스 사용 |
| 계획 질량 | **980.3 g** | 경질 기준 밀도·가정한 폼 밀도·부품 여유값으로 계산, 실측 아님 |
| 전체 외곽 | **X/Y/Z 124.8 × 223.3 × 366.3 mm** | 기존 발판 아래 2 mm 패드 포함 |

다른 축이 모두 중립일 때 **왼쪽 고관절 롤 −8° 또는 오른쪽 +8°**에서 발이 반대쪽 발을 침범합니다. 각 경우 외장·발판·테두리·패드 관련 5쌍이 겹칩니다. 보수적 모터 박스로 인한 오검출이 아니라 실제 자체 부품 간섭입니다.

v0.2 검사는 한쪽 다리만 포함해 반대 발 간섭을 확인하지 못했습니다. 이번 양쪽 검사가 기존 배치 한계를 드러냈으며 ±8°를 허용 가동 범위로 해석하면 안 됩니다.

협응된 ±4° 흔들림, 양쪽 −15°/+30°/−15° 낮춤 자세, 개별 피치·발목 표본, 목 위보기 20°/35°는 검사 범위에서 간섭이 없습니다. **표본 통과는 연속 경로·균형·전체 가동 범위 검증이 아닙니다.** 움직이는 혼 세부 형상·전자부품·배선·유연 외피·지면 접촉·토크·온도는 본 검사가 보장하지 않습니다.

자세별 결과와 질량 가정은 위 JSON 링크에 있습니다. 다음은 얇아진 외장·발 패드·관절 체결·머리 하중·배선·방열 실물 시험, 시뮬레이터 좌표·질량 갱신입니다. 보행 협응 또는 추후 발/간격 수정으로 간섭을 해결하며 검사 제외로 통과시키지 않습니다. 기존 10축 도형 URDF는 **v0.3과 동기화되지 않았고**, 이번 CAD 변경으로 RL 정책·자율 HRI 서버를 구현하지 않았습니다.
