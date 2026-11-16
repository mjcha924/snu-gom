[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Purchasing budget

`body.csv` and `bench.csv` are version-controlled sources from the Korean Excel BOM dated September 29, 2026. Their numeric fields remain the budget source of truth; additional English text columns translate item descriptions and purchasing assumptions. See [column glossary](COLUMNS.md). Distinguish product URLs, supplier homepages, displayed prices and estimates. Update line amounts when changing quantities/prices; CI checks the arithmetic. `budget.json` defines shipping, contingency and borrowing assumptions.

| Item | Estimated KRW |
| --- | --- |
| Base purchasing subtotal | 1,288,812 |
| Shipping | 20,000 |
| 15% contingency, rounded up to the next thousand | 194,000 |
| Total baseline request | **1,502,812** |
| Optional neck, foot sensors and spare motor | 36,400 additional |
| If test power supply/meters cannot be borrowed | 200,000 additional |

The motor mix is four XC330-M288-T at both hip-pitch and knee-pitch joints, six XL330-M288-T at the other leg joints, and one XL330 neck-pitch motor. The HRI baseline has ten leg joints, fixed arms and a pitching head, a nose camera, USB microphone/audio, speaker and onboard Pi. Large-model inference uses APIs/PC. Buy mandatory body items and bench items 2, 3, 4 and 7; assume other mandatory bench equipment can be borrowed. The neck and HRI additions require load, power and wiring tests.

Body item 5 budgets three 1kg PETG rolls together at KRW 56,100. Related printed parts priced at zero are covered by this pool, not free. Printer fees and outsourced machining are excluded. Horns use two five-piece packs; only cables additional to motor-included cables are budgeted separately.

Prices are not firm quotes. Explicit VAT entries include VAT; others use displayed domestic consumer prices, to be rechecked at checkout. The September 29 check found a 40-day XL330 preparation delay; the XC330 official-shop price was separately checked October 8 at KRW 96,800 including VAT, also with a listed 40-day preparation delay and the candidate UBEC out of stock. Supplier homepages for undecided specifications are not confirmed orderable-product links. Verify quotes and alternatives.

Recalculate with `python tools/check_project.py`. Update this summary and the proposal budget together when prices or quantities change.

---

<a id="한국어"></a>

# 구매 예산

`body.csv`와 `bench.csv`는 2026-09-29 작성한 한국어 Excel BOM의 버전 관리용 자료입니다. 제품 URL, 판매처 링크, 표시가격, 추정을 구분합니다. 수량·단가를 바꾸면 금액 열도 갱신해야 하며 CI가 불일치를 검사합니다. `budget.json`은 배송비·예비비·대여 가정을 담습니다.

| 항목 | 예상 금액 |
| --- | --- |
| 기본 구매 소계 | 1,288,812원 |
| 배송비 | 20,000원 |
| 예비비 15%, 천 원 올림 | 194,000원 |
| 기본 요청 총액 | **1,502,812원** |
| 선택 목·발 센서·예비 모터 추가 | 36,400원 |
| 시험 전원·측정기 대여 불가 시 추가 | 200,000원 |

모터 구성은 각 다리 고관절 피치·무릎 피치의 XC330-M288-T 4개, 나머지 다리 축의 XL330-M288-T 6개, 목 피치 XL330 1개입니다. HRI 기본안은 다리 10축·목 피치 1축·고정 팔·코 카메라·USB 마이크/오디오·스피커·온보드 Pi이며 대형 모델은 API/PC를 사용합니다. 기본 본체 필수 항목과 시험 장비 2·3·4·7번을 구매하고 나머지 필수 시험 장비는 대여를 가정합니다. 목 피치·HRI를 포함해 하중·전원·배선을 검증합니다.

본체 5번은 PETG 1kg 3롤 공통 재료비 56,100원을 일괄 계상합니다. 관련 출력 부품의 0원은 공통 예산 포함을 뜻합니다. 프린터 사용료·외주 가공은 제외되어 있습니다. 혼은 5개입 2팩, 모터당 포함 케이블 외 추가 배선분만 별도 계상합니다.

단가는 확정 견적이 아닙니다. VAT 명시 항목은 포함가, 그 외는 국내 소비자 표시가를 사용했으며 결제 시 재확인합니다. 공식몰 XL330 배송지연/40일 준비와 UBEC 후보 품절을 확인했습니다. XC330은 2026-10-08 공식몰 표시가 96,800원(VAT 포함), 준비 40일로 별도 확인했습니다. 규격 미정 품목의 판매처 홈페이지 링크는 바로 주문 가능한 확정 제품 링크가 아닙니다. 실견적과 대체품을 검토합니다.

재계산: `python tools/check_project.py`. 가격·수량 변경 시 이 요약과 제안서 예산도 같이 갱신합니다.

CSV의 숫자 필드는 기존 예산 기준을 유지하며 영문 텍스트 열은 품명·규격·설계 및 구매 가정을 번역합니다. [열 이름 안내](COLUMNS.md)를 참고하세요.

## HRI revision / HRI 변경

Pi is now required rather than an optional SBC. Rows 33–37 add camera, audio and interface hardware; row27 increases logic-power allowance. New prices are planning estimates with links, not freshly confirmed vendor quotations. The prior ₩834,412 budget is superseded by the HRI total above. API fees/network service are ongoing costs outside this hardware budget.

Pi는 필수로 바뀌었고 34–38번에 카메라·오디오·조작부, 27번에 로직 전원 증액을 반영했습니다. 새 단가는 링크가 있는 계획용 추정이며 판매처 확정 견적은 아닙니다. 이전 834,412원 대신 위 HRI 총액을 사용합니다. API 사용료·통신비는 하드웨어 예산 밖의 운영비입니다.
