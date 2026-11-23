# Tasks: 기술과 환경의 전하 생성

## Phase 1: Setup

- [x] T001 기준 docs 검토 및 specs/018-charge-generation 명세·계획·작업 작성.

## Phase 2: User Story 1 - 워든 기술

- [x] T002 [US1] game/mode.py·game/scene.py에 E 입력, 커서 생성·유효성, 한 개 제한, 쿨다운, 소비와 R을 추가한다. FR-001·FR-003.
- [x] T003 [US1] tests/integration/test_charge_scene.py의 표적 검사와 docs 및 verification.md를 갱신하고 첫 증분을 커밋한다.

## Phase 3: User Story 2 - 환경

- [ ] T004 [US2] game/scene.py·game/charge.py의 초기 위치 변동과 환경 소모 후 다른 위치에서 새로 생성되는 수명을 추가한다. FR-002·FR-003.
- [ ] T005 [US2] tests/integration·tests/smoke·tests/performance의 고정 배치 전제를 갱신하고 실제 SDL 경로와 소비·재생성·R을 확인한다.
- [ ] T006 현재 docs와 specs를 대조해 verification.md를 갱신하고 최종 증분을 커밋한다. SC-DOC.
