# Research: 스프라이트 실행 기능

상태: 2026-11-11 설계 조사 완료. 실제 구현·검증 결과는 verification.md에 기록한다. 아래는 기술 선택이며 사용자 게임 정책 확정이 아니다.

## 엔진 참고

- [Unity SpriteRenderer](https://docs.unity.com/en-us/engine/6000.0/manual/unity2d/sprite/sprite-renderer-reference): 이미지 자산과 표시 상태 분리. 반전·투명도·순서는 개체별로 적용한다.
- [Unity Sprite Atlas](https://docs.unity.com/en-us/engine/6000.0/manual/unity2d/sprite/atlas): 여러 프레임이 텍스처를 공유. Pico2D에서 같은 batching 성능을 보장하는 근거로 사용하지 않는다.
- [Unreal Paper2D Flipbooks](https://dev.epicgames.com/documentation/en-us/unreal-engine/paper-2d-flipbooks-in-unreal-engine): 프레임 순서와 유지 시간으로 동작을 표현한다.
- [GameMaker Texture Groups](https://manual.gamemaker.io/monthly/en/Settings/Texture_Groups.htm): 표시 중 끊김을 줄이기 위해 필요한 이미지를 미리 준비한다.
- [Unity Addressables 수명](https://docs.unity3d.com/Packages/com.unity.addressables@1.21/manual/MemoryManagement.html): 로딩과 해제의 대응. 이번에는 참조 수 관리·번들·원격 로딩을 복제하지 않는다.

위 공식 문서는 이번 대화의 선행 조사에서 확인했다. 특정 최신 엔진 버전과 호환되는 구현을 만드는 작업은 아니다.

## 기존 코드와 분기 기준

- **Decision**: feature/engine @ a32333c에서 분기.
- **Rationale**: main과 달리 008의 Level/Canvas/Renderer/좌표/수명 기능이 통합되어 있다. 기존 틀을 사용해야 중복 엔진을 만들지 않는다.
- **Alternatives considered**: main에서 독자 스프라이트 루프 작성은 기존 통합 구조와 충돌하므로 기각.
- 근거: engine.py의 _refresh_display는 실제 output_size를 pico.canvas_width/height에 반영한다. game_framework.py의 WorldTransform/UITransform은 좌상단 출력 좌표를 반환하며 Renderer는 월드→UI를 처리한다.

## 클리핑과 상태 격리

- **Decision**: 기존 draw_image의 알파/blend 관리 범위에서 선택적 source를 Pico2D clip_draw/clip_composite_draw로 출력.
- **Rationale**: 사용자 권장을 따르면서 기존 전체 이미지 호출과 상태 복원을 재사용한다.
- **Alternatives considered**: 직접 SDL source rect 렌더링은 오류 반환을 확인할 수 있으나 이번 우선안은 Pico2D 클리핑이다. 기존 draw_image의 전체 이미지 경로는 유지한다.
- 설치 Pico2D 1.5.1의 pico2d.py:356~374 확인: clip_draw의 source는 좌하단, 목적지는 중심. clip_composite_draw 기본 출력 크기는 전체 이미지다. 두 크기를 항상 전달한다.
- 같은 함수는 SDL_RenderCopy(Ex) 반환값을 전달하지 않는다. native draw 오류를 완전히 검출한다는 보장은 제외하고 실제 화면 검사와 별도 위험으로 남긴다. SDL_GetError만 뒤늦게 읽어 성공/실패를 추정하지 않는다.
- viewport 원점을 재가산하지 않고 실제 출력 높이로 한 번 y를 바꾼다. clip 경로는 정수 좌표 양자화가 있으므로 소수 위치의 화면 검사도 필요하다.

## 이미지 수명

- **Decision**: 장면 전용 ImageStore와 닫을 수 있는 ImageRef. 원본 pico.Image는 내부에서만 사용하며 닫을 때 texture를 분리한 후 유효 texture를 한 번 해제.
- **Rationale**: pico2d.py:319~320의 Image.__del__은 texture를 파괴한다. 수동 파괴 후 포인터를 남기면 이중해제 위험이 있다. 반대로 참조를 None으로만 만들면 draw 실패 traceback이 원본 Image를 보유해 렌더러 종료 뒤 소멸할 수 있다.
- **Alternatives considered**: raw Image 공개/전역 캐시/참조 수/단순 dict.clear는 이번 수명 요구에 부적합하거나 불필요하게 복잡하다.
- 유효 texture의 해제는 한 번, 닫힌 handle은 실패, 반복 close는 무해. 분리 후 Pico2D 소멸자의 None 처리와 예외 traceback 보유 시 정리는 실제 SDL로 검증할 항목이다.
- LevelScene.exit에서 level/canvas 정리를 모두 시도한 뒤 이미지를 닫는다. Engine.run의 finally는 이후 close_canvas를 실행한다. 기존 오류 모음·정리 순서를 보존한다.
- 장치 리셋 자동 복구는 현행 종료 정책을 유지하며 범용 자원 복구 체계는 도입하지 않는다.

## 프레임과 재생

- **Decision**: 좌상단 영역·정규화 pivot, 프레임별 양수 초, 불변 clip과 개체별 player.
- **Rationale**: 확인한 로컬 idle 메타데이터는 41/42ms, Run은 30ms다. 정수 FPS 고정은 원래 시간을 왜곡한다. 프레임별 시간은 이 두 경우를 모두 표현한다.
- **Alternatives considered**: 고정 FPS 전용·파일명 자동 정렬·애니메이션 이벤트·상태 머신은 이번 범위에 필요하지 않다.
- 누적 종료 시각과 bisect 검색으로 선택하며 전체 길이로 나눈 나머지로 반복을 처리한다. dt=0은 불변, dt<0/비유한은 거부. 경계 오차는 검사로 확인한다.
- 기존 art의 frames/anchor/durationsMs가 게임용 최종 포맷이라는 뜻은 아니다. 임시 하네스에서 실 배치와 기준점을 확인해 매핑하고 원본을 수정하지 않는다.

## 임시 출력 검사

- **Decision**: 저장소 밖 별도 로컬 임시 폴더를 사용하고, 원본을 읽기 전용으로 참조한다. 필요한 경우에만 복사한다.
- **Rationale**: 실 시트 미반영 및 사용자 확인 전 보존을 동시에 만족한다. 자동 정리되는 TemporaryDirectory나 종료 시 삭제 코드를 사용하지 않는다.
- **Alternatives considered**: assets 복사, 기본 main 연결, 확인 전 자동 삭제는 사용자 조건에 어긋난다.
- 사용자 직접 확인이 끝난 뒤 생성 목록에 포함된 하네스·설정·복사본만 제거한다. 원본·제품 구현·자동 회귀 검사는 유지한다.