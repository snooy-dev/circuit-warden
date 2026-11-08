# Tasks: 기본 실행 기반

**Input**: spec.md, plan.md와 docs/architecture.md
**Implementation authorization**: 2026-11-08 사용자 계획 승인. 기본 실행 기반의 구현·검증 진행.

## Rules

비단순 동작은 자동 검사한다. docs·실제 창 검증·verification은 필수다. 증거를 확인한 뒤 체크한다.

## Phase 1: Design & Documentation Readiness

- [X] T001 specs/001-engine-foundation/spec.md, plan.md와 기준 docs의 모순·미정을 분석한다.
- [X] T002 docs/architecture.md, docs/game-design.md, docs/progress.md에 승인 범위·기술 결정을 반영한다.

## Phase 2: Foundational

- [X] T003 tests/test_engine.py에 가짜 창·장면·시계로 제어 흐름 검사 기반을 작성하고 미구현 실패를 확인한다 (FR-006).

## Phase 3: User Story 1 - 실행·종료

- [X] T004 [US1] tests/test_engine.py에 창 실패·장면 콜백 오류·중첩 실행·종료 우선 검사 작성 (FR-001).
- [X] T005 [US1] engine.py에 Scene, Engine 실행 수명·오류 정리·중첩 실행 거부 구현 (FR-001).

## Phase 4: User Story 2 - 입력·시간

- [X] T006 [US2] tests/test_engine.py에 입력 순서·원형 보존·dt 제한·대기 검사 작성 (FR-002~003).
- [X] T007 [US2] engine.py에 입력 → 갱신 → 그리기 루프와 시간 제한 구현 (FR-002~003).

## Phase 5: User Story 3 - 장면 교체

- [X] T008 [US3] tests/test_engine.py에 마지막 요청·생명주기·전환 실패·후속 요청 검사 작성 (FR-004).
- [X] T009 [US3] engine.py에 프레임 끝 전환과 첫 갱신 시간 리셋 구현 (FR-004).
- [X] T010 [US3] tests/test_demo.py와 main.py에 에셋 없는 두 장면·시간 이동·마우스 반응 구현 및 검사 (FR-005).

## Phase 6: Documentation & Completion (mandatory)

- [X] T011 tests/ 전체 자동 검사를 실행하고 main.py 실제 창에서 표시·움직임·입력·왕복·두 종료 경로 확인 (FR-006, SC-001~002).
- [X] T012 README.md와 docs/README.md, docs/architecture.md, docs/workflow.md를 결과와 맞추고 영향 없는 문서 이유 기록 (SC-DOC).
- [X] T013 specs/001-engine-foundation/verification.md에 명령·결과·미실행·요구사항 대응 기록 (SC-DOC).
- [X] T014 docs/progress.md에 현재 상태·미결·다음 작업 반영 (SC-DOC).
- [X] T015 specs/001-engine-foundation/의 spec/plan/tasks와 docs·코드·검증 증거를 converge로 대조하고 남은 필수 작업 해결 (SC-DOC).

## Dependencies & Execution Order

T001~003 → US1 → US2 → US3 → T011~015. 같은 engine.py를 수정하므로 순차 구현한다. 테스트를 먼저 작성해 미구현 실패를 확인한 뒤 작은 공유 루프를 구현한다. US1은 실행·종료, US2는 이벤트/시간, US3는 왕복/생명주기를 각각 독립 검사한다.

## Parallel execution examples

US1의 실제 창 검증 준비와 오류 테스트 검토, US2의 입력 검사 검토와 문서 검토, US3의 화면 시각 검토와 전환 테스트 검토는 서로 다른 파일에서 가능하다. 이번 작은 변경은 순차 실행한다.

## Implementation Strategy

먼저 실행·정리 경로를 확보하고 입력/시간과 전환을 연결한다. 범위 전체와 필수 검증까지 마무리하며 US1만으로 완료 처리하지 않는다.
