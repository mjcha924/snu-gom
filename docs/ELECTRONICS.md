[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Electronics and power draft

**HRI:** Raspberry Pi 4, nose camera, USB microphone/speaker audio, separate regulated logic rail and USB backfeed review. Full wiring, API and packaging plan: [HRI.md](HRI.md).

## Motor interface and power

The 11 actuators are four XC330-M288-T (both leg hip-pitch and knee-pitch joints) and seven XL330-M288-T (the other six leg joints plus neck pitch). Both models use TTL half-duplex DYNAMIXEL communication and operate at 3.7–6.0 V, recommended 5 V. The actuator protocol/controller does not need to change just because two per leg are XC330. Do not connect a 2S pack directly to the motors. [XC330 manufacturer specs](https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/) · [XL330 manufacturer specs](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/).

At 5 V the listed stall currents are 1.80 A per XC330 and 1.47 A per XL330. For 4 XC + 7 XL, the simultaneous-stall sum is 17.49 A. This is a theoretical upper bound, not the expected walking draw, but the current 10/11 A regulator candidates cannot be assumed to supply that bound or its transients. Measure bus current and voltage sag during supported single-leg tests; choose the rail, fuse, wiring, connectors and distribution from measured gait peaks and a safe current-limit strategy.

Candidate power path: 2S battery → disconnect/fuse → regulated motor rail → external distribution harness → left/right branches. Keep logic power separate and tie common ground/data appropriately. OpenRB-150 lists a 3 A DYNAMIXEL current limit; do not route motor power through the controller or one servo lead. Check voltage/current ratings, heat, transient response, USB backfeeding, and low-voltage cutoff. Do not parallel outputs from different regulators.

The XC motors also increase nominal motor mass: 4×23 g + 7×18 g = 218 g total, 20 g above an eleven-XL configuration. Update the weighed payload and hip-pitch/knee-pitch torque calculations once the final hardware and battery are selected. Stall torque is not a continuous walking rating.

Record a schematic, connector ratings, power budget, converter settings, purchase candidates and one-leg load tests. Review communication and power sequencing together. The proposed controller can remain, but its external power path needs validation.

<a id="한국어"></a>

# 전장과 전원 초안

**HRI:** Raspberry Pi 4, 코 카메라, USB 마이크/스피커, 별도 조정 로직 전원 및 USB 역급전을 검토합니다. 배선·API·배치 계획은 [HRI.md](HRI.md)를 따릅니다.

## 모터 통신과 전원

모터 11개는 XC330-M288-T 4개(양쪽 다리 고관절 피치·무릎 피치)와 XL330-M288-T 7개(나머지 다리 6축과 목 피치)입니다. 두 모델 모두 TTL 반이중 DYNAMIXEL 통신, 3.7~6.0 V 입력, 권장 5 V를 사용합니다. 다리 모터 중 2개를 XC330으로 바꾸더라도 통신 프로토콜/제어기를 바꿀 필요는 없습니다. 2S 배터리를 모터에 직접 연결하지 않습니다. [XC330 공식 사양](https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/) · [XL330 공식 사양](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/).

5 V에서 표시된 정지 전류는 XC330당 1.80 A, XL330당 1.47 A입니다. XC 4개와 XL 7개 모두가 동시에 정지할 때 합계는 17.49 A입니다. 이는 보행 평균 소비가 아니라 이론적 상한이지만 현재 후보인 10/11 A 레귤레이터가 이 상한이나 과도전류를 공급한다고 볼 수 없습니다. 지지대를 사용한 한쪽 다리 시험에서 전류와 전압 강하를 측정하고, 실제 보행 피크와 안전한 전류 제한을 기준으로 전원·퓨즈·배선·커넥터·분배를 정하세요.

전원 경로 후보: 2S 배터리 → 차단/퓨즈 → 조정 모터 전원 → 외부 분배 하네스 → 좌우 분기. 로직 전원은 분리하고 공통 접지/통신 DATA를 적절히 연결합니다. OpenRB-150의 DYNAMIXEL 전류 제한은 3 A로 표시되어 있으므로 모터 전원을 제어기나 서보 케이블 한 가닥으로 보내지 않습니다. 전압/전류 정격, 발열, 과도응답, USB 역급전, 저전압 차단을 확인합니다. 서로 다른 레귤레이터 출력을 병렬 연결하지 않습니다.

XC 모터는 명목 질량도 늘립니다. 4×23 g + 7×18 g = 총 218 g으로, XL 11개 구성보다 20 g 증가합니다. 하드웨어/배터리를 확정해 무게를 잰 뒤 고관절 피치와 무릎 피치 토크 계산에 반영하세요. 정지 토크는 지속 보행 토크가 아닙니다.

회로도, 커넥터 정격, 전원 예산, 변환기 설정, 구매 후보 및 한쪽 다리 하중 시험을 기록하세요. 통신과 전원 시퀀스를 함께 검토합니다. 제어기는 그대로 사용할 수 있지만 외부 모터 전원 경로는 검증해야 합니다.
