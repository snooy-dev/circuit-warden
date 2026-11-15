# Tasks: 전하 순간이동

**Input**: [spec.md](spec.md), [plan.md](plan.md)
**Implementation authorization**: 2026-11-15 사용자 요청과 후속 입력/취소 답변. PR 외 별도 승인 대기 없음.

## Phase 1: Design & Documentation Readiness

- [x] T001 specs/012-charge-teleport/spec.md·plan.md에서 기준 docs·사용자 답변·기술 시험값을 정리한다.
- [x] T002 docs/systems/charge-teleport.md·docs/systems/basic-gameplay.md·docs/progress.md에 결정을 반영한다.

## Phase 2: User Story 1 - 전하 선택과 즉시 재배치

- [x] T003 [US1] tests/unit/test_charge_teleport.py에 FR-001~005 거리·중첩·모든 행동 취소·선입력·대시 소모·도착 경계 검사를 작성한다.
- [x] T004 [US1] game/charge.py와 assets/charge에 승인 전하 상태·전환을 연결한다. value 0~1, 유한 비음수 dt, 공통 3초 위상을 보존한다.
- [x] T005 [US1] game/character.py·game/mode.py·game/scene.py에 중심 도착·즉시 취소·입력 우선순위·배치·월드 좌표 변환을 연결한다.
- [x] T006 [US1] tests/integration/test_charge_scene.py에서 보간 픽셀·실제 PNG·초기화 실패/종료 수명·창 배율 선택을 확인한다.
- [x] T007 [US1] 선택 검사를 실행하고 docs/architecture.md·docs/art-direction.md·docs/progress.md·specs/012-charge-teleport/verification.md를 갱신해 1차 증분을 커밋한다.

## Phase 3: User Story 2 - 고정 끝점 전류 연결

- [ ] T008 [US2] game/teleport_link.py에 승인 v4 생성식을 이식하고 FR-006의 400ms·독립 수명·무피해·방향/거리 보존을 검사한다. 출처 고지를 보존한다.
- [ ] T009 [US2] game/mode.py에 성공한 이동당 효과 1개를 연결한다. 동일 위치에는 생성하지 않는다.
- [ ] T010 [US2] tests/smoke/charge_smoke.py에서 실제 SDL 클릭·상태 취소·연속 이동·가로/세로/대각/역방향 연결·F6/F11 좌표·종료를 확인하고 캡처를 관찰한다.

## Phase 4: Documentation & Completion

- [ ] T011 docs/systems/charge-teleport.md·docs/game-design.md·docs/architecture.md·docs/art-direction.md·tests/README.md·docs/progress.md를 실제 결과에 맞춘다.
- [ ] T012 specs/012-charge-teleport/verification.md에 요구사항·검사 결과·미확인 조작감을 기록하고 문서/공백 확인 후 2차 증분을 커밋한다.
- [ ] T013 specs/012-charge-teleport/tasks.md와 spec/plan/docs/코드/검증을 converge로 대조해 남은 필수 작업을 해결한다.

## Dependencies & Execution Order

T001→T002→T003~T007→T009~T013. T008은 확정된 끝점 계약에 따라 US1과 다른 워크트리/파일에서 독립 구현 가능하다. US1 MVP는 전하 상태·선택·낙하이며 US2가 연결 표현을 완성한다. 구현 파일을 공유하는 작업은 순차 통합한다.
