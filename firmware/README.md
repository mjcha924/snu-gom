[English](#english) | [한국어](#한국어)

<a id="english"></a>

# M3 firmware

There is no firmware driving real motors yet. OpenRB-150 is a candidate. Starting from `docs/INTERFACES.md`, implement single-motor ID verification, position reads, measured zero/direction/angle limits and status packets first.

Next measure ten-axis read/write rate and dropped packets. Validate command timeout, low voltage, overheating and restart behavior in a fixture. Record successful board/library/firmware versions and wiring. Do not share device-specific calibration as repository defaults.

---

<a id="한국어"></a>

# M3 펌웨어

아직 실물 모터를 구동하는 펌웨어는 없습니다. OpenRB-150은 후보입니다. `docs/INTERFACES.md`를 바탕으로 1축의 ID 확인, 현재 위치 읽기, 영점·방향·각도 한계 측정, 상태 패킷을 먼저 구현합니다.

다음으로 10축 읽기/쓰기 주기와 누락률을 측정하고 command timeout, 저전압, 과열, 재시작 동작을 지그에서 검증합니다. 성공한 보드·라이브러리·firmware 버전과 배선도를 기록합니다. 실제 calibration을 repo 기본값처럼 공유하지 않습니다.
