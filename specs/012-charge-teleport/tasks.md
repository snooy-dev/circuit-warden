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

- [x] T008 [US2] game/teleport_link.py에 승인 v4 생성식을 이식하고 FR-006의 원본 형태·독립 수명·무피해·방향/거리 보존을 검사한다. 출처 고지를 보존한다.
- [x] T009 [US2] game/mode.py에 성공한 이동당 효과 1개를 연결한다. 동일 위치에는 생성하지 않는다.
- [x] T010 [US2] tests/smoke/charge_smoke.py에서 실제 SDL 클릭·상태 취소·연속 이동·가로/세로/대각/역방향 연결·F6/F11 좌표·종료를 확인하고 캡처를 관찰한다.

## Phase 4: Documentation & Completion

- [x] T011 docs/systems/charge-teleport.md·docs/game-design.md·docs/architecture.md·docs/art-direction.md·tests/README.md·docs/progress.md를 실제 결과에 맞춘다.
- [x] T012 specs/012-charge-teleport/verification.md에 요구사항·검사 결과·미확인 조작감을 기록하고 문서/공백 확인 후 2차 증분을 커밋한다.
- [x] T013 specs/012-charge-teleport/tasks.md와 spec/plan/docs/코드/검증을 converge로 대조해 남은 필수 작업을 해결한다.

## Dependencies & Execution Order

T001→T002→T003~T007→T009~T011→T014~T016→T012~T013. T008은 확정된 끝점 계약에 따라 US1과 다른 워크트리/파일에서 독립 구현 가능하다. US1 MVP는 전하 상태·선택·낙하이며 US2가 연결 표현을 완성한다. 구현 파일을 공유하는 작업은 순차 통합한다.

## Phase 5: 후속 연속 이동 규칙

- [x] T014 [US1] game/mode.py·game/charge.py·game/scene.py에 FR-008 목표 지점 즉시 활성화·진행 중 재시작 금지·마지막 유효 전하 선입력·종료 후 재검사·포커스/출력 취소를 연결한다.
- [x] T015 [US2] game/teleport_link.py의 승인 형태를100ms로 압축하고 tests/unit/test_teleport_link.py·tests/integration/test_charge_scene.py·tests/smoke/charge_smoke.py에서 경계·선입력·출력·수명을 확인한다.
- [x] T016 docs/systems/charge-teleport.md·docs/architecture.md·docs/art-direction.md·docs/progress.md와 specs/012-charge-teleport/verification.md를 새 규칙에 맞추고 T012~T013을 마무리한다.

## Phase 6: 공중 도착 후 약한 상승 관성

- [x] T017 [US1] FR-004와 플레이 피드백을 docs/systems/charge-teleport.md·specs/012-charge-teleport/spec.md·plan.md에 반영하고 game/character.py에160ms 상승·상단 제한·속도 비누적을 적용한다.
- [x] T018 [US1] tests/unit/test_charge_teleport.py·tests/integration/test_charge_scene.py·tests/smoke/charge_smoke.py에서 정점/복귀/상단/선입력/대시 이력과 실제 화면을 확인한다.
- [x] T019 docs/architecture.md·docs/game-design.md·docs/progress.md와 specs/012-charge-teleport/verification.md를 실제 결과에 맞추고 대응·링크·공백 확인 후 커밋한다.

## Phase 7: 전하 표시보다 넓은 클릭 판정

- [x] T020 [US1] FR-002와 사용자 요청을 시스템/spec/plan에 반영하고 game/charge.py의 클릭 반경을48로 확대한다. 기존 선택·중첩·선입력·배율 검사를 표시 밖 클릭으로 조정해 실행한다.
- [x] T021 tests/smoke/charge_smoke.py에서 판정 안/밖·선입력·창 크기 변경 후 선택을 확인하고 progress·verification을 갱신한다. 문서/코드 대응·링크·공백을 대조한 뒤 관련 증분만 커밋한다.
