[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Design decisions

| Date | Decision or proposal | Status | Impact |
| --- | --- | --- | --- |
| 2026-09-29 | SNU GOM / 스누곰 name | User selected | Project/documentation identity |
| 2026-09-29 | Five XL330-M288-T per leg, ten lower-body motors | Confirmed | Lower-body DOF and quantities |
| 2026-09-29 | Hip roll/pitch, knee pitch, ankle pitch/roll | Proposed | CAD, URDF and control interfaces |
| 2026-09-29 | One neck-pitch XL330, straight nose camera and fixed arms; 11 motors total | Proposed | Mass, power and budget |
| 2026-09-29 | Onboard HRI computer, external large-model APIs/PC, local motion supervision + MCU | Revised HRI proposal | Latency, communications and power |
| 2026-09-29 | OpenRB-150, IMU, 2S battery and 5V UBEC | Candidates | Ratings, mass and availability need validation |
| 2026-09-29 | Repository renamed to `mjcha924/snu-gom`; English/Korean documentation | User requested | Links and team onboarding |

Add each new decision with its issue, rationale, rejected alternatives, affected files and validation evidence. Even if each leg retains five joints, changing the arrangement (for example adding hip yaw) requires a separate decision and model revision.

---

<a id="한국어"></a>

# 설계 결정 기록

| 날짜 | 결정 또는 제안 | 상태 | 변경 영향 |
| --- | --- | --- | --- |
| 2026-09-29 | 이름 SNU GOM / 스누곰 | 사용자 선택 | 문서·프로젝트 표시명 |
| 2026-09-29 | 다리당 XL330-M288-T 5개, 하체 10개 | 확정 | 하체 자유도·구매 수량 |
| 2026-09-29 | 고관절 roll/pitch, 무릎 pitch, 발목 pitch/roll | 제안 | CAD·URDF·제어 인터페이스 |
| 2026-09-29 | 목 피치 XL330 1개·정면 코 카메라·고정 팔, 전체 11개 | 제안 | 질량·전원·예산 |
| 2026-09-29 | 온보드 HRI·외부 대형 모델 API/PC·로컬 모션 감독 + MCU | HRI 변경안 | 지연·통신·전원 |
| 2026-09-29 | OpenRB-150, IMU, 2S 배터리와 5V UBEC | 후보 | 정격·질량·재고 검증 필요 |
| 2026-09-29 | 저장소 `mjcha924/snu-gom` 및 영어·한국어 문서 | 사용자 요청 | 링크·팀 온보딩 |

새 결정은 관련 Issue, 선택 이유, 포기한 대안, 영향을 받는 파일, 검증 증거를 이 표 아래에 추가합니다. 두 다리 5축을 유지해도 hip yaw 채택 등 관절 구성 변경은 별도 결정과 모델 버전 변경이 필요합니다.

## 2026-09-29 HRI / HRI 변경

Confirmed user requirements: human interaction, API connectivity, camera, microphone and speaker; lens at the bear nose. Proposed implementation: Pi 4 + retained OpenRB-150 + separate logic power. See [HRI.md](HRI.md). Latest update: the user requested head tilt; one neck-pitch motor is included, keeping five motors per leg.

사용자 확정 요구: HRI·API·카메라·마이크·스피커, 렌즈는 곰 코 위치. 구현 제안은 Pi 4 + OpenRB-150 유지 + 별도 로직 전원이며 [HRI.md](HRI.md)에 기록합니다. 최신 변경은 머리 틸트이며 목 피치 1개를 추가하고 다리당 5개를 유지합니다.
