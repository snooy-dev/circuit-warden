# Tasks: 기본 게임플레이

**Input**: spec.md, plan.md 및 참조 docs
**Implementation authorization**: 사용자 개발 요청·공격 중 정지 답변. PR 제외.

## Phase 1: Design & Documentation Readiness

- [x] T001 입력·재생·모드 감사를 specs/011-basic-gameplay/research.md에 기록하고 spec/plan과 대조한다.
- [x] T002 docs/systems/basic-gameplay.md·game-design.md·progress.md에 요청과 현재 단계를 반영한다.

## Phase 2: User Story 1 - 플레이 모드와 A/D

독립 검사: 레벨 모드에서 A/D 유지·상쇄·해제·포커스 정리를 한 번 처리한다.

- [x] T003 [US1] game/mode.py·scene.py에 GameplayMode와 명시적 player를 연결하고 character.py 입력을 단일 control 경로로 옮긴다.
- [x] T004 [US1] tests/unit/test_character.py·tests/integration/test_character_scene.py·tests/smoke/character_smoke.py의 이동 호출을 A/D와 모드 경로에 맞춰 갱신하고 관련 표적 검사를 실행한다.
- [x] T005 [US1] docs/architecture.md·progress.md와 specs/011-basic-gameplay/verification.md에 결과를 기록하고 첫 증분을 커밋한다.

## Phase 3: User Story 2 - 단발 공격

독립 검사: 양 방향 클릭 공격 중 정지·재클릭 무시·종료 후 유지 키 복귀와 첫 프레임.

- [x] T006 [US2] requirements.txt에 transitions를 추가하고 게임 .venv에 설치, assets/warden/attack.png·animations.json·README.md에 원본 공격을 보존한다.
- [x] T007 [US2] tests/unit/test_character.py와 tests/integration/test_character_scene.py에 공격 중 키 변경·재클릭·종료·loop 오류/자원 해제 검사를 추가한다.
- [x] T008 [US2] game/character.py에 단발 로더와 idle/run/attack 전이·방향 고정·종료 복귀를 구현한다.
- [x] T009 [US2] tests/smoke/character_smoke.py로 실제 양 방향 공격·복귀·접지를 캡처하고 표적 검사 결과를 specs/011-basic-gameplay/verification.md에 기록한다.

## Phase 4: Documentation & Completion

- [x] T010 README.md·tests/README.md·docs/architecture.md·game-design.md·art-direction.md·systems/basic-gameplay.md·progress.md를 최종 구현과 맞춘다.
- [x] T011 specs/011-basic-gameplay/verification.md에 요구별 증거·미확인·docs 영향을 기록하고 링크·공백·converge 대조 후 두 번째 증분을 커밋한다.

## Dependencies & Execution Order

T001→T002→T003→T004→T005가 첫 플레이 가능한 증분이다. T006→T007→T008→T009→T010→T011이 공격 증분이다. 주 에이전트만 쓰므로 파일 경합 없음. 독립 감사는 읽기 전용 서브에이전트가 수행한다. US1/US2 구현은 공통 파일이므로 순차 실행하고, 소스 검토와 문서/에셋 읽기만 병렬 가능하다.
