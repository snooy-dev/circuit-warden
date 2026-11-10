# 데이터 모델 제안

이 문서는 최종 결합 모델의 제안이다. [분리 계획](plan.md)의 각 범위가 해당 데이터/API를 도입한다. P1부터 모든 형식이나 빈 연결점을 구현하지 않는다.

**상태**: P1 객체·레벨·규칙과 P2 출력 상태 검증 커밋 통합 / 나머지는 후속 구현의 목표 모델. 동작·비용의 기준은 [기술 구조](../../docs/architecture.md#게임프레임워크-계약-제안-미구현)다. 아래 내부 필드명과 UIElement 이름은 제안이다.

| 형식 | 저장 데이터 | 소유/참조 |
|---|---|---|
| Level | _objects: dict[int, GameObject], _next_id: int, mode: GameMode, 열기/닫기·전달 상태 | GameObject·규칙 소유. ID는 Level 인스턴스 안에서 재사용하지 않음 |
| GameObject | 등록 ID, level 참조, NEW/등록/제거 수명, 위치·게임 상태 | 같은 인스턴스는 한 번만 등록. render_items()로 독립 월드 이미지 제공 |
| Canvas | _roots: list[UIElement], reference_size, logical_size, scale, 열기/닫기·전달 상태 | 화면 크기와 독립인 UI 논리 좌표·트리 소유 |
| UIElement | parent, _children: list[UIElement], canvas, 수명, 로컬 x/y, 루트 anchor, visible, 정수 draw_order, 로컬 bounds 또는 None, opacity | 한 번만 부착. 형제 draw_order, 등록순 children. 그리기는 논리 원점·UI→출력 변환·opacity를 받아 자신의 UI만 표현 |
| RenderItem | drawable 참조, 정수 draw_order, 월드 bounds 또는 None, visible, opacity | 월드 이미지의 정렬 단위. 이미지 픽셀·게임 상태 복제 없음 |
| Renderer | world_items: list[RenderItem], ui_items: list[tuple[UIElement, x, y, opacity]] | 렌더 호출 동안의 임시 참조. 종료·실패 시 비움 |
| LevelScene(engine.Scene) | Level, Canvas, Renderer, camera_center, view_height | 월드 카메라 상태와 장면 콜백 연결 |
| Engine 출력 상태 | window_size, output_size, viewport, 창/전체화면 모드 | 입력 단위·실제 출력 픽셀 분리. Scene 콜백 API 유지 |

Level의 tuple 스냅샷은 등록순이고 Canvas의 tuple 스냅샷은 원본 형제 등록순의 전위 DFS다. LevelScene.update 시작에 둘 다 얻은 뒤 모드→월드 객체→UI를 갱신한다. 같은 전달에서 생성된 대상은 다음 전달부터 참여한다. 제거 대상은 호출 직전 소속 확인으로 제외한다.

월드 렌더 목록은 매 프레임 원본을 검사해 화면 밖/숨김/알파 0을 제외한 뒤 draw_order 안정 정렬한다. 월드는 x 오른쪽/y 위의 게임 단위이며 camera_center·view_height와 실제 viewport로 출력 좌표에 투영한다. Canvas는 좌상단 원점/y 아래인 UI 논리 단위를 쓰고 reference_size로 균등 배율과 현재 논리 크기를 계산한다. 루트 anchor와 자식 로컬 위치를 더하며 위치/크기/폰트에 같은 배율을 적용한다. UI 목록은 형제 복사본을 안정 정렬한 전위 DFS 결과이며 전역 재정렬하지 않는다. 부모 위치를 합산한 UI 논리 좌표를 같이 보관한다. 출력 변환과 입력 역변환은 같은 프레임 출력 상태를 사용한다. 큰 draw_order가 앞이며 UI는 월드와 별도 패스다. 형제 하위 트리는 서로 섞이지 않는다.

등록 ID와 GameObject 생성 이력, UIElement 부착 이력은 다른 개념이다. 증가 ID만으로 동일 인스턴스의 재등록을 막았다고 간주하지 않는다. 제거 때 논리적 소유를 먼저 해제하고 정리를 한 번 시도한다. 모든 스냅샷·UI 부모/자식 연결은 수명 종료에 해제한다. 실제 Python 메모리 해제 시점은 외부 참조에도 달려 있다.

bounds는 실제 그림을 포함하는 AABB이며 None은 검사 불가로서 제외하지 않는다. opacity는 유한한 0~1, 기본 1이고 이미지 픽셀 알파에 곱한다. UI opacity는 자기 그림에만 적용한다. 부모 그림이 화면 밖/알파 0이어도 자식 순회는 유지하고 visible=false만 하위 트리를 숨긴다. 화면 밖/투명 상태가 소유·update를 바꾸지 않는다.

배치는 현재 실행 중 상태와 초기화 코드로 보관한다. 별도 파일 직렬화·ID 영속성·전역 UI·UI ID 검색·reparent·자동 레이아웃·클리핑은 현재 제안에 없다.
