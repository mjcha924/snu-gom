# Mechanical CAD / 기구 CAD

**Current package / 현재 패키지: `SNU_GOM_XL330_Prototype_v03.zip` · 2026-10-04**

The owner has the STEP/STL/source package. Binary CAD remains outside Git; this directory records revision, checksums, parameters, joint frames and verification summaries. No permanent public download URL or new Onshape document has been created. / 프로젝트 소유자에게 STEP·STL·소스 패키지를 전달합니다. CAD 바이너리는 Git 외부에 두고 이 폴더에는 버전·체크섬·치수·관절·검사 결과를 기록합니다. 영구 공개 다운로드 URL·새 Onshape 문서는 아직 없습니다.

## What changed / 변경 내용

BD-X and Olaf informed lighter segmented skins, rear ventilation and replaceable 2 mm sole pads. The baseline leaves joint gaps open; the more concealed soft-sleeve option is a separate neutral study. Five XL330-M288-T motors per leg, neck pitch, straight nose camera, supplied motor/horn geometry and structural brackets are retained.

BD-X·Olaf를 반영해 분절형 외장을 경량화하고 후면 통풍·교체형 2 mm 패드를 추가했습니다. 기본안의 관절 틈은 열려 있으며 은폐형 유연 슬리브는 중립 비교안으로 분리합니다. 다리당 XL330-M288-T 5개·목 피치·정면 코 카메라·제공 모터/혼·구조 브래킷은 유지합니다.

- [Paper-to-design rationale / 논문 반영](../../docs/PAPER_DESIGN.md)
- [Geometry and assembly / 형상·조립](../../docs/CAD_GEOMETRY.md)
- [Verification and foot-collision findings / 검사·양발 간섭](../../docs/CAD_VERIFICATION.md)
- [Motion authoring specification / 동작 설계 입력](../../motion/design/README.md)

**Prototype limits:** the CAD is not fabrication-qualified or a trained walking robot. Two inward hip-roll samples cause opposite-foot interference; thin skins, pad material, screw retention, head torque, cables and cooling need physical tests. Existing ten-joint URDF remains a proxy. / 제작 확정본이나 학습된 보행 로봇이 아닙니다. 두 내측 고관절 롤 표본에서 반대 발 간섭이 있으며 얇은 외장·패드·나사·목 토크·배선·방열 검증과 URDF 갱신이 필요합니다.
