[English](#english) | [한국어](#한국어)

<a id="english"></a>

# Shared interface draft

Source: `robot/config.json`, revision `snu-gom-biped-v0.1-proxy`. Right-handed frame: +X forward, +Y left, +Z up. Units: m, rad, s, kg, A and °C. Joint signs follow each URDF local axis; physical motor orientation and zero offsets must be measured separately.

Joint order: left hip_roll, hip_pitch, knee_pitch, ankle_pitch, ankle_roll, followed by the same right-side order. Logical IDs 1–10 are proposed assignments, not IDs already programmed into servos.

### PC ↔ MCU contract

Choose the transport encoding after bench tests. Initial semantics:

- Command: `schema_version`, `robot_revision`, `sequence`, `positions_rad[10]`. MCU validates length, finite values, angle bounds and revision.
- Telemetry: `sequence`, `device_time_us`, `positions_rad[10]`, `velocities_rad_s[10]`, `currents_A[10]`, `bus_voltage_V`, `temperature_C[10]`, `imu_accel_m_s2[3]`, `imu_gyro_rad_s[3]`, `faults`.
- Agree on observation/command rates after bench measurements. Record learning dt and measured latency consistently. Define synchronization between MCU timestamps and the host monotonic clock.
- Define behavior for dropped packets, stale sequences, sensor errors, low voltage, overheating and command timeout first. Sudden torque-off can topple a standing robot; validate failure behavior in a support fixture.

The repository does not yet implement motor transport for this contract. Temporary URDF limits are not hardware operating limits.

### Model ↔ learning contract

Candidate observations are joint q/dq, torso IMU and the previous command. Actions are ten joint targets. Version normalization, reference pose, action scale and update rate after measurement. Revalidate existing policies whenever model revision or joint order changes.

---

<a id="한국어"></a>

# 공통 인터페이스 초안

현재 기준: `robot/config.json`, revision `snu-gom-biped-v0.1-proxy`. 오른손 좌표계로 +X 전방, +Y 왼쪽, +Z 위쪽. 길이 m, 각도 rad, 시간 s, 질량 kg, 전류 A, 온도 °C. 양쪽 joint axis 부호는 URDF의 로컬 축을 따릅니다. 실제 모터 설치 방향과 영점은 별도 측정값입니다.

관절 배열은 왼쪽 hip_roll, hip_pitch, knee_pitch, ankle_pitch, ankle_roll 다음 오른쪽의 같은 순서입니다. 논리 ID 1~10은 배선·설정 제안이며 실제 서보에 기록된 ID가 아닙니다.

## PC ↔ MCU 계약

전송 인코딩은 벤치 시험 후 선정합니다. 초기 의미 계약은 아래를 따릅니다.

- Command: `schema_version`, `robot_revision`, `sequence`, `positions_rad[10]`. MCU는 길이·유한값·각도 범위와 revision을 검사합니다.
- Telemetry: `sequence`, `device_time_us`, `positions_rad[10]`, `velocities_rad_s[10]`, `currents_A[10]`, `bus_voltage_V`, `temperature_C[10]`, `imu_accel_m_s2[3]`, `imu_gyro_rad_s[3]`, `faults`.
- 관측/명령 주기는 벤치에서 측정 후 합의합니다. 학습 dt와 실측 지연을 동일하게 기록합니다. MCU 타임스탬프와 호스트 단조 시계 간 동기화 방식을 결정합니다.
- 패킷 누락·오래된 sequence·센서 오류·저전압·과열·명령 timeout의 동작을 먼저 정의합니다. timeout 시 갑작스러운 torque-off가 기립 로봇을 넘어뜨릴 수 있으므로 지지 지그에서 실패 동작을 검증합니다.

현재 저장소는 이 계약의 실제 모터 전송 구현을 제공하지 않습니다. 임시 URDF 제한을 실물 동작 한계로 사용하지 않습니다.

## 모델 ↔ 학습 계약

관측은 관절 q/dq, 몸통 IMU와 이전 명령을 후보로 합니다. 행동은 10축 관절 목표값입니다. 정규화, 기준 자세, 행동 스케일, 주기는 실측 후 별도 버전으로 고정합니다. 모델 revision 또는 관절 순서가 바뀌면 기존 정책은 재검증 전 사용하지 않습니다.

## HRI boundary / HRI 경계

[HRI.md](HRI.md) defines high-level behavior/API requests. Dialogue and cloud responses never directly populate `positions_rad[10]`; a validated local controller owns that conversion.
[HRI.md](HRI.md)의 행동·API 요청은 상위 의도이며 대화·클라우드 응답이 `positions_rad[10]`을 직접 채우지 않습니다. 검증된 로컬 제어기가 변환합니다.

## Neck update / 목 피치 추가

The existing configuration above remains the ten-leg-joint proxy contract. The detailed CAD now adds `neck_pitch` (proposed logical ID 11). A future versioned full-body command may append this joint, while the locomotion policy may retain ten leg actions with neck control handled separately. Do not silently send eleven values to the current ten-value interface.

위 기존 설정은 다리 10축 도형 모델 계약입니다. 상세 CAD는 `neck_pitch`(논리 ID 11 제안)를 추가합니다. 전신 명령은 버전을 올려 11축으로 확장하고 보행 정책은 다리 10축과 별도 목 제어로 구성할 수 있습니다. 현재 10개 배열 인터페이스에 11개 값을 임의로 보내지 않습니다.
