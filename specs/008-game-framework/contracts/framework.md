# 게임프레임워크 계약 제안

이 문서는 최종 결합 모델의 제안이다. [분리 계획](../plan.md)의 각 범위가 해당 데이터/API를 도입한다. P1부터 모든 형식이나 빈 연결점을 구현하지 않는다.

**상태**: P1 객체·레벨·규칙과 P2 출력 기반 검증 커밋 통합 / P3 구현 중 / P4·P5는 목표 계약. [architecture](../../../docs/architecture.md#게임프레임워크-계약-제안-미구현)가 세부 순서·비용의 기준이다. 기존 Scene 콜백과 기본 Engine 실행 호출은 유지하되 Engine의 크기/전체화면 설정·출력 조회·필요한 SDL 이벤트 처리는 P2 구현 계약을 따른다.

- P3 구현 API: `LevelScene(level, camera_center=(0,0), view_height=10)`은 Canvas 없는 월드 장면이다. `transform`, `event_to_world(event)`, 기존 Scene 콜백을 제공한다. P5에서 Canvas 결합을 확장하며 현재 빈 Canvas 인자는 요구하지 않는다.
- P3 구현 API: `WorldTransform(viewport, center=(0,0), view_height=10)`의 point/inverse/length/bounds, 불변 `RenderItem(drawable, draw_order=0, bounds=None, visible=True, opacity=1)`, `Renderer.draw(level, transform)`. drawable은 `(transform, opacity)`를 받는다. 원본 등록순에서 매번 수집·안정 정렬하고 1출력픽셀 여유를 둔 범위 판정 후 그린다. 목록은 성공·실패 모두 비운다.
- P3 구현 API: `draw_rect(transform, bounds, color, opacity=1)`, `draw_image(image, transform, bounds, opacity=1)`는 SDL 출력 좌표를 직접 사용하고 공유 상태를 복원한다. 이미지 texture 소유는 호출자다. LevelScene은 렌더 리셋 이벤트와 reset_generation 변화를 명시 오류로 처리하며 자동 자원 재업로드는 하지 않는다.
- P1 공개 API: Level(mode=None), 읽기 전용 mode/objects, get(id). GameMode는 생성 시 해당 Level에 연결되고 다른 Level에서 재사용하지 않는다. GameObject의 level/id는 읽기 전용이다. Level.on_open()에서 새 객체로 초기 배치를 구성한 뒤 mode.on_start()를 호출한다.
- Level.open()/close()는 초기 배치와 GameMode 수명을 관리한다. 닫는 상태와 정리 콜백 중 신규 등록을 거부한다. 부분 실패에도 전체 정리를 시도하고 오류를 보존한다.
- Level.spawn(obj)는 새 인스턴스에 재사용하지 않는 Level 내부 ID를 부여해 dict에 등록한다. 동일 인스턴스의 재등록을 거부한다. GameObject.destroy()는 등록/소속을 먼저 해제한 뒤 정리를 한 번 시도한다. 반복 제거는 무해하다.
- Level.handle_event(event)/update(dt)는 콜백 전 등록순 tuple을 취득하고 모드→객체 순으로 전달한다. 재진입 전달은 거부한다. 호출 직전 소속을 확인한다. 입력 이벤트 하나가 전달 경계다.
- GameMode는 level과 on_start/on_event/on_update/on_end를 가진다. GameObject는 on_spawn/on_destroy/handle_event/update/render_items 후보를 가진다. 초기화 실패는 소유 해제·정리 시도 후 오류를 전달한다. P1은 render_items를 아직 제공하지 않는다. 열기 실패 시 모드 on_end도 시도한다. 단일 오류는 그대로, 복수 오류는 BaseExceptionGroup으로 전달한다. 닫힌 상태의 입력/update는 무해하며 전달·정리 중 재열기는 거부한다.
- Canvas.add(element, parent=None)는 새 노드를 roots/children 끝에 붙인다. 같은 노드 재부착·다중 소유·순환을 거부한다. 제거된 노드는 다시 쓰지 않는다. reparent API는 없다.
- Canvas.remove(element)는 해당 하위 트리를 한 번에 소유 해제하고 자식부터 정리한다. 모든 대상의 소속을 정리 콜백 전에 해제한다. 반복 제거는 무해하며 일부 오류에도 나머지 정리를 시도한다. Canvas.close()는 전체 트리를 분리해 일괄 정리한다.
- UIElement는 UI 논리 로컬 위치, 루트 anchor, visible, 형제 범위 정수 draw_order, update(dt), 논리 원점·UI→출력 변환·opacity를 받는 자기 그리기를 가진다. draw는 자기 표현만 담당하고 자식 방문은 Renderer 책임이다. 숨김은 하위 트리 렌더를 생략하지만 update는 생략하지 않는다.
- LevelScene.update(dt)는 Level·Canvas 대상 스냅샷을 모두 콜백 전에 취득해 모드→월드 객체→UI 등록순 DFS로 호출한다. 내부 스냅샷 전달 API는 최소 구현으로 정한다.
- 같은 이벤트/update에서 신규 대상은 이후 전달부터 참여한다. update 중 생성은 해당 프레임 렌더에 보이며 제거 대상은 이후 호출/렌더에서 제외한다. 이미 실행 중인 메서드를 강제 중단하지 않는다.
- Renderer.draw(level, canvas, camera, viewport)는 월드 RenderItem을 등록순·객체 내부순으로 검사하고 화면 밖/숨김/알파 0을 제외해 draw_order 안정 정렬한다. 월드 drawable에는 위치/크기를 함께 변환하는 월드→출력 변환과 opacity를 전달해 원래 상태를 바꾸지 않고 그린다. camera는 중심·세로 시야의 최소 상태이며 구체 타입명은 미정이다. UI는 형제 복사본 정렬 후 부모→자식 DFS로 수집하며 전역 정렬하지 않는다. UI 부모의 위치는 자식 논리 좌표에 누적하고 UI→출력 변환을 따로 적용한다.
- 큰 draw_order가 앞이다. 월드 동률은 등록순·항목순, UI 형제 동률은 등록순이다. UI 하위 트리 전체는 연속해서 그린다. 월드 패스 뒤 UI 패스이며 UI 뎁스는 월드 뎁스와 비교하지 않는다.
- 렌더 수집부터 종료까지 생성/삭제/계층/뎁스 변경을 허용하지 않는다. 소유 API 변경은 오류로 거부하고 그리기 콜백은 상태 변경을 하지 않는다. 임시 목록·스냅샷은 종료·실패 시 해제한다.
- 엔진 종료 반영 단위는 기존 Scene 콜백 경계다. UI 입력/포커스·레이아웃·클리핑·물리·빈 simulate 단계는 추가하지 않는다.

- bounds는 실제 그림을 포함한 유한한 AABB 또는 None이다. 영역이 완전히 분리된 항목만 제외하며 부분 겹침·경계·미확인 범위는 보수적으로 남긴다. 중심점만으로 판정하지 않는다. 화면 밖이어도 Level/Canvas 소유·update는 유지한다.
- UI 자기 bounds는 누적 UI 논리 좌표로 현재 Canvas 논리 영역과 비교한다. 부모의 자기 그림 제외는 자식 방문을 중단하지 않는다. UI는 월드 카메라를 적용하지 않는다.
- opacity는 유한한 0~1이며 이미지 픽셀 알파에 곱한다. 표준 알파 합성으로 기존 뎁스 순서를 유지하고 불투명/반투명 분리 재정렬·가림 판정 제외를 하지 않는다. UI opacity 상속/그룹 합성은 없다.
- draw 백엔드는 매 호출에 opacity/blend 상태를 적용하고 실패 시에도 기존 상태를 복원한다. 공유 이미지 상태가 다음 객체로 누출되지 않게 한다. 도형 그리기 상태도 별도 복원한다.

- camera의 view_height와 Canvas.reference_size는 유한한 양수다. 월드는 세로 시야 고정/화면비별 가로 확장을 제안한다. Canvas는 min(viewport/reference_size) 균등 배율과 전체 viewport의 논리 영역을 사용한다. 축 방향과 수식은 architecture를 따른다.
- Engine은 창 클라이언트 크기와 실제 렌더 출력 픽셀을 별도 조회한다. 크기/전체화면/DPI 변경은 viewport·월드/UI 변환·bounds 판정을 함께 갱신한다. 0 크기/최소화 때 그리기·좌표 역변환을 생략한다.
- 원본 입력 이벤트는 보존한다. 마우스 위치는 창→출력→world/UI 역변환 함수로 해석하며 wheel delta는 위치로 취급하지 않는다. 필요 SDL 창/렌더 리셋 이벤트가 Pico2D 필터에서 사라지지 않도록 엔진 펌프를 보완한다.
- 보더리스 전체화면을 첫 정책으로 제안하며 전환 실패·복귀·영향받은 렌더 자원 복구를 검증한다. 게임 좌표나 UI 저장 위치를 출력 픽셀로 재작성하지 않는다.
