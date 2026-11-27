# Tasks: 워든 게임용 모션 통합

**Input** [명세](spec.md)와 [계획](plan.md)

## Phase 1: Design & Documentation Readiness

- [x] T001 기존 이동·전투 규칙, 새 모션의 연결 범위와 기준 문서를 대조한다.

## Phase 2: User Story 1 - 새 워든 동작으로 플레이

- [x] T002 [US1] Git에 포함된 `art/game-ready/warden/`의 18종 시트와 메타데이터를 두 플레이 장면의 공통 로더에서 읽는다. (FR-001)
- [x] T003 [US1] `game/character.py`에서 이동·점프·대시 및 전투·순간이동에 새 클립을 연결하고 기존 조작과 판정을 보존한다. (FR-002~FR-004)
- [x] T004 [US1] 직접 영향이 있는 상태·조작을 개별 검사하고 SDL에서 플레이 장면의 실제 표시를 관찰한다. (SC-001~SC-003)

## Phase 3: Documentation & Completion (mandatory)

- [x] T005 기준 문서와 진행 상태를 구현에 맞추고 `verification.md`에 실행 명령, 결과와 남은 확인을 기록한다. (SC-DOC)
- [x] T006 명세·계획·작업·코드·검증을 대조하고 관련 변경을 한 증분으로 묶어 커밋할 수 있도록 준비한다.

## Dependencies & Execution Order

T001 → T002 → T003 → T004 → T005 → T006 순서로 진행한다.
