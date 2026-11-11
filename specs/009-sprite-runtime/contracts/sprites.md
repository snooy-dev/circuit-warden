# Contract: 스프라이트·이미지 공개 호출

상태: 이미지·프레임·표시·장면 수명·재생을 구현했다. 실제 사용자 출력 확인은 미완료.

## 이미지

- ImageStore(root): 명시적인 리소스 기준 경로. 생성 시 이미지 로딩 없음.
- load(path) -> ImageRef: 절대 경로 또는 root 기준 상대 경로를 실제 경로로 정규화해 캐시. renderer 없거나 store가 닫혔으면 오류. 파일 누락/로딩 실패는 원인과 파일 경로를 포함.
- ImageRef: 크기·경로·닫힘 상태 조회. raw pico.Image는 외부에 노출하지 않음. 내부 renderer 세션과 다른 실행에서 사용하지 않음.
- close(): 닫기/이미지 해제는 반복해도 무해. 살아 있는 texture 포인터를 먼저 분리한 뒤 한 번 파괴. 이미 닫힌 frame/image의 출력은 RuntimeError.
- 개별 ImageRef.close 뒤 같은 저장소에서 load하면 닫힌 캐시 오류를 낸다. 재사용에는 새 저장소를 만든다.
- 유효 이미지 해제는 renderer 생존 중, 동일 스레드의 장면 종료에서 수행. draw 중 load/close하지 않음.

## 프레임과 재생

- SpriteFrame(image, rect, pivot=(0.5,0.5)): 좌상단 정수 source 영역과 정규화 기준점. 이미지 크기를 넘거나 크기가 0 이하면 ValueError.
- SpriteClip(frames, durations, loop=True): 각 프레임 지속 시간은 초. 프레임·시간 목록은 불변으로 보관.
- SpritePlayer(clip), play(clip, restart=False), update(dt), frame, finished.
- 별도 play 이름 테이블·자동 GameObject 등록·이벤트 콜백은 없음.
- 같은 clip의 play는 재시작하지 않음. 다른 clip/명시 restart는 처음부터. 반복과 단발의 상세 경계는 [데이터 모델](../data-model.md).

## 표시

- draw_sprite(frame, transform, position, size, opacity=1, flip_x=False).
- transform은 기존 WorldTransform 또는 UITransform. position은 논리 기준점, size는 논리 너비/높이. 유한 좌표, 양수 크기, 0~1 opacity를 검사.
- GameObject.render_items()의 drawable이 호출하고, UIElement.draw(origin, transform, opacity)가 자기 좌표를 넘겨 호출한다.
- draw_order/visible/opacity의 기존 소유자는 Renderer/RenderItem/UIElement. 새 정렬·소유 컨테이너 없음.
- draw_sprite는 닫힘 검사와 pivot bounds를 계산한 뒤 기존 draw_image의 선택적 source 경로로 위임한다.
- 확장 서명: draw_image(image, transform, bounds, opacity=1, *, source=None, flip_x=False). source=(left,top,width,height). source=None과 flip_x=False의 기존 동작·SDL 오류 검사는 유지.
- source가 있는 경우 source 검증 후 clip_draw, flip_x=True면 clip_composite_draw(rad=0). 전체 이미지 반전 요청은 전체 크기 source로 취급. 대상 크기 w/h를 모두 전달한다.
- 알파/blend 상태는 성공과 Python 예외 모두 복원한다. 출력 무효 시 draw를 생략하며 상태를 변경하지 않는다.
- Pico2D clip 내부 SDL 반환값은 관측 불가. 이 한계는 Python 예외·로딩 오류를 숨겨도 된다는 의미가 아니다.

## 장면 수명

- LevelScene(level, canvas=None, *, camera_center=(0,0), view_height=10, images=None).
- images=None 기존 호출 호환. 전달한 ImageStore는 이 장면이 소유하며 다른 장면에 공유하지 않는다.
- level.on_open 등 진입 준비에서 이미지를 로드한다. store 참조는 필요한 구체 Level/객체에 명시 전달한다. 전역 registry 없음.
- exit는 level/canvas/images 순으로 모두 정리를 시도하고 복수 오류를 보존한다. 반복 exit에서도 유효 texture를 다시 파괴하지 않는다.
- 이미지 있는 장면을 다시 진입할 때 새 store를 제공한 새 장면을 만든다. 이전 frame을 다음 renderer 세션으로 넘기지 않는다.
- 기존 입력·update·렌더 순서·장치 리셋 종료 정책은 유지한다.

## 임시 검사 경계

실 시트·로컬 하네스·그 연결은 제품 계약의 필수 자산이 아니다. 자동 검사에는 대역과 검사 중 생성·정리하는 합성 입력을 사용한다. 사용자 직접 확인용 임시 하네스는 자동 검사용 단명 임시 파일과 달리 확인 전 삭제하지 않는다.