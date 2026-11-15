# Tasks: PNG 효과 재생

**Input**: spec.md·plan.md
**Implementation authorization**: 사용자 PNG 전환·미세 차이 허용·검증/커밋 요청.

## Phase 1: Design & Documentation Readiness

- [x] T001 specs/014-baked-effects의 명세·계획·기준 docs를 대조하고 미세 차이 범위를 해결한다.
- [x] T002 docs/progress.md에 요청 범위와 브랜치 작업을 기록한다.

## Phase 2: User Story 1 - 전하

- [x] T003 [US1] scripts/bake-effects/charge.py와 assets/charge/baked에 재현 가능한 전환 시트를 만든다.
- [x] T004 [US1] game/charge.py·scene.py에서 공유 PNG 선택을 연결하고 게임 NumPy 의존성을 제거한다.
- [x] T005 [US1] tests/integration/test_charge_scene.py·unit/test_charge_teleport.py에서 원본·반전·공유·해제·업로드 부재를 검사한다.
- [x] T006 [US1] docs/architecture.md·tooling.md·verification.md를 갱신하고 검증된 전하 증분을 커밋한다.

## Phase 3: User Story 2 - 전류

- [ ] T007 [US2] scripts/bake-effects/link.mjs·assets/charge/baked에 승인 원본의 길이별12샘플 시트를 만든다.
- [ ] T008 [US2] engine/rendering/drawing.py·game_framework/drawing.py의 회전, game/teleport_link.py·scene.py·mode.py의 공유 재생을 연결한다.
- [ ] T009 [US2] tests/unit/test_teleport_link.py와 그리기 회귀·게임 통합에서 방향·끝점·수명·자원 해제를 확인한다.
- [ ] T010 [US2] tests/performance/charge_benchmark.py의 비교와 tests/smoke/charge_smoke.py 실제 창으로 성능·메모리·모양을 검증한다.

## Phase 4: Documentation & Completion

- [ ] T011 docs/architecture.md·art-direction.md·tooling.md·tests/README.md와 verification.md를 결과에 맞춘다.
- [ ] T012 docs/progress.md·specs/014-baked-effects의 대응을 converge로 확인하고 관련 변경만 커밋한다.

## Dependencies & Execution Order

T001→T002→US1→US2→T011→T012. 원본 읽기 검토만 병렬 위임하며 공유 파일 동시 쓰기 없음. 전하를 독립 검증·커밋한 뒤 전류를 통합한다.
