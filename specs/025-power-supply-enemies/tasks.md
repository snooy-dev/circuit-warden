# Tasks: 전원 구역 몬스터

**Input** 이 기능의 spec.md, plan.md 및 기준 문서

**Implementation authorization** 2026-11-26 사용자 요청

## Phase 1: Design & Documentation Readiness

- [x] T001 공식 및 실제 플레이를 확인하고 지형·기존 기본 적과 요구사항을 대조한다.
- [x] T002 첫 배치와 통합 범위를 spec.md, plan.md, docs/progress.md에 기록한다.

## Phase 2: User Story 1 - 금속 먼지와 복수 전투

- [x] T003 [US1] game/enemy.py, game/scene.py, game/power_supply_map.py와 맵 데이터에 금속 먼지 배치·다중 전투·R을 연결한다.
- [x] T004 [US1] tests/integration/test_power_supply_enemies.py와 기존 훈련장 적 테스트로 적별 타격·접촉·초기화를 검증한다.
- [x] T005 [US1] 기준 문서와 verification.md를 갱신하고 첫 증분을 커밋한다.

## Phase 3: User Story 1 - 구역별 몬스터

- [x] T006 [US1] assets/enemies/와 game/enemy.py에 냉각 팬·콘덴서의 원화, 스프라이트, 행동을 연결한다.
- [x] T007 [US1] 맵에 새 적을 넣고 자동 검사와 SDL 화면에서 예고·공격·회피·복구·출력을 확인한다.
- [x] T008 [US1] docs/의 레벨·적·아트 기준과 진행 상태를 갱신한다.

## Phase 4: Documentation & Completion (mandatory)

- [x] T009 verification.md의 직접 검사와 미확인 항목을 spec/plan/tasks와 대조하고 남은 필요 작업을 해결한다.
- [x] T010 후속 증분을 검증된 파일만 선별해 커밋한다.

## Dependencies & Execution Order

T001–T002 → T003–T005 → T006–T008 → T009–T010.
