[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Project brief

SNU GOM is a small bipedal research platform with a bear's short legs and large paws. It uses five joints per leg and ten XL330-M288-T motors. Develop standing and short walks first, then expressive waddles and body tilts.

The baseline has fixed head/arms, an IMU and joint feedback, plus a required nose camera, microphone, speaker and onboard HRI computer. See [HRI](HRI.md). A two-axis neck and foot-contact sensors remain optional. Human-motion imitation, skating and autonomous recovery are outside the current acceptance criteria.

### Proposed acceptance criteria

- Stand on level ground without external support for 30 seconds in at least 8 of 10 trials.
- Move forward 0.5 m on level ground within 30 seconds in at least 7 of 10 trials.
- Record repeated tests of two expressive motions. Trials with human intervention or a tether supporting body weight do not count as independent walking.
- Compare baseline control and learned policies under the same conditions: success rate, time, torso-angle RMS, current and temperature.
- Share CAD, BOM, wiring, model, code, test logs and reproduction instructions.

These are proposed targets for team agreement before testing, not achieved results. If learning or hardware transfer fails, document failure conditions and limitations.

Project period: September 15, 2026–January 30, 2027. See [roadmap](ROADMAP.md), [roles](TEAM.md) and [budget](../hardware/bom/README.md). The submission Word document is separate; use repository Markdown as the collaboratively maintained technical plan.

---

<a id="한국어"></a>

# SNU GOM 프로젝트 개요

SNU GOM은 곰처럼 짧은 다리와 큰 발을 가진 소형 이족보행 연구 플랫폼입니다. 다리 5축씩, XL330-M288-T 10개를 사용합니다. 기립·짧은 보행을 먼저 만들고 뒤뚱거림·몸 기울이기 같은 표현 동작을 확장합니다.

기본안은 고정 머리·팔, IMU·관절 피드백에 필수 코 카메라·마이크·스피커·온보드 HRI 컴퓨터를 추가합니다. [HRI](HRI.md)를 참고하세요. 목 2축·발 접촉 센서는 선택입니다. 사람 동작 모방, 스케이팅, 자율 회복은 현 단계의 완료 조건이 아닙니다.

## 제안 완료 기준

- 평탄한 바닥에서 외부 지지 없이 30초 기립: 10회 중 8회 이상.
- 평지 0.5m 전진을 30초 이내 완료: 10회 중 7회 이상.
- 표현 동작 2종의 반복 시험 기록. 줄이 체중을 지지하거나 사람이 개입한 시험은 독립 보행 성공에서 제외.
- 기준 제어와 학습 정책의 성공률·시간·몸통 각도 RMS·전류·온도를 같은 조건으로 비교.
- CAD, BOM, 배선도, 로봇 모델, 코드, 시험 로그와 재현 안내 공유.

목표는 팀이 시험 전 확정할 제안값이며 달성 실적이 아닙니다. 학습 성공 또는 실물 전이가 불가능하면 실패 조건과 한계 분석을 남깁니다.

활동 기간: 2026.09.15~2027.01.30. [상세 일정](ROADMAP.md), [5인 역할](TEAM.md), [예산](../hardware/bom/README.md)을 참고하세요. 제출용 Word 문서는 별도 작성되어 있으며 본 저장소 Markdown을 팀이 함께 갱신할 기술 계획의 기준으로 사용합니다.
