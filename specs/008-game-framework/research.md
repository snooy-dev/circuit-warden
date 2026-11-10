# 기술 선택 제안

## 명칭 검토와 공식 엔진 참고

확인일: 2026-11-10. 사용자는 이름부터 정리하고 상용 2D 엔진을 참고하도록 요청했다. Unity·GameMaker를 중심으로 보고 Godot는 비교 자료로, Unreal은 GameMode 용어의 근거로만 참고했다. 이 조사는 엔진 변경·구현 재개·상세 설계 승인이 아니다.

### 공식 문서에서 확인한 용례

| 엔진 | 공간·실행 객체 | UI와 그리기 순서 | 근거 |
|---|---|---|---|
| Unity | Scene에 환경·캐릭터·UI 등의 콘텐츠를 구성. GameObject는 컴포넌트를 담는 실행 객체 | uGUI는 Canvas 아래 UI 배치. 2D Renderer는 Sorting Layer와 Order in Layer 사용 | [Scene](https://docs.unity.com/en-us/engine/6000.0/manual/working-with-scenes/creating-scenes), [GameObject](https://docs.unity.com/en-us/engine/6000.0/manual/working-with-gameobjects/game-objects), [uGUI Canvas](https://docs.unity3d.com/Packages/com.unity.ugui@2.0/manual/UICanvas.html), [2D sorting](https://docs.unity.com/en-us/engine/6000.0/manual/unity2d/sprite/sort-sprites/2d-renderer-sorting) |
| GameMaker | Room에 객체의 Instance를 배치. Object는 Instance의 정의/템플릿 | Room Layer의 depth로 순서 지정. 별도의 UI Layers와 GUI 그리기 경로 | [Room](https://manual.gamemaker.io/monthly/en/Quick_Start_Guide/Rooms.htm), [Object/Instance](https://manual.gamemaker.io/monthly/en/Quick_Start_Guide/Objects_And_Instances.htm), [UI Layers](https://manual.gamemaker.io/monthly/en/The_Asset_Editors/Room_Properties/UI_Layers.htm) |
| Godot (비교) | Scene은 Node 트리. 2D 게임 노드는 Node2D 계열, UI는 Control 계열 | CanvasLayer는 독립 렌더 계층이며 CanvasItem.z_index와 별개로 앞뒤 순서 결정 | [Scene](https://docs.godotengine.org/en/stable/getting_started/step_by_step/nodes_and_scenes.html), [CanvasItem](https://docs.godotengine.org/en/stable/classes/class_canvasitem.html), [CanvasLayer](https://docs.godotengine.org/en/stable/classes/class_canvaslayer.html) |

GameMode는 모든 2D 엔진의 공통 표준 명칭이라는 뜻이 아니다. Unreal은 게임 규칙을 GameMode로 표현하고 레벨 플레이 초기화 시 생성한다. 이 역할을 참고하면 사용자가 의도한 레벨별 규칙 객체에 GameMode라는 이름이 맞는다. 서버 전용·복제·GameState 체계까지 가져오지는 않는다. [Unreal GameMode](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-mode-and-game-state-in-unreal-engine)

### 프로젝트에 대한 해석과 제안

다음은 위 출처를 참고한 Codex의 설계 제안이며 엔진 공통 규격이 아니다.

| 역할 | 권장 이름 | 현재 상태 |
|---|---|---|
| 엔진이 진입·입력·업데이트·그리기·퇴장을 호출하는 실행 단위 | Scene | 기존 engine.Scene 유지 권장. 렌더 목록만 의미하는 이름으로 쓰지 않음 |
| 레벨과 UI 등을 묶는 게임 화면 구현 | GameScene | 기존 계획의 LevelScene에 대한 이름 후보. 아직 변경하지 않음 |
| 게임오브젝트·배치·레벨별 규칙 소유 | Level | 기존 사용자 의도를 유지하는 후보. 첫 범위에서 별도 World는 두지 않음 |
| 월드의 실행 객체 | GameObject | 유지 후보. Unity의 컴포넌트 체계까지 채택한다는 뜻은 아님 |
| 레벨별 게임 규칙 | GameMode | 유지 후보. 렌더링/객체 목록 소유와 구분 |
| UI 요소와 배치를 담는 소유 루트 | Canvas | 사용자 제안에 따른 권장 후보. Level을 이름만 바꾸는 것이 아니라 UI 역할을 분리 |
| 참조 수집·정렬·그리기 담당 | Renderer | 사용자가 2D 전용 프로젝트이므로 Renderer면 충분하다고 명시. 이 명칭을 반영 |
| 월드 이미지·도형 등 독립 그리기 단위 | RenderItem | 기존 후보 유지. UI는 UIElement의 계층 순서로 표현 |

Renderer는 사용자 지정 이름이다. 이후 구체 자료 구조 제안 요청에 따라 Canvas·UIElement를 상세안에 포함했고 LevelScene의 UI 직접 목록은 Canvas 소유로 대체 제안했다. 이는 최종 승인이 아니다. LevelScene→GameScene 이름 변경은 하지 않으며 구현 보류를 유지한다.

### 뎁스 명칭과 적용 범위

Unity의 Order in Layer는 큰 값이 앞에 오고, GameMaker의 depth는 작은 값이 앞에 온다. 따라서 depth 숫자의 방향은 엔진 공통 규칙이 아니다. 우리 안은 draw_order라는 이름과 작은 값부터 그린다는 계약을 유지하는 것을 권장한다. 월드/UI 목록 분리와 동률 안정성도 우리 프로젝트의 명시적 계약으로 둔다. [Unity order](https://docs.unity.com/en-us/engine/6000.0/manual/unity2d/sprite/sort-sprites/2d-renderer-sorting), [GameMaker depth](https://manual.gamemaker.io/monthly/en/Quick_Start_Guide/Rooms.htm)

Canvas라는 이름만으로 UI 수명이 정해지지는 않는다. 예를 들어 GameMaker 월간 문서는 UI Layer의 요소가 룸 변경 뒤에도 유지된다고 설명한다. 이 정책을 우리 프로젝트의 화면별 UI에 자동 적용하지 않는다. 공통 UI 유지 여부는 미정이다. [GameMaker UI lifetime](https://manual.gamemaker.io/monthly/en/The_Asset_Editors/Room_Properties/UI_Layers_At_Runtime.htm)

Unity의 Canvas 설명은 uGUI 체계에 관한 것이며 모든 Unity UI 시스템을 대표한다고 일반화하지 않는다. Pico2D의 open_canvas는 창/그리기 표면 API이므로 프로젝트의 UI 소유 Canvas와 역할이 다르다. 외부 엔진 설치·실행은 하지 않았다. Python 자료 구조만 아래 독립 실험으로 비교했다.

## 렌더 항목 이름 비교

사용자가 RenderItem의 대안과 Primitive 용례 조사를 요청했다. 이름은 아래 대상의 의미를 정한 뒤 선택한다. 아직 이름 변경을 승인받은 것은 아니다.

| 후보 | 적합한 의미 | 현재 계약과의 관계 |
|---|---|---|
| RenderItem | 렌더 목록에서 정렬·처리할 한 항목 | drawable 참조와 draw_order를 가진 현재 계약에 가장 직접적 |
| Drawable / Renderable | 그릴 수 있는 객체 또는 인터페이스 | 항목 자체가 draw()를 제공한다면 적합. 별도 참조 래퍼와 구분 |
| RenderCommand / DrawCommand | 제출한 그리기 작업과 실행 정보 | 한 프레임의 그리기 요청을 명령으로 표현할 때 적합 |
| Primitive | 기하/렌더 기본 요소 | 단순 삼각형에만 한정되는 용어는 아니나, 일반 정렬 항목과는 의미 차이가 있음 |

Cocos2d-x v4는 Renderer가 RenderCommand를 소비하고 명령에 정렬 순서를 둔다. Godot는 CanvasItem 안에 primitive·texture rectangle·polygon 등의 서로 다른 그리기 명령을 추가한다. Unreal의 UPrimitiveComponent는 렌더링/충돌용 기하를 담거나 생성하며 FPrimitiveSceneProxy는 이를 렌더 스레드 쪽에 표현한다. 따라서 Primitive를 틀린 이름이라 할 수는 없지만, 현재 객체 참조·정렬 정보만 가진 항목에는 RenderItem이 더 정확하다는 것이 Codex의 제안이다. [Cocos RenderCommand](https://docs.cocos2d-x.org/api-ref/cplusplus/v4x/d6/d9a/classcocos2d_1_1_render_command.html), [Godot drawing commands](https://docs.godotengine.org/en/stable/classes/class_renderingserver.html), [Unreal PrimitiveComponent](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UPrimitiveComponent?lang=en-US), [Unreal PrimitiveSceneProxy](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/FPrimitiveSceneProxy)

## 엔진 내부 자료 구조 조사

확인일: 2026-11-10. 상용 엔진의 공개 구현과 상용 게임 개발에 사용하는 공개 엔진의 구현을 구분해 조사했다. 이름·에디터 계층만 보고 내부 컨테이너를 추정하지 않는다. Cocos2d-x는 v4 태그, Unity uGUI는 조회 시점 main, Unreal은 5.5 공식 API, Defold는 개발 커밋 9066bb952b42ddfd2cd6a68c48352b0937dab4e3을 기준으로 한다. 모든 엔진의 최신 안정판을 동일 조건으로 비교한 결과는 아니다.

| 대상 | 확인한 자료 구조 | 순서·변경 처리와 해석 범위 |
|---|---|---|
| Unity uGUI 등록부 | GraphicRegistry의 Dictionary<Canvas, IndexedSet<Graphic>>. IndexedSet은 List<T>와 Dictionary<T, int> 결합 | 빠른 검색·중복 방지·삭제를 지원하지만 삭제/활성 변경 시 원소를 교환하여 등록 순서를 보장하지 않음. 최종 화면 그리기 순서 자료라는 뜻이 아님 |
| Unity uGUI 갱신 | 레이아웃·그래픽 재구축 대상을 별도 IndexedSet에 등록 | 변경 대상 큐와 소유 계층을 구분. 레이아웃 큐는 부모 깊이로 정렬하고 갱신 |
| Cocos2d-x Node | 부모 참조 + Vector<Node*> 자식 목록. Vector 내부는 std::vector | 배열로 자식 관계를 저장하는 트리. 순서 변경 표시가 있을 때 자식 목록을 정렬하고 순회 |
| Cocos2d-x Renderer | 패스 그룹별 std::vector<RenderCommand*> | global Z 음수/양수 그룹 등을 안정 정렬. 이미 순서대로 제출된 기본 2D 그룹은 중복 정렬하지 않음 |
| Defold Collection | dmArray<Instance*> 슬롯 배열 + 빈 인덱스 풀 + ID→Instance 해시 테이블 | 슬롯을 재사용하므로 생성 등록순 배열이 아님. 삭제 요청과 PostUpdate의 실제 파괴를 분리 |
| Defold GUI | dmArray<InternalNode> + 인덱스 풀. 노드에 부모·이전/다음 형제·첫/마지막 자식 인덱스 | 물리 저장은 배열, 논리 관계는 순서 있는 트리. 계층 순회로 별도 RenderEntry 배열을 만들고 레이어·순서 키로 정렬 |
| Defold Renderer | 렌더 항목 배열, 지속/임시 저장소, 정렬 값·인덱스 버퍼와 등록/태그 캐시 | 캐시가 있어도 최종 depth/batch 정렬은 별도. 모든 엔진이 매 프레임 전체를 새로 수집한다는 일반화는 틀림 |
| Unreal ULevel (2D 전용 아님) | Actors가 TArray<TObjectPtr<AActor>> | 레벨의 Actor 참조 배열을 확인. 이것이 엔진의 모든 객체 조회·업데이트·렌더 구조를 대표하지 않음 |

### 공식 근거

- Unity: [GraphicRegistry](https://github.com/Unity-Technologies/uGUI/blob/main/com.unity.ugui/Runtime/UGUI/UI/Core/GraphicRegistry.cs), [IndexedSet](https://github.com/Unity-Technologies/uGUI/blob/main/com.unity.ugui/Runtime/UGUI/UI/Core/SpecializedCollections/IndexedSet.cs), [CanvasUpdateRegistry](https://github.com/Unity-Technologies/uGUI/blob/main/com.unity.ugui/Runtime/UGUI/UI/Core/CanvasUpdateRegistry.cs). 공개 C# uGUI 부분만 확인했으며 Unity 네이티브 Scene·렌더러의 전체 저장 구조는 확인하지 못했다.
- Cocos2d-x: [Node 선언](https://github.com/cocos2d/cocos2d-x/blob/v4/cocos/2d/CCNode.h), [Vector 구현](https://github.com/cocos2d/cocos2d-x/blob/v4/cocos/base/CCVector.h), [sortAllChildren·visit](https://github.com/cocos2d/cocos2d-x/blob/v4/cocos/2d/CCNode.cpp), [RenderQueue::sort](https://github.com/cocos2d/cocos2d-x/blob/v4/cocos/renderer/CCRenderer.cpp). 기본 2D 그룹의 정렬 생략은 제출 순서가 이미 맞다는 전제에 의존한다.
- Defold: [Collection](https://github.com/defold/defold/blob/9066bb952b42ddfd2cd6a68c48352b0937dab4e3/engine/gameobject/src/gameobject/gameobject_private.h#L261-L291), [NewInstance·Delete·PostUpdate](https://github.com/defold/defold/blob/9066bb952b42ddfd2cd6a68c48352b0937dab4e3/engine/gameobject/src/gameobject/gameobject.cpp), [GUI InternalNode·Scene](https://github.com/defold/defold/blob/9066bb952b42ddfd2cd6a68c48352b0937dab4e3/engine/gui/src/gui_private.h), [CollectRenderEntries·RenderScene](https://github.com/defold/defold/blob/9066bb952b42ddfd2cd6a68c48352b0937dab4e3/engine/gui/src/gui.cpp#L1814-L1876), [RenderContext](https://github.com/defold/defold/blob/9066bb952b42ddfd2cd6a68c48352b0937dab4e3/engine/render/src/render/render_private.h), [DrawRenderList](https://github.com/defold/defold/blob/9066bb952b42ddfd2cd6a68c48352b0937dab4e3/engine/render/src/render/render.cpp). Collection의 m_LevelIndices는 게임 레벨 목록이 아니라 계층 깊이별 인덱스다. 슬롯 반환이 빠르다는 사실만으로 자식 처리 등을 포함한 객체 파괴 전체를 O(1)이라고 할 수 없다.
- Unreal: [ULevel 5.5](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/Engine/ULevel?application_version=5.5). GameMaker는 공개 Room/Layer API만으로 내부 배열·해시·연결 목록 중 무엇을 쓰는지 확인할 수 없어 구조를 단정하지 않는다.

### 우리 설계에 적용할 판단

아래는 소스 관찰에서 도출한 제안이며 사용자 확정 사항이 아니다.

1. 소유 저장, ID 조회, 부모·자식 관계, 업데이트 대상, 렌더 순서는 서로 다른 문제다. 한 컨테이너로 모두 해결할 필요가 없다. 다만 현재 필요한 자료만 만든다.
2. Level의 dict 제안은 상용 엔진의 표준을 모방한 것이 아니다. Python에서 동적 변경과 삽입 순서를 간단하게 유지하는 선택이다. 연속 순회와 메모리가 우선이면 list+안정 압축을 비교해야 한다. C++ 포인터 배열과 Python 객체의 실제 메모리 배치·호출 비용도 다르다.
3. Canvas의 트리는 관계 표현이고 배열은 저장 방식이므로 함께 사용할 수 있다. 지금부터 풀·정수 핸들·형제 연결 인덱스를 복제할 근거는 없다. UI 계층이 필요하다면 parent+순서 있는 children 목록부터 검토한다.
4. 삭제 시 마지막 원소로 빈자리를 채우는 방식은 빠르지만 등록순 계약을 깨뜨린다. 이를 채택하려면 업데이트 순서와 렌더 동률 순서를 별도로 보장하거나 계약을 바꿔야 한다. 현재 검토안에서는 그대로 도입하지 않는다.
5. Renderer의 평탄한 목록은 실제 엔진에서도 확인된다. 하지만 매 프레임 정렬, 변경 시 정렬, 순서대로 제출해 정렬 생략 중 선택은 변경률과 정렬 규칙에 달려 있다. 현재 안정 정렬은 최소 기준안이며 최적 성능을 입증한 결론이 아니다.

외부 엔진 설치·빌드·실행·성능 측정은 하지 않았다. 공개 구현 조사는 자료 구조를 확인하는 근거이며 Circuit Warden의 성능 측정을 대체하지 않는다.

## 자료 구조와 성능 검토

현재는 게임프레임워크 구현 보류 중이다. 아래는 독립 실험과 검토안이며 실제 게임 성능 보증이 아니다. 최대 객체/렌더 항목 수·생성/제거율·뎁스 변경률은 아직 정하지 않았다. UI 최소 계층은 아래 구체안의 미승인 제안이다.

### 연산별 후보

| 책임 | 후보와 비용 | 선택 기준 |
|---|---|---|
| Level 소유 | 삽입 순서를 유지하는 dict[내부 정수 ID, GameObject]. 추가/조회/제거 평균 O(1), 단계 스냅샷·순회 O(N) | 즉시 소유 해제·안전한 동적 변경·단순한 구현을 기준으로 우선 제안. list보다 컨테이너 메모리 큼 |
| Level 대안 | list와 활성 표시, 단계 경계의 안정 압축. 논리 제거 O(1), 압축 O(N) | 순회·메모리에 유리할 수 있지만 소유/정리 시점과 저장 공간 회수 시점을 분리 관리해야 함 |
| 피할 Level 구현 | 임의 항목을 list.remove로 매번 검색해 K개 제거: O(NK) | 대량 생성/소멸에 불리. 단순 list 자체가 항상 나쁘다는 뜻은 아님 |
| Canvas 소유 | roots/children의 list와 parent/canvas 참조로 순서 있는 트리 권장 | 순회 O(U), 하위 트리 제거 O(제거 수+형제 수). UI 묶음 순서를 표현하려는 선택이며 트리 자체가 정렬을 빠르게 하지는 않음 |
| Renderer | world 평탄한 list 안정 정렬, UI 형제 복사본 안정 정렬→전위 DFS 목록 | 월드 O(N+R log R), UI O(U+Σ k_i log k_i). UI 최종 목록은 전역 재정렬하지 않음 |
| 힙 | 구축 O(R) 후 전 항목 pop O(R log R) | 전체 항목을 그리는 경우 정렬보다 점근적 이득 없음. 동률 보조 키도 필요 |
| 변경 시 정렬 캐시 | 순서가 안 바뀌면 재정렬 생략 가능 | 추가/제거/내부 순서/뎁스/가시성/패스 변경을 누락 없이 추적해야 함. 실제 병목 확인 전 도입하지 않음 |

복잡도는 일반적인 CPython 연산 분석이며 dict의 O(1)은 최악 시간 보장이 아니다. Python list는 연속 객체 본체 배열이 아니라 연속 참조 배열이다. dict는 해시 테이블이며 삽입 순서가 보장되므로 별도 OrderedDict는 필요하지 않다. [CPython list/dict 구조](https://docs.python.org/3.14/faq/design.html#how-are-lists-implemented-in-cpython), [dict 계약](https://docs.python.org/3.14/library/stdtypes.html#mapping-types-dict)

리스트에 이진 탐색으로 삽입 위치를 찾더라도 실제 삽입은 O(N)이다. 힙도 모든 항목을 꺼내면 전체 정렬 비용을 없애지 못한다. [bisect](https://docs.python.org/3.14/library/bisect.html#performance-notes), [heapq](https://docs.python.org/3.14/library/heapq.html)

Canvas의 트리와 렌더러의 평탄한 목록은 함께 사용할 수 있다. 트리에서 부모 위치·가시성 등을 계산한 후 참조를 평탄화하는 방식이다. 현재 구체 권장안은 로컬 위치·숨김·수명·형제 순서를 위한 최소 Canvas 트리를 제안한다. 클리핑·레이아웃까지 포함하지 않으며 최종 승인 전이다. Cocos의 노드 트리나 Godot의 CanvasItem 트리도 구조적 관계를 표현하며, 노드를 많이 만드는 것 자체가 무료인 것은 아니다. [Cocos hierarchy](https://docs.cocos.com/creator/3.8/manual/en/concepts/scene/node-tree.html), [Godot CanvasItem](https://docs.godotengine.org/en/stable/classes/class_canvasitem.html)

### 독립 측정

게임 환경 Python 3.14.7, Windows 11. 크기 100/1,000/10,000, 삭제 비율 1%/10%, 전체 단계 비교는 1,000/10,000과 교체율 0%/1%/10%. 시나리오마다 준비 3회 후 31회 중앙값. 준비·결과 검사는 시간에서 제외하고 측정 구간의 GC는 일시 중지했다. 동일 원본·삭제 대상·잔존 순서를 assert로 확인했다. 소유 콜백·렌더링·레이아웃·실제 게임 규칙은 없으며, 단계 실험은 활성 표시 확인과 단순 카운터 갱신만 포함한다.

전체 단계: 참조 스냅샷 → 첫 규칙 역할의 제거/신규 생성 → 살아 있는 기존 항목만 갱신 → 필요한 안정 압축. 새 항목과 제거 항목이 같은 단계에서 갱신되지 않는 것도 검사했다. 모든 후보에 스냅샷을 사용했으므로 길이 경계만 쓰는 최적화된 list 구현과 비교한 결과는 아니다.

| 10,000개 항목 전체 단계 | 교체 없음 | 1,000개 제거+1,000개 생성 |
|---|---:|---:|
| list 반복 검색·제거 | 0.311 ms | 18.079 ms |
| list 활성 표시·안정 압축 | 0.310 ms | 0.581 ms |
| dict ID 기반 제거 | 0.361 ms | 0.609 ms |

별도 무작위 순서 렌더 항목 10,000개 수집·안정 정렬은 0.721ms, 수집·힙 구성·전체 추출은 2.318ms였다. 이는 이미지 그리기 비용을 포함하지 않는다.

10,000개 컨테이너 자체의 얕은 크기는 list 85,176바이트, dict 294,992바이트였다. 키·객체·일시 스냅샷·할당기 메모리를 제외하므로 전체 사용량 비교가 아니다.

[실험 원본](C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c37d-0ed1-7d02-9951-6a21f240d309/framework-container-comparison.py), [측정 결과](C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c37d-0ed1-7d02-9951-6a21f240d309/framework-container-comparison.json).

실험 결과 dict가 항상 빠른 것은 아니다. 동적 변경 계약을 단순하게 지키는 선택으로 dict를 우선 제안하며, 메모리/순회 중심이면 list+안정 압축도 유효하다. 어떤 방식도 실제 장면의 목표 성능을 아직 입증하지 못했다. 로컬 Pico2D의 이미지 draw가 SDL_RenderCopy로 전달되는 것만 코드에서 확인했으며 GPU·SDL 호출·알파 겹침 비용은 측정하지 않았다.

### 정합성 조건

- 단계 대상 스냅샷은 GameMode 콜백 전에 만든다. 모드가 생성한 객체가 같은 단계에 참여하면 현재 계약을 어긴다.
- 이전 프레임 정렬 목록을 다시 안정 정렬하는 것만으로 등록순 동률을 보장할 수 없다. A가 먼저 등록되고 A.order=2/B.order=1에서 [B,A]였다가 A.order=1이 되면 재정렬은 [B,A]를 유지한다. 원본 순서에서 다시 수집하거나 원래 수집순 보조 키를 써야 한다.
- 정렬 캐시와 공간 검색 인덱스는 별개다. 현재 보기 영역은 선형 검사하며 쿼드트리 등을 뎁스 정렬의 대체재로 추가하지 않는다.
- 불투명/투명 이미지를 텍스처별로 임의 재정렬하면 앞뒤 표시가 달라질 수 있다. 배칭을 이유로 명시적 그리기 순서를 깨뜨리지 않는다.

안정 정렬의 동률 의미는 [Python sorting](https://docs.python.org/3.14/howto/sorting.html#sort-stability-and-complex-sorts)을 따른다. 위 수명·캐시 함정은 gpt-6.1-sol/high 읽기 전용 검토에서도 확인했다. Canvas의 레이아웃/클리핑 성능이나 실제 게임 프레임은 이번 실험에서 검증하지 않았다.

## 현재 구조 검토안

아래는 사용자 의도를 구현할 후보이며 최종 승인 전이다.

- Decision: 객체 소유를 Level에 모으고 Renderer는 참조, GameMode는 규칙을 담당한다.
  Rationale: 객체 수명·시각 표현·게임 규칙의 책임을 분리하고 제거 후 잔존을 막는다.
  Alternatives considered: 모드 소유는 이번 사용자 의도와 맞지 않는다. 씬의 복제 객체 목록은 동기화 부담을 만든다.
- Decision: 기존 engine.Scene과 렌더링 씬을 구분하고 LevelScene으로 연결한다.
  Rationale: 기존 엔진은 입력·수명까지 담당하므로 렌더링 전용으로 취급하면 계약이 충돌한다.
  Alternatives considered: 엔진의 Scene 이름 변경은 기존 호출부를 바꾸므로 현재 최소안에서 제외한다.
- Decision: LevelScene.update는 Level·Canvas 스냅샷을 모두 얻은 뒤 모드·객체·UI에 시간 진행을 전달하고 draw는 Renderer에 맡긴다.
  Rationale: 현재 시뮬레이션이 없다는 사용자 지시에 맞게 입력·업데이트·렌더링만 둔다.
  Alternatives considered: 빈 simulate 연결점·별도 시뮬레이션 순회·고정 시간 물리 반복은 필요해질 때 검토한다.
- Decision: 첫 범위에서 World/Level을 하나로, 배치를 메모리와 초기화 코드로 표현한다.
  Rationale: 파일 보관·여러 레벨의 동시 소유까지 요청되었다고 추측하지 않는다.
  Alternatives considered: LevelData/영속 World/에디터는 해당 요구가 확정되면 검토한다.

공식 문서 조사는 위 명칭 검토에 반영했다. 새 의존성은 추가하지 않았다. 모드 소유 초안 검토와 현재 구조의 읽기 전용 수명/순서 검토를 구분한다. 어느 쪽도 런타임 테스트 성공을 의미하지 않는다.

- Decision: Level은 삽입 순서 dict, Canvas는 roots/children 목록 트리, Renderer는 월드 전역 정렬과 UI 형제 정렬 후 DFS 목록을 권장한다. [구체 계약](../../docs/architecture.md#자료-구조와-그리기-순서-제안)을 따른다.
  Rationale: Level의 ID 조회·삭제·등록순을 단순하게 유지한다. UI는 부모와 하위 트리의 수명·표시·순서를 표현한다. 월드 이미지 교차 정렬과 UI 패널 묶음 순서는 다른 규칙이다.
  Alternatives considered: dict가 최속이라는 근거는 없다. list+안정 압축은 순회/메모리 대안이다. UI 평탄한 전역 뎁스는 패널 자식이 다른 패널을 넘어가는 문제를 만들 수 있다. 풀·정렬 캐시는 미도입이다.

구체안은 공식 Python dict의 삽입 순서와 sort의 안정성을 확인해 구성했다. 같은 인스턴스의 재등록 금지, 모드 콜백 전 전체 UI 스냅샷, UI 로컬 정렬의 제약은 읽기 전용 설계 검토로 대조했다. 실제 UI 트리 구현·측정은 하지 않았다.

## 화면 영역과 반투명 합성

사용자가 화면보다 큰 월드의 화면 밖 객체와 반투명 객체를 추가로 제시했다. 독립 좌표계·가변 해상도 지시에 맞춰 카메라 중심/월드 세로 시야·출력 viewport 투영을 제안한다. 자동 추적/조작용 줌/다중 뷰포트는 제외한다. Level 소유·update와 렌더 제외는 분리한다. 현재 월드의 모든 항목을 선형 검사하므로 제외 후 정렬/그리기는 줄지만 전체 업데이트/범위 검사 비용은 남는다.

Unity 공식 Renderer.bounds는 월드 그림을 포함하는 AABB를 설명한다. 우리 안은 RenderItem마다 실제 그리기 범위를 사용하며 중심점이나 충돌 범위로 대신하지 않는다. 미확인 bounds는 제외하지 않고, UI 부모 자기 범위가 화면 밖이어도 자식은 검사한다. [Unity bounds](https://docs.unity.com/en-us/engine/6000.0/script-reference/unityengine/renderer/bounds)

SDL2의 표준 BLEND는 앞 RGB와 알파를 뒤 색에 합성하며, TextureAlphaMod는 이미지 픽셀 알파에 추가 비율을 곱한다. 따라서 opacity=1이 이미지 전체 불투명을 보장하지 않으며 불투명/반투명 재분류로 명시된 2D 순서를 바꾸지 않는다. 가림 판정 제외와 텍스처별 재정렬은 미도입이다. [SDL blend](https://wiki.libsdl.org/SDL2/SDL_BlendMode), [alpha modulation](https://wiki.libsdl.org/SDL2/SDL_SetTextureAlphaMod), [texture blend state](https://wiki.libsdl.org/SDL2/SDL_SetTextureBlendMode)

로컬 Pico2D 1.5.1 소스의 Image.draw는 SDL_RenderCopy, Image.opacify는 SDL_SetTextureAlphaMod를 호출한다. opacify는 texture 상태를 바꾸며 반환 코드를 전달하지 않는다. draw_rectangle 등은 renderer draw color를 바꾸므로 texture와 별도 상태 관리가 필요하다. 의존성을 수정하지 않고 구현 시 최소 그리기 코드에서 상태 설정·오류 확인·복원을 책임져야 한다. [로컬 소스](D:/GitHub/circuit-warden/.venv/Lib/site-packages/pico2d/pico2d.py)

합성·화면 경계·실제 SDL 백엔드는 이번에 실행하지 않았다. 표준 alpha만 제안하며 덧셈 혼합·그룹 표면 합성·premultiplied-alpha 경로·색 공간 보정은 새 기능으로 도입하지 않는다. UI opacity는 자기 그림에만 적용한다. 이전 합성 컨테이너 벤치마크는 이 변경의 실행 성능 근거가 아니다.

## 좌표계와 가변 창·전체화면

월드 게임 단위와 Canvas 논리 단위를 각각 출력 픽셀로 변환한다. 월드 세로 시야 고정/가로 화면비 확장, UI 기준 크기 대비 균등 배율/전체 영역 anchor는 프로젝트 기술 제안이며 엔진 공통 규격이나 사용자 확정 게임 정책이 아니다. 실제 출력 해상도와 UI 제작 기준 크기를 혼동하지 않는다. 기준 숫자·허용 화면비/최소 창 크기는 미정이다.

SDL_GetRendererOutputSize는 실제 출력 픽셀 크기를 반환하며 고DPI에서 SDL_GetWindowSize와 다를 수 있다. 창 마우스 좌표를 출력 픽셀로 바꾸고 그리기 변환을 역으로 적용해야 한다. SDL_FULLSCREEN_DESKTOP은 데스크톱 크기 전체화면이며 일부 렌더러는 전환 시 자원 리셋을 알릴 수 있다. [출력 크기](https://wiki.libsdl.org/SDL2/SDL_GetRendererOutputSize), [창 크기](https://wiki.libsdl.org/SDL2/SDL_GetWindowSize), [전체화면](https://wiki.libsdl.org/SDL2/SDL_SetWindowFullscreen)

P2 이전 engine.py는 WIDTH/HEIGHT=800/600을 open_canvas에 전달했다. Pico2D open_canvas(full=True)는 독점 전체화면 플래그를 사용하고, resize_canvas는 SDL_SetWindowSize까지 호출한다. get_events는 창/렌더 리셋 이벤트를 호출자에게 전달하지 않으며 그리기 y 변환은 canvas_height를 사용한다. 따라서 화면 크기만 바꾸면 기존 코드가 완전 대응한다고 주장할 수 없다. Engine의 출력 조회·이벤트·화면 모드 처리와 프로젝트 그리기 경계의 출력 높이/좌표 변환을 연결해야 한다. 의존성 소스는 수정하지 않았다.

문서 수식의 읽기 전용 검토에서 출력 y 방향을 Pico2D 경계에서 한 번만 변환할 것, 0 크기 때 입력 역변환까지 생략할 것을 확인했다. 실행 테스트·실제 DPI/전체화면 검증은 하지 않았다.
