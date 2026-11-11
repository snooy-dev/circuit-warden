# Data Model: 캐릭터 검사

- Animation metadata: file(에셋 폴더 내 PNG), frameSize(128×104), columns(양수), count(양수), pivot(픽셀), durationsMs(count개 양수), loop=true. 이미지 크기·프레임 영역은 SpriteFrame에서 검사한다.
- Character: x(유한 월드 좌표), facing(-1 또는 1), pressed(set), clips(idle/run_left/run_right), player(SpritePlayer). speed·표시 배율은 기술 기본값이다.
- 전이: 무입력/상쇄/경계 정지 → idle, 실제 좌/우 이동 → 해당 Run. 같은 clip은 시간 유지, 다른 clip은 처음부터. 포커스 상실/최소화 → 입력 비우기. 장면 종료 → Level 정리 후 ImageStore.close.
