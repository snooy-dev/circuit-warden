# Tasks: 스프라이트 실행 기능

**Input**: spec.md, plan.md, contracts/sprites.md 및 docs/architecture.md
**Implementation authorization**: 2026-11-11 사용자가 이 계획의 구현·중간 커밋을 지시했다. 임시 검사는 미추적이며 직접 확인 전 삭제하지 않는다.

## Phase 1: Design & Documentation Readiness

- [x] T001 specs/009-sprite-runtime의 명세·계획·작업 대응과 docs/progress.md의 구현 권한을 갱신하고 analyze를 수행한다.

## Phase 2: User Story 3 - 이미지 로딩과 수명 (P1)

독립 검사: 같은 경로 한 번 로딩, 실패 캐시 없음, 부분 실패/반복 종료/외부 참조 정리.

- [x] T002 [US3] tests/test_sprites.py와 tests/test_scene_integration.py에 로딩·수명·실패 검사부터 작성한다.
- [x] T003 [US3] sprites.py에 ImageStore/ImageRef를 구현하고 game_framework.py의 LevelScene에 선택적 images 수명을 연결한다. FR-005~007/010.

## Phase 3: User Story 1 - 정지 프레임과 표시 (P1)

독립 검사: 식별 가능한 합성 시트에서 자르기·기준점·반전·투명도·월드/UI 출력 위치.

- [x] T004 [US1] tests/test_sprites.py와 tests/test_world_rendering.py에 source 범위·좌표·상태 복원·기존 호출 검사를 작성한다.
- [x] T005 [US1] sprites.py의 SpriteFrame/draw_sprite와 game_framework.py의 선택적 source/flip_x 경로를 구현한다. FR-001~002/010.
- [x] T006 [US1] 해당 자동 검사를 실행하고 docs/architecture.md·progress.md·009 verification.md에 결과를 반영해 P1을 커밋한다.

## Phase 4: User Story 2 - 독립 애니메이션 재생 (P2)

독립 검사: 가변 프레임 시간, 동일 총 dt, 반복/단발·독립 개체·동작 전환.

- [x] T007 [US2] tests/test_sprites.py에 시간 경계·큰 dt·단발·같은/다른 clip·독립 재생·잘못된 입력 검사를 작성한다.
- [x] T008 [US2] sprites.py에 SpriteClip/SpritePlayer를 구현한다. FR-003~004.
- [x] T009 [US2] 자동 회귀 검사와 독립 코드 검토를 수행하고 docs·009 verification.md를 갱신해 P2를 커밋한다.

## Phase 5: User Story 4 - 미추적 임시 출력 확인 (P3)

독립 검사: 실제 원본을 읽기 전용으로 사용해 재실행 가능한 로컬 화면 제공.

- [x] T010 [US4] 저장소 밖 임시 폴더의 preview.py와 설정을 준비하고 실 시트 원본/생성 목록/해시를 기록한다. FR-008, SC-004. 기본 실행·assets·Git에 반영하지 않는다.
- [x] T011 [US4] 실제 Pico2D에서 월드/UI·프레임/반전/기준점/확대/알파/재생/출력 크기/정리 실패를 확인하고 quickstart.md·verification.md에 실행법과 관찰을 기록한다.
- [x] T012 [US4] 사용자에게 임시 화면 실행법과 검사 결과를 제공하고 직접 확인 대기로 둔다. docs/progress.md와 verification.md 갱신·커밋. 임시 파일 삭제 금지.
- [ ] T013 [US4] 사용자 직접 출력 확인 결과를 받은 뒤 필요한 수정을 반영하고 verification.md에 확인 범위를 기록한다.
- [ ] T014 [US4] 사용자 확인 후 생성 목록의 임시 자료만 제거하고 원본 해시·자동 테스트·미추적 여부를 확인한다. FR-009.

## Phase 6: Documentation & Completion

- [x] T015 spec/plan/tasks/docs/코드·증거를 converge로 대조하고 남은 작업을 기록한다. 사용자 확인·정리 미완료를 완료로 표시하지 않는다.
- [ ] T016 모든 필수 확인 후 docs/progress.md·architecture.md·009 verification.md를 최종 갱신하고 관련 변경을 커밋한다.

## Dependencies & Execution Order

T001 → T002~T006(P1) → T007~T009(P2) → T010~T012(P3 사용자 대기) → 사용자 확인 → T013~T016.
T015의 현재 대응 점검은 대기 전에 수행하되 전체 완료 판정은 T014 후다. 같은 파일을 만지는 P1/P2는 순차 구현한다. 독립 읽기 전용 검토만 병렬로 수행한다. 주 에이전트가 구현·통합·커밋을 책임진다. UI 임시 자료와 영구 자동 테스트를 구분한다.


## Phase 7: Engine Package Integration

- [x] T017 최신 사용자 범위·FR-011·SC-005와 패키지별 담당·검증 계획을 spec/plan에 기록하고 기존 008/009 계약과 대조한다.
- [x] T018 기존 스프라이트 자동 검사를 현재 unit/integration 배치에 옮기고 게임 API·엔진 backend·장면 수명을 통합한다.
- [x] T019 전체 자동 검사와 실제 시트 SDL 출력·원본 불변·정리를 검사하고 docs/009 verification에 실제 결과와 미확인을 기록한다.
- [ ] T020 docs·spec·plan·tasks·코드의 대응을 대조하고 검증된 변경을 feature/engine에 커밋한 뒤 main 대상 PR을 생성한다.

T013/T014/T016의 이전 사용자 확인·임시 정리는 별도 미완료로 보존한다. T020의 PR 생성은 사용자 직접 확인을 완료로 바꾸지 않는다. 게임 브랜치 작업은 T020 뒤에 시작한다.
