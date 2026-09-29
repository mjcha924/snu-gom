[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Five-person collaboration

These are proposed roles. Assign actual GitHub accounts at kickoff; the repository owner is not automatically M1. Each owner leads implementation and asks a neighboring area to review interfaces.

| Slot | Area | Main paths | First deliverable | Default reviewer |
| --- | --- | --- | --- | --- |
| M1 | Mechanical / CAD | `hardware/mechanical/`, `robot/` | One-leg CAD and joint ranges | M4 |
| M2 | Electronics / power / purchasing | `hardware/electronics/`, `hardware/bom/` | Wiring, current budget and quotes | M3 |
| M3 | MCU / communications / firmware | `firmware/`, `docs/INTERFACES.md` | One-motor communication, feedback and watchdog test | M2 |
| M4 | Model / simulation / RL | `simulation/`, `tools/`, `robot/` | Frame/joint/mass validation and baseline locomotion | M1 |
| M5 | Integration / testing / schedule | `tests/`, `docs/experiments/`, `docs/ROADMAP.md` | Repeatable tests, fixtures and integrated demo | Affected area owner |

### Daily workflow

1. Put one owner, one reviewer and acceptance criteria in an issue. Link dependencies when blocked.
2. Create a short-lived branch from current main, such as `mech/12-ankle-bracket`, `elec/13-power`, `fw/14-telemetry`, `sim/15-model` or `test/16-stand`. Avoid permanent personal branches.
3. Open a draft PR early to share CAD links or interface changes. Run checks and mark it ready when complete.
4. Have the neighboring area review, then squash merge. Changes to models/protocols need both affected areas to agree. Delete the branch after merging.

### Shared files

`robot/config.json` is the source of truth for joint names, order, units and logical IDs. Regenerate `robot/snu_gom.urdf` and update affected code/docs in the same PR. Use task-specific Onshape workspaces and include a named version in the PR. Agree on editing boundaries before changing the same main assembly.

Suggested weekly meeting: 30 minutes, split into 10 minutes each for evidence, blocked interfaces and next tasks. The team chooses the time. M5 copies `docs/meetings/TEMPLATE.md` to record decisions.

### GitHub settings still needed

This is a personally owned private repository. Documentation does not activate invitations, permissions or protection rules.

- The owner verifies accounts and grants access in Settings → Collaborators. No teammates have been invited by this setup.
- `.github/CODEOWNERS` currently falls back to the verified repository owner. Replace area owners after collaborators have write access.
- If the account plan supports private-repository protection, require PRs, one approval, dismissal of stale approvals, resolved conversations and the successful `gom-checks` check on main. Select the actual check name in the UI. These settings have not been applied.
- An optional Project can use Backlog → Ready → In progress → Review → Done. Issues already provide a usable task list.

See the [research page](RESEARCH.md) for a role-based reading plan and note template.

### Starter tasks

| Slot | Issue |
| --- | --- |
| M1 | [#1 One-leg CAD validation](https://github.com/mjcha924/snu-gom/issues/1) |
| M2 | [#2 Power and procurement](https://github.com/mjcha924/snu-gom/issues/2) |
| M3 | [#3 Single-motor communication](https://github.com/mjcha924/snu-gom/issues/3) |
| M4 | [#4 Model and learning environment](https://github.com/mjcha924/snu-gom/issues/4) |
| M5 | [#5 Roles and repeatable integration tests](https://github.com/mjcha924/snu-gom/issues/5) |

---

<a id="한국어"></a>

# 5인 협업

역할은 제안이며 각 담당자와 검토자의 GitHub 계정은 첫 미팅에서 정합니다. 프로젝트 소유자가 M1이라고 가정하지 않습니다. 담당자가 실행을 주도하되 인접 영역의 검토자가 인터페이스를 확인합니다.

| 슬롯 | 담당 영역 | 주요 경로 | 첫 결과물 | 기본 검토자 |
| --- | --- | --- | --- | --- |
| M1 | 기구·CAD | `hardware/mechanical/`, `robot/` | 한쪽 다리 CAD와 가동 범위 | M4 |
| M2 | 전장·전원·구매 | `hardware/electronics/`, `hardware/bom/` | 배선도·전류 예산·실구매 견적 | M3 |
| M3 | MCU·통신·펌웨어 | `firmware/`, `docs/INTERFACES.md` | 1축 통신·피드백·watchdog 시험 | M2 |
| M4 | 모델·시뮬레이션·RL | `simulation/`, `tools/`, `robot/` | 좌표·관절·질량 검증 및 기준 보행 | M1 |
| M5 | 통합·시험·일정 | `tests/`, `docs/experiments/`, `docs/ROADMAP.md` | 반복 시험 규약·지그·통합 데모 | 영향받는 영역 담당자 |

## 하루 작업

1. Issue 하나에 담당자 1명, 검토자 1명, 완료 조건을 기록합니다. 대기 사유는 의존 Issue 링크로 남깁니다.
2. 최신 main에서 `mech/12-ankle-bracket`, `elec/13-power`, `fw/14-telemetry`, `sim/15-model`, `test/16-stand`처럼 짧은 브랜치를 만듭니다. 개인별 장기 브랜치는 만들지 않습니다.
3. 완성 전에도 Draft PR로 CAD 링크나 인터페이스 변경을 공유합니다. 완료 시 검사를 실행하고 review-ready로 바꿉니다.
4. 인접 담당자가 확인한 PR을 squash merge합니다. 모델 또는 프로토콜 변경은 관련 두 영역이 함께 확인합니다. 브랜치는 merge 후 삭제합니다.

## 공통 파일 충돌 줄이기

`robot/config.json`이 관절 이름·순서·단위·논리 ID의 기준입니다. 이를 바꾸는 PR은 `robot/snu_gom.urdf`를 재생성하고 영향받는 코드·문서를 함께 수정합니다. CAD를 편집할 때는 작업별 Onshape workspace를 사용하고 PR에 named version 링크를 남깁니다. 같은 메인 어셈블리를 동시에 수정하기 전에 Issue에서 편집 범위를 나눕니다.

주 1회 30분 미팅을 제안합니다: 지난주 증거 10분, 막힌 인터페이스 10분, 다음주 담당 작업 10분. 시간은 팀 합의로 결정합니다. M5가 `docs/meetings/TEMPLATE.md`를 복사하여 기록합니다.

## 아직 필요한 GitHub 설정

현재 저장소는 개인 소유 private repo입니다. 실제 초대·권한·보호 규칙은 문서 파일만으로 활성화되지 않습니다.

- 소유자가 Settings → Collaborators에서 팀원 계정을 확인하고 접근 권한을 부여합니다. 아직 계정이 없어 초대하지 않았습니다.
- `.github/CODEOWNERS`의 기본 소유자는 현재 repo owner입니다. 팀원이 write 권한을 얻은 후 각 경로를 실제 담당자 계정으로 바꿉니다.
- 계정 플랜이 private repo 보호를 지원하면 main에 PR 필수, 승인 1명, 새 커밋 시 승인 무효화, 대화 해결, `gom-checks` 통과를 설정합니다. 실제 성공한 check 이름을 UI에서 선택합니다. 이 설정은 아직 적용하지 않았습니다.
- Projects를 사용한다면 Backlog → Ready → In progress → Review → Done 열을 만들고 Issue를 연결합니다. 기본 작업 목록은 Issues만으로도 사용할 수 있습니다.

역할별 자료조사와 기록 양식은 [자료조사 페이지](RESEARCH.md)를 참고하세요.

## 첫 작업 이슈

| 슬롯 | 시작 이슈 |
| --- | --- |
| M1 기구/CAD | [#1 한쪽 다리 CAD 검증](https://github.com/mjcha924/snu-gom/issues/1) |
| M2 전장/구매 | [#2 전원·구매 계획](https://github.com/mjcha924/snu-gom/issues/2) |
| M3 펌웨어 | [#3 단일 모터 통신](https://github.com/mjcha924/snu-gom/issues/3) |
| M4 모델/시뮬레이션 | [#4 모델·학습 환경](https://github.com/mjcha924/snu-gom/issues/4) |
| M5 통합/시험 | [#5 역할·반복 시험 운영](https://github.com/mjcha924/snu-gom/issues/5) |
