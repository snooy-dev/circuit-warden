# Tasks: 캐릭터 표시와 좌우 이동 검사

**Input**: spec.md·plan.md·기준 docs
**Implementation authorization**: 사용자 구현 요청·계속 지시, 엔진 PR #2 생성 완료.

## Phase 1: Design & Documentation Readiness

- [x] T001 specs/010-character-movement/spec.md·plan.md·tasks.md와 docs를 analyze로 대조한다.
- [x] T002 docs/progress.md·architecture.md에 현재 범위와 임시 기본값을 반영한다.

## Phase 2: User Story 1 - 게임 에셋 배치 (P1)

- [x] T003 [US1] assets/warden에 PNG 3개를 복사하고 animations.json·README.md와 .gitattributes를 작성한다. FR-001/006.
- [x] T004 [US1] 원본/복사 해시·시트 크기·시간을 검사하고 art-direction·verification을 갱신해 에셋 증분을 커밋한다.

## Phase 3: User Story 2 - 출력과 이동 (P2)

- [x] T005 [US2] tests/unit/test_character.py·tests/integration/test_character_scene.py에 FR-002~005의 입력·시간·전이·정리 검사를 작성한다.
- [x] T006 [US2] game/character.py·game/scene.py·main.py에 표시·입력·이동·전환·경계·포커스 정리를 구현한다.
- [x] T007 [US2] tests/smoke/character_smoke.py로 실제 PNG/SDL 입력·크기 변경·종료를 확인한다.

## Phase 4: Documentation & Completion

- [x] T008 README·docs/README·architecture·art-direction·progress·010 verification을 실제 결과와 맞춘다.
- [x] T009 전체 자동 검사·문서 링크·공백·원본 불변을 검사하고 spec/plan/tasks/코드를 converge로 대조한 뒤 게임 증분을 커밋한다.

## Dependencies & Execution Order

T001→T002→T003→T004(에셋 커밋)→T005/T006→T007→T008→T009. P1 에셋/문서는 주 에이전트, P2 코드/테스트는 Sol(high)이 별도 담당 파일로 병행 가능하다. P2를 커밋하기 전 P1 커밋을 보존한다. 별도 gameplay PR/병합은 이번에 수행하지 않는다.

## Phase 5: Development Preparation

- [x] T010 specs/010-character-movement/spec.md·plan.md에 후속 정리 범위를 명시하고 독립 검토로 삭제/보존 근거를 분석한다. FR-007~010.
- [x] T011 초기 demos/check.py·전용 테스트·중복 display_smoke와 framework_demo.py를 제거하고 필요한 장면은 tests/fixtures로 이동한다. import·patch 호출부를 갱신한다. FR-007/008.
- [x] T012 README·docs/architecture·docs/README·docs/workflow와 quickstart를 main 중심으로 갱신하고 docs/progress에 다음 개발 준비를 기록한다. FR-009/010. AGENTS·constitution·템플릿·overlay의 최소 검사 원칙도 맞춘다.
- [x] T013 이전 자동/실제 smoke 통과 결과를 재사용하고 옮긴 렌더 검사 1개·탐색·게임/에셋 불변·의존성·링크·공백을 확인해 verification에 기록한다. SC-004.
- [x] T014 spec/plan/tasks/docs/코드를 converge로 대조하고 정리 증분을 커밋한다.

T010→T011→T012→T013→T014. 기존 009 사용자 직접 확인/임시 자료 보존 조건과 엔진 PR 상태는 변경하지 않는다.
