# Data Model: 스프라이트

상태: 이미지·프레임·클립·재생기 구현. [공개 계약](contracts/sprites.md)과 함께 본다.

| 자료 | 필드·관계 | 검증·수명 |
|---|---|---|
| ImageStore | root: 절대 기준 경로, cache: 정규화 실제 경로 → ImageRef, closed | root를 실행 위치와 무관하게 고정. load는 renderer 생성 후. close 후 재사용 불가 |
| ImageRef | path, width/height, 내부 pico.Image, closed | 외부에 raw Image 공개 금지. 내부 유효 texture를 분리·해제, 닫힌 참조 사용 거부 |
| SpriteFrame | image: ImageRef, rect: (left, top, width, height), pivot: (px, py) | 정수 영역, 양수 크기, 이미지 안에 완전히 포함. pivot은 좌상단 기준 각 0~1, 기본 (0.5,0.5) |
| SpriteClip | frames: tuple[SpriteFrame], durations: tuple[float], loop: bool | 비어 있지 않음, 길이 동일, 각 duration과 합계가 양수 유한 초. 각 프레임을 구분 가능한 유한 누적 종료 시각을 계산 |
| SpritePlayer | clip, elapsed, frame, finished | 개체별 상태. dt는 유한 비음수. 클립 데이터와 이미지 공유는 가능 |
| 임시 확인 기록 | 생성 파일 목록, 읽기 전용 원본 경로, 실행 방법, 관찰·사용자 확인·정리 상태 | 제품 런타임 데이터 모델이 아님. 실 시트 및 로컬 설정은 미추적 |

## 재생 상태

- 생성/다른 clip 선택/명시 restart: elapsed=0, 첫 frame, finished=False.
- 같은 clip을 restart 없이 지정: 상태 불변. 값이 비슷한 별도 clip 객체는 다른 clip으로 취급.
- 반복: elapsed를 전체 시간 내에 유지하고 해당 반개구간 [시작, 종료)의 frame 선택. 마지막 종료 경계는 처음으로.
- 단발: 전체 시간 이상이면 elapsed를 전체 시간으로 제한, 마지막 frame, finished=True.
- 한 프레임 클립도 같은 규칙. 단발은 그 프레임 유지 시간이 지난 뒤 완료.
- draw는 재생 상태를 바꾸지 않음. 실제 엔진 전달 dt(최대 0.1초)를 사용하며 별도 실제 시계를 추가하지 않음.

## 기준점과 좌표

source rect와 pivot은 이미지 좌상단 기준이다. position은 표시할 기준점의 월드 또는 UI 논리 좌표이며 size는 해당 좌표계의 양수 너비·높이다. 프레임 해상도가 달라도 같은 position으로 기준점을 맞춘다.

수평 반전 시 이미지와 함께 pivot_x를 1-pivot_x로 변환한다. 월드에서는 y-up, UI에서는 y-down을 사용한다. 최종 source bottom과 출력 center의 변환은 렌더 경계에서 한 번만 수행한다.

## 닫기

열린 장면 → 객체/Canvas 정리 시도 → ImageStore.close → 모든 ImageRef 무효화 및 texture 해제 → 렌더러 종료.
예외 중에도 뒤 정리를 시도한다. ImageRef 또는 traceback이 외부에 남더라도 유효 texture를 계속 소유하지 않는다. store가 닫히면 load를 거부하고 재진입에는 새 store를 사용한다.