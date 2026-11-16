# Tasks: ComfyUI LTX-2.5 연결

**Input**: spec.md, plan.md, docs/tooling.md
**Implementation authorization**: 2026-11-16 사용자 연결 요청.

## Phase 1: Design & Documentation Readiness
- [X] T001 specs/015-comfy-ltx-sprites/spec.md·plan.md를 기준 docs와 대조한다.
- [X] T002 docs/tooling.md·docs/progress.md에 현재 연결 설계를 기록한다.

## Phase 2: User Story 1 - 로컬 생성
- [X] T003 [US1] scripts/comfy-media/workflows/에 고정 원본·API·출처·라이선스를 보관한다. FR-001.
- [X] T004 [US1] scripts/comfy-media/media.py에 입력 준비·서버 점검·영상 생성·결과 계약을 구현한다. FR-002/003/005.
- [X] T005 [US1] tests/test_comfy_media.py에서 그래프 입력·기존 생성기 계약을 검사한다.
- [X] T006 [US1] 실제 서버 점검 후 specs/015-comfy-ltx-sprites/verification.md와 docs를 갱신하고 검증 증분을 커밋한다.

## Phase 3: User Story 2 - 실패와 재개·스킬 연결
- [X] T007 [US2] scripts/comfy-media/media.py의 제출 상태·timeout·재개·출력 보호를 구현하고 tests/test_comfy_media.py로 검사한다. FR-004/005.
- [ ] T008 [US2] scripts/comfy-media/install_skill_route.py와 세 로컬 SKILL.md의 경로 안내를 연결한다. FR-006.
- [ ] T009 [US2] 짧은 로컬 클립·디코딩·기존 sprite_set 계약을 실제 확인한다. FR-007.

## Phase 4: Documentation & Completion
- [ ] T010 docs/tooling.md·docs/progress.md·verification.md에 명령·결과·한계를 반영한다.
- [ ] T011 specs/015-comfy-ltx-sprites와 구현의 대응을 converge로 확인하고 최종 증분을 커밋한다.

## Dependencies & Execution Order
T001→T002→T003→T004/T005→T006→T007/T008→T009→T010→T011.
US1에서 작동하는 최소 경로를 확인하고 US2에서 재개·로컬 설치를 마무리한다. 원본/API 그래프 조사만 서브에이전트에 분리하며 같은 파일의 병렬 쓰기는 없다.
