[English](#english) | [한국어](#한국어)

<a id="english"></a>

# CAD collaboration

The existing [Onshape document](https://cad.onshape.com/documents/70e60901c3f0fdac6b9cd14a/w/8da76927eccdd278710924b6/e/0a419943727577ede2a57301) references the old nine-joint design. It is not validated manufacturing CAD for the current SNU GOM biped.

M1 creates a separate biped workspace and registers a named version in `hardware/mechanical/cad_manifest.json`. Agree on part interfaces, then split work across legs, pelvis and shells. Each PR records before/after images, named version, units, axis positions, mass, fasteners and interference limits. M4 checks simulation frames before docs/models are merged.

Onshape may use mm, but URDF uses m. Export relative to link-local frames; do not scale by visual guesswork. The generated primitive URDF is not a replacement for manufacturing CAD.

---

<a id="한국어"></a>

# CAD 협업

기존 [Onshape 문서](https://cad.onshape.com/documents/70e60901c3f0fdac6b9cd14a/w/8da76927eccdd278710924b6/e/0a419943727577ede2a57301)는 이전 9축 설계의 참고 링크입니다. 최신 SNU GOM 제조 CAD로 검증된 링크가 아닙니다.

M1은 별도 biped workspace를 만들고 named version 링크를 `hardware/mechanical/cad_manifest.json`에 등록합니다. 팀별 부품 인터페이스를 정한 뒤 좌우 다리, 골반, 외장으로 작업을 나눕니다. PR에는 변경 전후 그림, named version, 단위, 축 위치, 질량, 체결 규격, 충돌 범위를 기록합니다. M4가 시뮬레이션 좌표를 확인한 후 main에 문서와 모델을 반영합니다.

Onshape는 mm로 설계해도 URDF에는 m를 사용합니다. 링크 로컬 프레임 기준으로 내보내며, 눈으로만 크기를 맞추지 않습니다. 생성된 기본 도형 URDF는 제조용 CAD를 대체하지 않습니다.
