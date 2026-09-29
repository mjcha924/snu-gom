[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Contributing to SNU GOM

Follow [TEAM.md](docs/TEAM.md) for areas and reviewers. Keep each PR focused on one reviewable change. English, Korean or both are welcome in discussion; update both language sections when changing shared documentation.

```bash
git switch main
git pull --ff-only
git switch -c mech/12-ankle-bracket
# After making changes:
python tools/check_project.py
python -m unittest discover -s tests -v
git add <changed-paths>
git commit -m "Describe the change"
git push -u origin mech/12-ankle-bracket
```

Include the linked issue, motivation, affected areas, checks actually run, and a CAD named version or logs. Mark unmeasured mass, current and joint limits as estimates. Agree with affected owners before changing joint names, axes, motor IDs or units.

For mechanical changes, update `robot/config.json` and interference/mass records, then run `python tools/generate_robot.py`. Do not edit the generated URDF directly. Onshape is the manufacturing CAD source; share STEP/STL through external version links under the current repository policy.

Specify whether evidence covers CPU syntax/contracts, simulator import, physics, training or hardware. Passing CPU checks does not demonstrate walking. Do not commit tokens, personal calibration, large checkpoints or logs.

If modifying `motion/`, also run its existing CPU checks. Do not overwrite nine-joint legacy data with ten-joint biped data.

---

<a id="한국어"></a>

# SNU GOM 기여 방법

팀의 담당 영역과 검토자는 [TEAM.md](docs/TEAM.md)를 따릅니다. 한 PR은 검토 가능한 하나의 변경을 다룹니다.

```bash
git switch main
git pull --ff-only
git switch -c mech/12-ankle-bracket
# 작업 후
python tools/check_project.py
python -m unittest discover -s tests -v
git add <수정한-경로>
git commit -m "Describe the change"
git push -u origin mech/12-ankle-bracket
```

PR에 연결 Issue, 변경 이유, 영향받는 영역, 실제 실행한 검사, CAD named version 또는 로그를 넣습니다. 측정하지 않은 질량·전류·가동 범위는 추정으로 표시합니다. 다른 영역의 관절 이름·축·모터 ID·단위를 합의 없이 바꾸지 않습니다.

기구 변경: `robot/config.json` 및 간섭/질량 기록을 갱신하고 `python tools/generate_robot.py`를 실행합니다. 생성된 URDF는 직접 편집하지 않습니다. Onshape가 제조 CAD의 원본이며 STEP/STL은 현재 저장소 정책대로 외부 버전 링크로 공유합니다.

검증 결과에는 CPU 문법/명세 검사, 시뮬레이터 import, 물리 시험, 학습, 실물 시험 중 무엇을 했는지 적습니다. CPU 통과를 보행 성공으로 적지 않습니다. 토큰, 개인 캘리브레이션, 대형 학습 체크포인트와 로그는 커밋하지 않습니다.

기존 `motion/`을 고쳤다면 이전 워크플로의 CPU 검사도 실행합니다. 기존 9축 데이터를 새로운 10축 데이터로 덮어쓰지 않습니다.

논의는 영어·한국어 또는 둘 다 사용할 수 있습니다. 공통 문서를 바꿀 때는 두 언어 섹션을 함께 갱신합니다.
