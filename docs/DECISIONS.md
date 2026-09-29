[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Design decisions

| Date | Decision or proposal | Status | Impact |
| --- | --- | --- | --- |
| 2026-09-29 | SNU GOM / 스누곰 name | User selected | Project/documentation identity |
| 2026-09-29 | Five XL330-M288-T per leg, ten total | Confirmed | Lower-body DOF and quantities |
| 2026-09-29 | Hip roll/pitch, knee pitch, ankle pitch/roll | Proposed | CAD, URDF and control interfaces |
| 2026-09-29 | Fixed head/arms initially; optional two-axis neck | Proposed | Mass, power and budget |
| 2026-09-29 | External PC inference plus MCU motor communication | Proposed | Latency, communications and power |
| 2026-09-29 | OpenRB-150, IMU, 2S battery and 5V UBEC | Candidates | Ratings, mass and availability need validation |
| 2026-09-29 | Five responsibility areas | Team workflow proposal | Actual accounts still to be assigned |
| 2026-09-29 | Repository renamed to `mjcha924/snu-gom`; English/Korean documentation | User requested | Links and team onboarding |

Add each new decision with its issue, rationale, rejected alternatives, affected files and validation evidence. Even if each leg retains five joints, changing the arrangement (for example adding hip yaw) requires a separate decision and model revision.

---

<a id="한국어"></a>

# 설계 결정 기록

| 날짜 | 결정 또는 제안 | 상태 | 변경 영향 |
| --- | --- | --- | --- |
| 2026-09-29 | 이름 SNU GOM / 스누곰 | 사용자 선택 | 문서·프로젝트 표시명 |
| 2026-09-29 | 다리당 XL330-M288-T 5개, 총 10개 | 확정 | 하체 자유도·구매 수량 |
| 2026-09-29 | 고관절 roll/pitch, 무릎 pitch, 발목 pitch/roll | 제안 | CAD·URDF·제어 인터페이스 |
| 2026-09-29 | 초기 머리·팔 고정, 목 2축 선택 | 제안 | 질량·전원·예산 |
| 2026-09-29 | 외부 PC 추론 + MCU 모터 통신 | 제안 | 지연·통신·전원 |
| 2026-09-29 | OpenRB-150, IMU, 2S 배터리와 5V UBEC | 후보 | 정격·질량·재고 검증 필요 |
| 2026-09-29 | 5인 담당 영역 분리 | 팀 운영안 | 실명·계정 배정 필요 |
| 2026-09-29 | 저장소 `mjcha924/snu-gom` 및 영어·한국어 문서 | 사용자 요청 | 링크·팀 온보딩 |

새 결정은 관련 Issue, 선택 이유, 포기한 대안, 영향을 받는 파일, 검증 증거를 이 표 아래에 추가합니다. 두 다리 5축을 유지해도 hip yaw 채택 등 관절 구성 변경은 별도 결정과 모델 버전 변경이 필요합니다.
