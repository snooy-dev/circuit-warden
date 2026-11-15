# Data Model: 전하 순간이동

- Charge: 고정 position, active(현재 거리 판정), elapsed(공유 3초 위상), value/velocity(전환). value는 0~1이며 dt는 유한한 비음수다. 클릭 판정은 시각 보간 완료를 기다리지 않는다.
- Character: 기존 상태에 중심 좌표와 teleport를 추가한다. 도착은 유한 좌표, 바닥 이상, 현재 화면 수평 여유 안, 상단에 몸이 들어와야 한다. 성공 시 위치/낙하 상태 변경과 선입력 제거를 원자적으로 수행한다.
- TeleportLink: immutable 출발·도착 중심, elapsed, 생성 seed, 프레임 출력. 400ms에 destroy하며 피해/입력/캐릭터 참조는 없다.
- ChargeArt: 장면 소유 PNG 프레임 바이트와 전하별 스트리밍 텍스처. 종료·초기화 실패에서 SDL 포인터를 한 번 해제한다.
