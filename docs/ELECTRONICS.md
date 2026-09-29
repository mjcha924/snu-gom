[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Electronics and power draft

XL330-M288-T uses half-duplex TTL communication and an internal driver. Recommended voltage is 5V; allowed range is 3.7–6V. Do not connect a 2S pack directly to the motors.

Candidate path: 2S battery → disconnect switch/fuse → 5V motor converter → external distribution harness → left/right motor branches. Review logic power for the controller and IMU, and connect common GND and communication DATA. Do not parallel outputs from different regulators.

OpenRB-150 lists a 3A DYNAMIXEL current limit. Do not route the full ten-motor load through the board or one servo cable. Review external power injection, separated power wiring and DATA/GND paths in a schematic. Check backfeeding between USB and external supplies.

At 5V, 1.5A stall current per motor gives 15A for ten motors. This is not an average walking-current estimate. Do not assume a candidate 10A UBEC handles every transient: size it from actual current limiting, peaks, voltage sag and heat. Recalculate if adding a neck.

M2 delivers a schematic, connector ratings, power budget, low-voltage monitoring/cutoff, converter settings, purchasing candidates and one-leg load tests. Review communication and power sequencing with M3.

Manufacturer references: [XL330](https://www.robotis.com/shop/item.php?it_id=902-0163-000), [OpenRB-150](https://www.robotis.com/shop/item.php?it_id=902-0183-000). Pricing and candidates are in the [BOM](../hardware/bom/README.md).

---

<a id="한국어"></a>

# 전장과 전원 초안

XL330-M288-T는 TTL 반이중 통신과 내장 드라이버를 사용합니다. 권장 5V, 허용 3.7~6V입니다. 2S 팩을 모터에 직접 연결하지 않습니다.

후보 연결: 2S 배터리 → 차단 스위치·퓨즈 → 5V 모터 변환기 → 외부 분배 하네스 → 좌우 모터 분기. 제어기·IMU는 로직 전원을 검토하고 공통 GND 및 통신 DATA를 연결합니다. 서로 다른 레귤레이터의 출력을 병렬로 연결하지 않습니다.

OpenRB-150의 DYNAMIXEL 허용전류는 3A로 표시되어 있습니다. 10축의 전류를 보드나 한 개 서보 케이블로 모두 통과시키는 연결은 채택하지 않습니다. 외부 전원 주입, 전원선 분리, DATA/GND 연결 방식은 회로도로 검토합니다. USB 전원과 외부 전원의 역급전도 확인합니다.

5V에서 모터당 스톨 전류 1.5A이므로 10축 합산 스톨 전류는 15A입니다. 이를 보행 평균 전류로 사용하지 않습니다. 10A UBEC 후보가 모든 순간 부하를 감당한다고 가정하지 말고, 실제 전류 제한·피크·전압 강하·발열로 용량을 정합니다. 목 추가 시 다시 산정합니다.

M2 결과물: 배선도, 커넥터별 정격, 전원 예산, 저전압 감시/차단, 변환기 설정, 구매 후보, 단일 다리 부하 시험. M3와 통신·전원 시퀀스를 함께 검토합니다.

제조사 근거: [XL330](https://www.robotis.com/shop/item.php?it_id=902-0163-000), [OpenRB-150](https://www.robotis.com/shop/item.php?it_id=902-0183-000). 가격·후보는 [BOM](../hardware/bom/README.md)을 따릅니다.
