# Tasks: 게임프레임워크 — 계획별 작업

**현재 실행 근거**: 2026-11-10 사용자가 각 계획을 새 채팅에서 구현하고 독립 계획을 별도 워크트리에서 병렬 진행하도록 지시했다. 이전 검토 대기는 해제됐다. P1/P2부터 착수하고 P3는 P1/P2, P4는 P3, P5는 P1~P4의 검증된 커밋에 의존한다. 상세 기술 선택은 제안 기본값으로 구현하며 별도 사용자 확정으로 과장하지 않는다.

**Input**: spec.md, plan.md, plans/01-core.md~05-integration.md, docs/architecture.md
**Implementation authorization**: 2026-11-10 사용자가 각 계획의 새 채팅 구현과 독립 계획의 별도 워크트리 병렬 작업을 지시했다. P1/P2 즉시 착수, P3~P5는 선행 검증 커밋 통합 후 구현한다.

## Rules
[전체 계획](plan.md)의 범위/의존 관계를 따른다. 아래 작업만 단일 작업 목록으로 관리하고 하위 계획에 실행 체크리스트를 중복하지 않는다. 최종 결합 계약에 있는 미래 클래스/연결점을 앞 계획에서 미리 구현하지 않는다. drafts/test_game_framework.py.txt는 옛 초안이므로 승인 후 새 범위에 맞춰 검사한다. 자동 검사·실제 화면·사용자 확인을 구분한다.

## Phase 1: Design & Documentation Readiness
- [X] T001 spec.md의 사용자 의도·기술 제안·구현 보류와 plan.md의 분리 범위를 명시한다.
- [X] T002 plans/01-core.md~05-integration.md와 docs/architecture.md·docs/progress.md에 담당·선행 계약·검증·다음 검토 계획을 반영한다.

## Phase 2: P1 - 게임 객체·레벨·규칙
- [X] T003 [US1] tests/test_game_framework.py에 창 없는 소유·ID/재등록·생성/삭제·스냅샷·규칙 격리·부분 실패 검사를 작성한다 (FR-001~004).
- [X] T004 [US1] game_framework.py에 GameObject·Level·GameMode와 입력/update/열기/닫기를 구현한다. UI/Renderer/SDL은 도입하지 않는다.
- [X] T005 P1 자동 검사·기존 엔진 회귀를 실행하고 docs/architecture.md·docs/progress.md·verification.md의 P1 상태/근거를 갱신한 검증 증분을 커밋한다.

## Phase 3: P2 - 창·출력 기반
- [ ] T006 [US3] tests/test_engine.py에 window/output/viewport·DPI 비율·휠 구분·0 크기·모드 전환 실패·창/렌더 리셋 이벤트 보존 검사를 작성한다 (FR-006/010).
- [ ] T007 [US3] engine.py의 출력 조회·화면 모드·필요 SDL 이벤트·리셋 전달과 좌표 경계를 구현한다. 필요 최소 범위로 main.py와 tests/test_demo.py를 맞추고 기존 Scene API/기본 실행 호출을 보존한다.
- [ ] T008 기존 도형 검사 장면으로 창 크기/전체화면/복귀/최소화·입력 일치를 확인하고 실제/모의 DPI 증거를 구분한다.
- [ ] T009 P2 검사와 README·quickstart.md·docs/architecture.md·docs/progress.md·verification.md의 P2 결과를 갱신한 검증 증분을 커밋한다.

## Phase 4: P3 - 월드 렌더링
- [ ] T010 [US3] tests/test_game_framework.py에 월드 투영/역변환·뎁스/동률·범위/부분 겹침·알파/공유 상태 복원·자원 리셋/실패 검사를 작성한다 (FR-004/005/007~010).
- [ ] T011 [US3] game_framework.py에 카메라 변환·RenderItem·Renderer 월드 경로·월드 전용 LevelScene을 구현하고 framework_demo.py/tests/test_framework_demo.py에 UI 없는 월드 검사를 만든다.
- [ ] T012 월드 자동 검사와 실제 도형/검사용 이미지로 배치·생성/삭제·경계 진입·반투명·레벨 왕복·실패 정리를 확인한다.
- [ ] T013 P3의 docs/architecture.md·docs/progress.md·quickstart.md·verification.md와 필요 계약을 갱신한 검증 증분을 커밋한다.

## Phase 5: P4 - Canvas UI
- [ ] T014 [US3] tests/test_game_framework.py에 Canvas 트리 수명·전체 DFS 스냅샷·형제 순서/하위 트리 연속성·논리 배율/anchor·bounds/숨김·알파 검사를 작성한다 (FR-004/006~010).
- [ ] T015 [US3] game_framework.py의 Canvas·UIElement·Renderer UI 경로와 framework_demo.py/tests/test_framework_demo.py의 게임 규칙 없는 UI 검사 모드를 구현한다.
- [ ] T016 UI 자동 검사와 실제 화면에서 패널/자식 겹침·부모 이동/숨김/삭제·크기/화면비별 기준점/배율·반투명을 확인한다.
- [ ] T017 P4의 docs/architecture.md·docs/progress.md·quickstart.md·verification.md와 필요 계약을 갱신한 검증 증분을 커밋한다.

## Phase 6: P5 - 통합 및 Completion
- [ ] T018 [US2] tests/test_framework_demo.py와 필요한 기존 검사에 Level/Canvas 공동 스냅샷·상호 생성/삭제·복합 초기화/정리 오류·출력 변경 통합 검사를 작성한다 (FR-001~010).
- [ ] T019 [US3] game_framework.py의 LevelScene에 복합 수명/두 스냅샷/두 렌더 패스를 연결하고 framework_demo.py의 통합 화면을 완성한다. 새 기능은 추가하지 않는다.
- [ ] T020 전체 자동 회귀와 실제 통합 화면에서 레벨 왕복·생성/삭제·좌표/입력·UI/월드 겹침·반투명·창/전체화면 전환을 확인하고 필수 실패/미실행을 해결한다 (SC-001/002).
- [ ] T021 README.md·docs/README.md·docs/workflow.md·docs/architecture.md·docs/progress.md와 spec/plan/data-model/contracts/quickstart/verification을 실제 상태에 맞춰 갱신한다 (SC-DOC).
- [ ] T022 문서 링크·git diff --check와 converge 대조로 완료 근거를 확인하고 검증된 통합 증분을 커밋한다. PR은 구체 변경 준비 후 별도 승인 대상으로 둔다.

## Dependencies & Execution Order
권장 P1(T003~005) → P2(T006~009) → P3(T010~013) → P4(T014~017) → P5(T018~022). P1과 P2는 논리적으로 독립이며 P3 이후는 선행 계약을 소비한다. 현재 모든 계획의 구현은 승인됐으며 선행 결과가 필요한 작업만 대기한다. 계획 하나의 범위 승인을 전체 승인으로 확대하지 않는다.

## Parallel execution examples
P1/P2의 독립 읽기 전용 검토는 병행할 수 있다. 실제 동시 구현은 별도 결정 시 작업 폴더/파일을 분리한다. P3/P4/P5의 game_framework.py 동시 쓰기는 하지 않는다.

## Implementation Strategy
각 계획에서 최소 기능·검사·docs를 함께 진행하고 검증된 증분마다 커밋한다. 계획 전체 또는 P5까지 커밋을 미루지 않는다. 계획별 완료와 전체 프레임워크 완료를 구분한다. 승인된 각 계획 범위로 implement·검증·docs 갱신·converge를 진행한다. 선행 계획의 미완료를 건너뛰지 않는다.
