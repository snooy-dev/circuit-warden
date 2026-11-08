---
description: Circuit Warden tasks with mandatory docs maintenance
---

# Tasks: [FEATURE NAME]

**Input**: 이 기능의 spec.md, plan.md 및 참조된 docs
**Implementation authorization**: [사용자의 구현 시작 지시 또는 보류]

## Rules

- 작업은 `- [ ] T001 [US1] 설명과 실제 파일 경로` 형식, 유일한 ID로 쓴다.
- 아래 예시는 실제 요구에 맞는 작업으로 교체하고 연속 ID를 부여한다.
- 비단순 게임 동작에는 자동 테스트가 필수다. 문서만 수정하면 문서 검증을 한다.
- docs 작업을 선택적 polish로 미루지 않는다. 설계 결정 직후 기록하고 구현 후 다시 대조한다.
- 증거 없이 체크하지 않는다. 구현 보류 상태에서는 구현·에셋 생성 작업을 시작하지 않는다.

## Phase 1: Design & Documentation Readiness

- [ ] T001 기준 docs와 spec/plan을 대조하고 미정·충돌을 해결한다.
- [ ] T002 확정된 결정을 해당 docs에 반영하고 docs/progress.md를 현재 상태로 갱신한다.

## Phase 2: User Story 1 - [목표]

- [ ] T003 [US1] [FR 요구사항]을 검증할 테스트를 [경로]에 작성/갱신하고 변경 전 결과를 확인한다.
- [ ] T004 [US1] [승인된 기능]을 [실제 코드/에셋 경로]에 구현한다.
- [ ] T005 [US1] 해당 자동 테스트와 필요한 Pico2D/에셋 검사를 실행한다.

[필요한 시나리오만 반복. 무관한 웹/API/DB 기반 작업을 만들지 않는다.]

## Phase 3: Documentation & Completion (mandatory)

- [ ] T006 영향받는 docs의 규칙·구조·아트 기준을 결과와 맞춘다. 영향 없는 문서는 이유를 적는다.
- [ ] T007 기능의 verification.md에 요구사항별 명령·결과·미실행·docs 변경과 남은 문제를 기록한다.
- [ ] T008 docs/progress.md에 단계·활성 작업·미결 사항·다음 작업을 갱신한다.
- [ ] T009 spec/plan/tasks/docs/코드/증거를 대조하고 analyze/converge의 남은 필수 작업을 해결한다.

docs·verification은 현재 내용으로 갱신하고 오래된 규칙·해결된 질문·누적 실행 로그는 남기지 않는다. 변경 경위는 Git으로 확인한다. 완료 specs를 정리할 때는 docs 반영·검증 결과의 커밋 보존·참조 없음을 먼저 확인한다.

## Dependencies & Execution Order

[실제 의존 순서. T006~T009 상당의 완료 단계는 필수다. 문서·검증 누락 시 완료로 표시하지 않는다.]
