# Tasks: 기본 적 금속 먼지 덩어리

**Input**: [명세](spec.md), [계획](plan.md)

**Implementation authorization**: 기본 적 원화·hibit 표현의 게임 추가 및 전투 구현 요청.

## Phase 1: Design & Documentation Readiness

- [x] T001 `specs/013-basic-enemy/spec.md`와 `specs/013-basic-enemy/plan.md`에서 작업 범위·기술 기본값·게임 규칙을 맞춘다.
- [x] T002 `docs/systems/basic-enemy.md`, `docs/systems/README.md`, `docs/game-design.md`, `docs/progress.md`에 현재 범위와 준비 상태를 기록한다.

## Phase 2: User Story 1 - 기본 적에게 검을 맞히고 처치

- [x] T003 [US1] FR-001의 단일 적 리소스 `assets/enemies/metal_dust.png`와 피벗을 `game/enemy.py`, `game/scene.py`에 연결한다.
- [x] T004 [US1] FR-002의 공격 ID당 최대 1회 명중, 활성 구간 [0.10, 0.20)초, 방향 고정, 전방 85와 바닥 기준 높이 8~70을 `game/character.py`와 `game/scene.py`에 연결한다.
- [x] T005 [US1] FR-002의 초기 적 체력 3, 피해 1, 피격 표시 0.18초와 체력 0에서 전투와 표시 제거를 `game/enemy.py`, `game/scene.py`에 연결한다.
- [x] T006 [US1] SC-001의 양방향·활성 구간 경계·긴 프레임·중복 피해·체력 0을 `tests/unit/test_basic_enemy.py`, `tests/integration/test_basic_enemy.py`에서 확인한다.
- [x] T007 [US1] 적 표시 및 검 명중 증분의 구조·아트·검증을 `docs/architecture.md`, `docs/art-direction.md`, `specs/013-basic-enemy/verification.md`에 실제 결과로 기록하고 증분을 커밋한다.

## Phase 3: User Story 2 - 돌진을 회피하고 다시 도전

- [ ] T008 [US2] FR-003의 대기·접근·예고·돌진·회복과 예고 시 방향 고정 및 돌진당 최대 1회 피해를 `game/enemy.py`, `game/scene.py`에 연결한다.
- [ ] T009 [US2] FR-004의 초기 워든 체력 5·하한 0·피해 1·피격 보호 0.75초와 체력 0에서 일반 입력과 적 행동 정지를 `game/character.py`, `game/scene.py`, `game/mode.py`에 연결한다.
- [ ] T010 [US2] FR-005의 R로 체력·위치·행동·피격 보호와 공격 중복 판정 기록 초기화를 `game/scene.py`, `game/mode.py`에 연결한다.
- [ ] T011 [US2] FR-003~006 및 SC-003의 실제 접촉, 점프 회피, 보호, 대시 중 피격, 사망 및 R과 기존 조작을 `tests/unit/test_basic_enemy.py`, `tests/integration/test_basic_enemy.py`, `tests/integration/test_character_scene.py`, `tests/integration/test_jump_animation.py`, `tests/integration/test_dash_animation.py`, `tests/unit/test_character.py`, `tests/unit/test_input_buffer.py`에서 확인한다.
- [ ] T012 [US2] SC-002의 이미지 정렬·예고·돌진·회복·피해·점프 회피·사망·R을 `tests/smoke/basic_enemy_smoke.py`로 실제 SDL 창에서 확인한다.
- [ ] T013 [US2] 돌진 및 재시작 증분의 규칙·구조·검증을 `docs/systems/basic-enemy.md`, `docs/architecture.md`, `specs/013-basic-enemy/verification.md`에 맞추고 검증된 증분을 커밋한다.

## Phase 4: Documentation & Completion (mandatory)

- [ ] T014 SC-DOC의 기획·아트·검사 안내·진행 상태를 `docs/game-design.md`, `docs/art-direction.md`, `tests/README.md`, `docs/progress.md`에 동기화하고 `specs/013-basic-enemy/verification.md`에 실제 명령·결과·미실행 항목을 기록한다.
- [ ] T015 `specs/013-basic-enemy/tasks.md`, `specs/013-basic-enemy/verification.md`, `docs/progress.md`를 실제 코드 및 실행 결과와 대조한다. converge 누락을 해결하고 완료 작업을 표시한다.

## Dependencies & Execution Order

T001~002 후 T003~007을 실행한 뒤 T008~013, T014~015 순서로 진행한다. 구현과 독립적으로 테스트 사례를 준비할 수 있으며 같은 파일을 동시에 편집하지 않는다. 첫 플레이 가능 증분은 US1이며 사용자 요청의 전체 범위는 US2까지다.
