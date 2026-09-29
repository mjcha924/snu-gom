[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Purchasing budget

`body.csv` and `bench.csv` are version-controlled sources from the Korean Excel BOM dated September 29, 2026. Their numeric fields remain the budget source of truth; additional English text columns translate item descriptions and purchasing assumptions. See [column glossary](COLUMNS.md). Distinguish product URLs, supplier homepages, displayed prices and estimates. Update line amounts when changing quantities/prices; CI checks the arithmetic. `budget.json` defines shipping, contingency and borrowing assumptions.

| Item | Estimated KRW |
| --- | --- |
| Base purchasing subtotal | 707,412 |
| Shipping | 20,000 |
| 15% contingency, rounded up to the next thousand | 107,000 |
| Total baseline request | **834,412** |
| Optional neck, SBC, foot sensors and spare motor | 143,600 additional |
| If test power supply/meters cannot be borrowed | 200,000 additional |

The baseline has ten leg joints, fixed head/arms and external-PC control. Buy mandatory body items and bench items 2, 3, 4 and 7; assume other mandatory bench equipment can be borrowed. Adding a neck requires another power, structure and wiring review.

Body item 5 budgets three 1kg PETG rolls together at KRW 56,100. Related printed parts priced at zero are covered by this pool, not free. Printer fees and outsourced machining are excluded. Horns use two five-piece packs; only cables additional to motor-included cables are budgeted separately.

Prices are not firm quotes. Explicit VAT entries include VAT; others use displayed domestic consumer prices, to be rechecked at checkout. The September 29 check found a 40-day XL330 preparation delay and the candidate UBEC out of stock. Supplier homepages for undecided specifications are not confirmed orderable-product links. M2 must verify quotes and alternatives.

Recalculate with `python tools/check_project.py`. Update this summary and the proposal budget together when prices or quantities change.

---

<a id="한국어"></a>

# 구매 예산

`body.csv`와 `bench.csv`는 2026-09-29 작성한 한국어 Excel BOM의 버전 관리용 자료입니다. 제품 URL, 판매처 링크, 표시가격, 추정을 구분합니다. 수량·단가를 바꾸면 금액 열도 갱신해야 하며 CI가 불일치를 검사합니다. `budget.json`은 배송비·예비비·대여 가정을 담습니다.

| 항목 | 예상 금액 |
| --- | --- |
| 기본 구매 소계 | 707,412원 |
| 배송비 | 20,000원 |
| 예비비 15%, 천 원 올림 | 107,000원 |
| 기본 요청 총액 | **834,412원** |
| 선택 목·SBC·발 센서·예비 모터 추가 | 143,600원 |
| 시험 전원·측정기 대여 불가 시 추가 | 200,000원 |

기본안은 다리 10축, 고정 머리·팔, 외부 PC 제어입니다. 기본 본체 필수 항목과 시험 장비 2·3·4·7번을 구매하고 나머지 필수 시험 장비는 대여를 가정합니다. 목을 추가하면 전원·구조·배선 비용도 재검토합니다.

본체 5번은 PETG 1kg 3롤 공통 재료비 56,100원을 일괄 계상합니다. 관련 출력 부품의 0원은 공통 예산 포함을 뜻합니다. 프린터 사용료·외주 가공은 제외되어 있습니다. 혼은 5개입 2팩, 모터당 포함 케이블 외 추가 배선분만 별도 계상합니다.

단가는 확정 견적이 아닙니다. VAT 명시 항목은 포함가, 그 외는 국내 소비자 표시가를 사용했으며 결제 시 재확인합니다. 공식몰 XL330 배송지연/40일 준비, UBEC 후보 품절을 확인했습니다. 규격 미정 품목의 판매처 홈페이지 링크는 바로 주문 가능한 확정 제품 링크가 아닙니다. M2가 실견적과 대체품을 검토합니다.

재계산: `python tools/check_project.py`. 가격·수량 변경 시 이 요약과 제안서 예산도 같이 갱신합니다.

CSV의 숫자 필드는 기존 예산 기준을 유지하며 영문 텍스트 열은 품명·규격·설계 및 구매 가정을 번역합니다. [열 이름 안내](COLUMNS.md)를 참고하세요.
