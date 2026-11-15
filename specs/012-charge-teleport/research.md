# Research: 전하 순간이동

- **Decision**: CharacterScene.event_to_world를 GameplayMode에 콜백으로 전달한다.
  **Rationale**: 이미 DPI·viewport 역변환이 존재한다. 엔진 이벤트나 공용 Level 인터페이스를 늘릴 필요가 없다.
  **Alternatives considered**: 이벤트에 월드 좌표를 덧붙이는 방식은 전달 계약을 바꾸므로 제외.
- **Decision**: Character에 중심·도착 가능성·teleport 동작을 둔다.
  **Rationale**: 상태 머신, 선입력, 점프·대시 필드의 소유자가 캐릭터다. 기존 모션 취소는 상태 머신 전이 한 개로 처리한다.
  **Alternatives considered**: 모드에서 캐릭터 내부 필드를 직접 수정하는 방식은 제외.
- **Decision**: 승인 controller.js의 임계 감쇠·위상과 픽셀 보간을 Python/SDL로 이식한다.
  **Rationale**: 단순 두 겹 알파 합성은 중간 밝기를 보존하지 않는다. SDL surface/streaming texture는 설치된 Pico2D가 제공한다.
  **Alternatives considered**: 새 Pillow 의존성·대량 보간 시트·게임 내 JS 런타임은 불필요하다.
- **Decision**: 승인 link.js와 최소 pixelfx 수학/그리기 도우미를 끝점 기반 CPU 래스터로 이식하고 MIT 고지를 보존한다.
  **Rationale**: 고정 길이 시트를 늘리면 중심 굵기와 가지가 왜곡된다. 좌표는 world Y-up에서 효과 local Y-down으로 변환한다.
  **Alternatives considered**: 거리별 시트·단순 직선은 승인 형태를 충족하지 않는다.

참조 아트와 API 조사는 gpt-6.1-sol/medium 읽기 전용으로 확인했다. 외부 검색·새 패키지·서비스는 사용하지 않는다.
