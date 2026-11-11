# 프로젝트 문서

이 폴더는 Circuit Warden의 장기 유지 문서다. 기본 실행 기반의 명세·계획은 사용자 승인을 받았고 코드 구현 및 자동 검사를 마쳤다. 실제 창과 사용자 키 조작 검사까지 완료했다.

## 읽는 순서

1. [진행 상태](progress.md): 목표, 구현 허가 여부, 다음 작업.
2. [게임 설계](game-design.md), [시스템 설계](systems/README.md): 의도와 규칙.
3. [기술 구조](architecture.md), [아트 기준](art-direction.md): 필요한 부분만.
4. 게임 기능 개발일 때만 활성 기능의 `specs/<feature>/spec.md`, `plan.md`, `tasks.md`, `verification.md`.

반복 스프라이트 생성·보정은 Spec Kit 문서를 작성하지 않는다. [아트 기준](art-direction.md)과 사용자 요청으로 작업하고 결과·검사는 채팅으로 보고한다.

엔진 통합 브랜치는 `feature/engine`이다. [008 계획](../specs/008-game-framework/plan.md)의 P1~P5 구현·검증을 통합했으며, 과거 구현 근거는 [008 검증 결과](../specs/008-game-framework/verification.md), 현재 실행·검사는 [tests 안내](../tests/README.md)를 따른다. 게임 브랜치에는 idle·Run 기반 표시·이동이 연결돼 있으며 최종 게임 규칙은 별도다. 승인된 엔진/게임 API 경계와 game·tests 분류는 [기술 구조](architecture.md#코드-폴더-구조)를 따른다.

## 운영 원칙

- docs는 현재 기준, specs는 진행 중인 변경의 작업 문서다. 변경 이력은 Git 로그·diff로 확인한다.
- 제안·가정·미정·확정·대체·폐기와 미구현·구현 중·검증 완료를 구분한다.
- 승인된 규칙은 한 문서에서 소유하고 다른 곳은 참조한다.
- 결정 직후 기록 → 계획에 문서 영향 포함 → 구현 후 docs 갱신 → 증거와 함께 완료 판정한다.
- PPTX는 제안 자료다. 이번 설정은 원본 내용의 승인이나 재작성 작업이 아니다.
- 이전 내용을 수정·대체하고 폐기된 규칙과 해결된 질문은 제거한다. 현재 선택의 이유는 짧게 남기되 별도 결정 연표·변경일지를 쌓지 않는다.
- 완료 specs의 정리 조건과 미커밋 근거 보호는 [작업 규칙](../AGENTS.md)을 따른다.

[워크플로우](workflow.md), [도구 구성](tooling.md), [AGENTS.md](../AGENTS.md), [Constitution](../.specify/memory/constitution.md)를 함께 따른다.

스프라이트 표시·재생·이미지 수명은 [009 명세](../specs/009-sprite-runtime/spec.md)와 [통합 검증](../specs/009-sprite-runtime/verification.md)을 따른다.

캐릭터 출력·좌우 이동은 [010 명세](../specs/010-character-movement/spec.md)·[실행법](../specs/010-character-movement/quickstart.md)·[검증](../specs/010-character-movement/verification.md)을 따른다.
