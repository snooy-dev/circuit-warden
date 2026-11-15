# Tasks: 감사 1~5 수정

**Input**: spec.md, plan.md와 기준 docs
**Implementation authorization**: 2026-11-15 사용자 요청으로5개 수정·효과 보존·검증·로컬 커밋을 수행한다.

## Phase 1: Design & Documentation Readiness

- [x] T001 specs/013-audit-fixes/spec.md·plan.md와 docs/architecture.md·시스템 기준의 범위/모순을 확인한다.
- [x] T002 docs/progress.md에 요청·브랜치·사용자 변경 보존을 기록하고 specs/013-audit-fixes/tasks.md의 요구 대응을 analyze한다.

## Phase 2: User Story 1 - 입력과 공격 첫 프레임

- [x] T003 [P] [US1] game/character.py와 tests/unit/test_input_buffer.py·tests/integration/test_character_scene.py에서 FR-001 예약 공격 첫 프레임을 수정·회귀 검사한다.
- [x] T004 [P] [US1] engine/loop.py와 tests/unit/test_engine.py에서 FR-002 표시 전환 전에 대기 클릭을 처리하고 같은/다음 묶음·종료를 회귀 검사한다.

## Phase 3: User Story 3 - 상태와 수명 정리

- [x] T005 [US3] game/character.py에서 FR-005 요청 플래그를 제거하고 단일 판정을 사용한다. tests/unit/test_charge_teleport.py의 내부 플래그 확인을 동작 검사로 바꾼다(T003과 같은 담당).
- [x] T006 [P] [US3] game_framework/world.py·ui.py와 tests/unit/test_game_framework.py에서 FR-004 snapshot 해제·예외 보관 약한 참조 회귀를 검사한다.
- [x] T007 docs/architecture.md·specs/013-audit-fixes/verification.md·tasks.md에 T003/005 결과를 기록하고 해당 증분만 커밋한다.
- [x] T008 docs/architecture.md·specs/013-audit-fixes/verification.md·tasks.md에 T004/006 결과를 기록하고 해당 증분만 커밋한다.

## Phase 4: User Story 2 - 효과 모양 유지와 성능

- [x] T009 [US2] requirements.txt에 NumPy 버전을 명시하고 게임 .venv에 설치하며 docs/architecture.md에 기록한다.
- [x] T010 [US2] 변경 전 game/charge.py의 출력 기준을 tests/fixtures/charge_composition.json에 보존하고 game/charge.py를 배열 합성으로 바꾼다.
- [x] T011 [US2] tests/unit/test_charge_teleport.py·tests/unit/test_teleport_link.py·tests/integration/test_charge_scene.py에서 RGBA·캐시·수명·자산을 검사한다.
- [x] T012 [US2] tests/performance/charge_benchmark.py로 전후 동일 시나리오 교대 측정과 출력 일치를 검증한다. FR-003/SC-003 미충족 시 보완한다.
- [x] T013 [US2] docs/architecture.md·tests/README.md·specs/013-audit-fixes/verification.md에 결과를 기록하고 성능 증분을 커밋한다.

## Phase 5: Documentation & Completion

- [x] T014 tests/ 전체 unittest를 한 번 실행하고 실제 SDL에서 예약 공격·표시 전환·전하·종료를 확인한다. 필요 시 tests/smoke/에 최소 재현 도구를 추가한다.
- [x] T015 docs/progress.md·specs/013-audit-fixes/verification.md·tasks.md를 결과와 맞추고 spec/plan/docs/코드 대응을 converge한다.
- [x] T016 assets/warden/jump_*.png 해시·기존 tmp 보존과 git diff --check를 확인하고 관련 변경만 최종 커밋한다.

## Dependencies & Execution Order

T001→T002 이후 T003/005, T004, T006, T009/010은 파일 담당을 나눠 진행한다. tests/unit/test_charge_teleport.py는 캐릭터 담당 완료 후 성능 담당에게 넘긴다. T007·T008은 각 검증된 증분에서 수행하고 성능 전체 완료까지 미루지 않는다. T011→T012→T013 후 T014→T015→T016을 완료한다. 문서와 Git은 주 에이전트만 수정한다.
