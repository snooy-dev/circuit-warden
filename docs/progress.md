# 진행 상태

갱신일: 2026-11-11

## 현재 단계

- 엔진 패키지·스프라이트 통합은 자동 106개와 실제 PNG·SDL 8단계 검사를 통과했고 [Draft PR #2](https://github.com/snooy-dev/circuit-warden/pull/2)를 생성했다. main은 병합하지 않았다.
- 사용자 요청·중단 후 계속 지시에 따라 `feature/character-movement`에서 캐릭터 표시·좌우 이동을 구현 중이다. [010 명세](../specs/010-character-movement/spec.md)·[계획](../specs/010-character-movement/plan.md)·[검증](../specs/010-character-movement/verification.md)을 따른다.
- idle v7·Run v4 좌우 시트를 버전 없는 assets/warden 이름으로 복사했고 3개 SHA-256·규격·시간이 원본과 일치했다. `.gitattributes`에 PNG binary를 명시했다. 원본 art를 수정하지 않았다.

## 확정 범위와 가정

- Python + Pico2D, 기존 engine/game_framework API를 재사용한다. 표시·키 유지 이동·정지·idle/Run 전환·방향·경계·포커스 정리를 검사한다.
- 이동 축·키·속도·배율·바닥선은 [기술 구조](architecture.md#캐릭터-이동-검사)의 검사 기본값이며 최종 게임 규칙이 아니다. 전투·VFX·충돌·물리·추가 아트 생성은 포함하지 않는다.
- 원본 main 작업 폴더의 미커밋 정책·도구 변경을 보존하고 별도 파일 사본에서 검증하며 원격 예상 head를 확인해 게시한다.

## 미결 사항

- 010의 코드·자동/실제 창 검사와 문서 대조·커밋.
- 009의 이전 사용자 직접 확인·확인 후 임시 자료 정리(T013/T014/T016). 해당 자료는 보존한다.
- 엔진 PR 병합, 게임 PR 생성·병합은 별도 결정이다.
- 최종 이동감·시각적 품질의 사용자 직접 확인, 실물 고DPI·대량 객체 성능·리셋 자동 복구는 미확인이다.

## 다음 작업

에셋 증분을 커밋하고 game 패키지의 표시·입력·이동을 구현·검증한 뒤 관련 docs와 010 검증 근거를 함께 커밋한다.
