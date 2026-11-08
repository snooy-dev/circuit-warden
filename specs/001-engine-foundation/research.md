# 기술 조사

## Decision: 설치된 Pico2D를 직접 사용

Rationale: .venv의 1.5.1 소스를 읽어 open_canvas, close_canvas, get_events, draw_rectangle, clear/update_canvas를 확인했다. window/renderer 생성 실패가 확인되지 않으므로 엔진이 핸들을 검사하고 부분 초기화도 정리한다. 구현 모듈을 참조해야 나중에 생성된 핸들을 볼 수 있다.

Alternatives considered: 새 렌더러·래퍼·의존성 도입은 범위를 넘고 필요 없다. Pico2D 패키지 자체 수정도 하지 않는다.

## Decision: 단조 시계와 프레임 끝 장면 교체

Rationale: perf_counter와 sleep만으로 경과 시간과 CPU 사용을 제어할 수 있다. 전환을 미루면 콜백 중 활성 장면이 바뀌지 않는다. 예외는 finally 정리 후 전파한다.

Alternatives considered: 고정 물리 스텝·장면 스택·이벤트 버스는 현재 요구하지 않는다.

## 근거와 한계

읽기 전용 연구 에이전트와 주 작업자가 .venv/Lib/site-packages/pico2d/pico2d.py의 창·이벤트·도형 구현을 확인했다. get_events는 키 반복을 제거하고 1ms 대기하며 창 제목을 FPS로 갱신한다. debug_print는 비어 있어 안내 텍스트는 README와 콘솔에 둔다. 실제 창 검증은 구현 후 별도 수행한다.
