# CAD files and status / CAD 파일과 상태

The prototype CAD package contains a full STEP assembly, an internal assembly, a five-joint left leg, separate custom STEP/STL parts and small joint fit specimens. It uses the user-supplied XL/XC-330 motor geometry including horns. The bear nose holds a forward-facing camera; a separate XL330 tilts the head.

프로토타입 CAD 패키지는 전체·내부·한쪽 다리 STEP, 개별 STEP/STL와 관절 시편으로 구성합니다. 제공받은 XL/XC-330 모터·혼 형상을 사용하고 정면 코 카메라와 별도 목 피치를 포함합니다.

Current deliverable: `SNU_GOM_XL330_Prototype_v02.zip`, shared with the project owner. Detailed CAD binaries are not committed here. The version, units and file checksum are recorded in `cad_manifest.json`; a permanent download URL is not yet assigned; no new Onshape document has been created by this update.

현재 결과물은 프로젝트 소유자에게 전달하는 `SNU_GOM_XL330_Prototype_v02.zip`이며 대용량 CAD는 저장소에 추가하지 않습니다. `cad_manifest.json`에 버전·단위·체크섬을 기록했으며 영구 다운로드 URL은 아직 없습니다. 이번 변경으로 새 Onshape 문서를 만들지는 않았습니다.

## v0.2 covers / v0.2 외장

Rounded paw covers, curved hand inlays, removable front/rear leg panels, rear wiring troughs and soft joint sleeves now surround the mechanism. The sleeves are neutral envelopes; they need physical material and cable-motion development. / 둥근 발·곡면 손 패드·분리형 다리 패널·후면 배선 홈·유연 관절 커버를 추가했습니다. 유연 커버는 중립 외곽이며 소재·배선 동작 검증이 필요합니다.

Read [CAD geometry and assembly](../../docs/CAD_GEOMETRY.md) and [revision verification](../../docs/CAD_VERIFICATION.md). / 형상·조립 구조와 버전별 검사 결과는 링크를 참고하세요.

## Before fabrication / 제작 전

- Verify saddle fastening, horn screw engagement and access with one physical motor. / 실물 모터로 새들·혼·나사 체결 확인.
- Check full motion, cables, neck load and shell retention. / 전체 가동 범위·배선·목 하중·외장 고정 확인.
- Record estimated and measured masses separately. / 질량 추정·실측 구분.
- Update the existing proxy URDF to match the chosen CAD revision. / 선택 CAD 버전에 맞춰 도형 URDF 갱신.

See [mechanical design](../../docs/MECHANICAL_DESIGN.md), [HRI](../../docs/HRI.md) and [change guidelines](../../CONTRIBUTING.md).
