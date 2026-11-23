# Tasks: 워든 전투와 일회성 전하

## Phase 1: Setup and Foundational

- [x] T001 기준 문서와 기존 입력·충돌·아트 검토, specs/017-warden-combat 명세·계획 확정.

## Phase 2: User Story 1 - 돌진 회피와 소비

- [x] T002 [US1] game/charge.py, game/mode.py, game/scene.py에서 성공 시 소비, 실패 시 보존, 예약 재검사와 재시작 복원 구현. FR-001.
- [x] T003 [US1] game/character.py와 game/scene.py에서 100ms 돌진 피해 보호와 기존 몸통 밀림 확인. FR-003.
- [x] T004 [US1] tests/integration/test_charge_scene.py와 tests/unit/test_basic_enemy.py의 영향 동작 검증. SC-002.

## Phase 3: User Story 2 - 공중 타격과 이탈

- [x] T005 [US2] game/character.py·game/scene.py에 J 공격과 실제 공중 타격 경로를 적용하고 tests/integration/test_basic_enemy.py에 시나리오 추가. FR-002.
- [x] T006 [US2] docs/game-design.md·docs/systems·docs/architecture.md·docs/progress.md 및 verification.md를 갱신하고 검증된 기본 전투를 커밋. SC-DOC.
- [ ] T007 [US2] assets/combat에 적중·전하 소비 원본/시트를 만들고 game/effects.py·game/scene.py·game/mode.py에서 연결. FR-004.

## Phase 4: Verification and convergence

- [ ] T008 tests/smoke/charge_smoke.py의 SDL 입력·소비·공중 명중·이탈을 실행하고 게임 크기 합성 검수. SC-001–003.
- [ ] T009 docs 및 verification.md 동기화, 잔여 요구 확인과 최종 증분 로컬 커밋. SC-DOC.
