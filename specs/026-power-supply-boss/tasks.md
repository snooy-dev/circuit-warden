# Tasks: 전원 조립체

**Input** 026 명세·계획과 기존 전원 구역 기준

**Implementation authorization** 2026-11-26 사용자 요청

## Phase 1: Design & Documentation Readiness

- [x] T001 기획서 20~21쪽과 시험실 지형을 확인하고 spec.md·plan.md에 범위·배치를 기록한다.

## Phase 2: User Story 1 - 공유 판정

- [x] T002 [US1] game/enemy.py와 game/scene.py에서 몸통의 두 축 위치와 이동을 스윕에 연결한다.
- [x] T003 [US1] 기존 적 전투와 충돌의 대상 검사를 하고 기술 구조·검증 근거와 첫 증분을 커밋한다.

## Phase 3: User Story 1 - 보스와 출구

- [ ] T004 [US1] assets/enemies/와 game/enemy.py에 전원 조립체 원화, 세 공격, 경고와 회복을 연결한다.
- [ ] T005 [US1] game/power_supply_map.py와 맵 데이터에 보스·전하·셔터·처치·R을 연결한다.
- [ ] T006 [US1] 표적 자동 검사, 두 경로 및 실제 SDL 보스 전투를 확인한다.

## Phase 4: Documentation & Completion (mandatory)

- [ ] T007 게임·적·아트·구조·진행과 verification.md를 결과에 맞춘다.
- [ ] T008 요구와 코드·검증을 대조하고 최종 증분을 커밋한다.

## Dependencies & Execution Order

T001 → T002–T003 → T004–T006 → T007–T008.
