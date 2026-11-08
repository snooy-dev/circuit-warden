# 장면 연결 계약

규칙·기본값의 기준은 [architecture](../../../docs/architecture.md)다.

- Scene을 상속하고 필요한 enter(engine), handle_event(event), update(dt), draw(), exit()를 구현한다.
- Engine().run(scene)으로 실행한다. enter에서 받은 엔진의 change_scene(next_scene), stop()으로 전환·종료를 요청한다.
- run에는 Scene 인스턴스를 전달한다. 콜백은 동기식이며 한 스레드에서 실행한다. 다중 창·동시 실행은 지원하지 않는다.
- change_scene·stop은 활성 실행의 콜백에서 사용한다. 전환은 프레임 끝, 종료는 다음 처리 전에 반영한다.
- 이벤트는 Pico2D 원형 그대로, dt는 초 단위다. 종료 키는 엔진이 소비한다.
- 장면 자원은 enter/exit에서 관리하며 부분 진입 실패에 대한 exit도 안전하게 처리한다.
