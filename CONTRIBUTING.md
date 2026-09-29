# Making changes / 변경 올리기

Anyone can work on any part of SNU GOM. Use one shared workflow for code, CAD, electronics and documents. Keep shared project information in English and Korean.

누구나 프로젝트의 필요한 부분을 수정할 수 있습니다. 코드·CAD·전장·문서에 같은 절차를 적용하고 공통 안내는 영문·한글을 함께 갱신합니다.

## 1. Start a branch / 브랜치 만들기

```bash
git switch main
git pull --ff-only
git switch -c feature/nose-camera
```

Use a short descriptive name: `feature/...`, `fix/...`, `docs/...`, or `cad/...`. Before editing a shared CAD assembly, note the intended change in an issue so simultaneous edits are visible.

변경 내용을 설명하는 짧은 브랜치 이름을 사용합니다. 공유 CAD 조립체를 수정하기 전 Issue에 작업 내용을 남겨 동시 편집을 확인합니다.

## 2. Make focused commits / 변경 단위로 커밋하기

Use `type: short description`, for example:

```text
feat: add speech status endpoint
fix: correct left ankle axis
cad: add neck pitch bracket
docs: explain the nose camera
```

Types: `feat`, `fix`, `cad`, `docs`, `test`, `chore`. English or Korean summaries are welcome. Explain why the change is needed in the body when it is not obvious. Keep generated exports with the source/version that produced them. Do not commit API keys, recordings with personal information, build caches or unrelated large binaries.

제목은 `유형: 짧은 설명`으로 작성하며 한글도 가능합니다. 이유가 명확하지 않으면 본문에 적습니다. CAD 내보내기 파일에는 원본·버전 정보를 연결하고 API 키·개인정보 녹음·빌드 캐시·무관한 대용량 파일은 올리지 않습니다.

```bash
git add <changed-files>
git diff --cached
git commit -m "cad: add neck pitch bracket"
git push -u origin feature/nose-camera
```

## 3. Open a pull request / PR 만들기

Describe the problem, what changed and how it was checked. Add a screenshot for visible geometry changes; include units, CAD version and affected joint frames for mechanical changes. Keep unfinished work as a draft. Resolve relevant CI failures and review comments before merging; prefer a squash merge for a single coherent change.

문제·변경 내용·확인 방법을 적습니다. 형상 변경은 이미지, 단위, CAD 버전, 영향받는 관절 좌표를 첨부합니다. 미완성 작업은 draft로 두고 관련 CI 오류·검토 의견을 해결한 뒤 병합합니다. 하나의 변경에는 squash merge를 권장합니다.

## 4. Check what you changed / 필요한 검증

```bash
python tools/check_project.py
python -m unittest discover -s tests -v
```

These check the existing proxy model and budget. They do not establish real motor fit, power capacity or walking. For hardware changes, record measurements and unresolved points in `docs/experiments/`. For CAD changes, record clearance, fasteners, mass assumptions and the matching simulation revision.

위 검사는 기존 도형 모델·예산 일치 검사입니다. 실물 체결·전원·보행을 검증하지 않습니다. 하드웨어는 `docs/experiments/`에 측정값·미해결점을, CAD는 간섭·체결품·질량 가정·대응 모델 버전을 기록합니다.
