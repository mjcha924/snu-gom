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
