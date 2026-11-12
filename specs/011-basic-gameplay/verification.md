# Verification: 기본 게임플레이

상태: 요청 범위 구현·검증 완료. 사용자 직접 조작감·미술 품질은 미확인. feature/basic-gameplay에 로컬 증분 커밋, 원격 게시/병합 없음.

## Analyze

FR-001→T001, FR-002/003→T003/004, FR-004/005→T006~009, FR-006→T007/008, FR-DOC→T002/005/010/011. 기능 요구 7개·두 흐름·성공 기준 4개·헌법 대조에서 차단 충돌/누락 없음. requirements checklist 7개 충족. 확장 hooks 파일 없음. 별도 계획 승인으로 표시하지 않았다.

## 실제 검증

모든 Python 명령은 프로젝트 루트에서 게임 `.venv/Scripts/python.exe`를 사용했다.

| 명령·검사 | 결과 |
|---|---|
| `-B -m unittest tests.unit.test_character tests.integration.test_character_scene.CharacterSceneTests.test_gameplay_mode_delivers_once_and_keeps_player_reference -v` | US1 시점 7개 통과. A/D 이동·상쇄·해제·시간·포커스·경계·단일 전달·player 참조 확인 |
| `-B -m unittest tests.unit.test_character tests.integration.test_character_scene -q` | 공격 구현 후 15개 통과. 공격 진입 첫 프레임, 재클릭, 키 변경/해제/상쇄/포커스, 종료 복귀, 실제 PNG·잘못된 loop·수명 검증 |
| `-B tests/smoke/character_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/11/01a1cac2-b470-7663-9b16-80b99460d51f` | 실제 SDL 창 종료 0/PASS. idle·좌우 Run·양 방향 공격·이동 재개·해제·focus-loss·resize·fullscreen·Escape·이미지/장면 정리 |
| `-B -m unittest tests.unit.test_character.CharacterTests.test_attack_starts_at_first_frame_ignores_clicks_and_resumes_held_key -q` | 최종 중복 조건 제거 후 해당 전이 1개 통과. 동작 등가 변경으로 이전 PNG/SDL 결과 재사용 |
| `-m pip check` | 의존성 충돌 없음. transitions 0.9.3, 전이 의존성 six 1.17.0 설치 |
| pathlib/hashlib/struct 원본 대조 | attack.png와 원본 SHA-256 일치, 1344×192·7셀, 원본 시간·root 보존 |
| 변경 Markdown 로컬 파일 링크 검사·`git diff --check` | 누락 0·공백 오류 0 |

구현 전 공격 검사 1개는 state 부재로 예상 실패했다. 구현 중 transitions에 tuple 형식 전이표를 넣어 생성 오류를 확인했고 지원되는 list 형식으로 수정한 뒤 위 15개가 통과했다. 최초 pip 설치는 sandbox DNS 제한으로 실패했고 허용된 권한 상승 설치로 성공했다. 실패를 통과로 포함하지 않았다.

읽기 전용 독립 감사는 기존 이벤트/재생 표적 9개 통과를 보고했다. 최종 독립 리뷰에서는 실제 asset+SDL 소프트웨어 렌더러의 7프레임 순차 재생·종료 직전 클릭·경계/창 축소·무효 출력 복귀를 확인했고 진행 차단 결함은 없었다. 주 검증 수 15개와 합산하지 않는다.

## 화면 관찰

위 출력 폴더의 character-idle.png, character-attack-first-right.png, character-attack-first-left.png, character-attack-right.png를 직접 열었다. 첫 프레임·양 방향 반전·바닥 접점과 투명 배경/시트 자르기를 확인했다. 공격은 몸을 숙여 idle과 실루엣이 다르지만 셀 크기 차이로 전체를 강제 축소하지 않았다. 공격 후반 검은 바닥선 아래로 내려가는 원본 동작이다. 실제 PNG 렌더 캡처이며 목업이 아니다.

자동 SDL 이벤트와 사람의 키·마우스 조작은 구분한다. 사용자 직접 플레이·애니메이션 매끄러움/해부학적 손 표현의 최종 승인은 미확인이다.

## 요구사항·문서 대응

- FR-001: research의 입력/재생 지원·부족 기능·전달 순서 감사. engine/game_framework 변경 없음.
- FR-002/003·SC-001: GameplayLevel/GameplayMode→Character.control 단일 경로, 명시적 player, A/D·상쇄·해제·경계·포커스.
- FR-004/005·SC-002/003: transitions idle/run/attack, SpritePlayer 단발, 공격 중 위치·방향 고정/재클릭 무시/키 상태 갱신, 완료 후 이동 상태 선택. 종료 갱신의 이동 dt 중복 없음.
- FR-006: bool loop 및 클립 정책 검증, 진입 실패·종료 이미지 정리. 게임은 assets만 사용하며 원본 art에 의존하지 않는다.
- FR-DOC·SC-DOC: README·docs/README·game-design·systems·architecture·art-direction·progress·assets README·tests README·011 문서를 현 구현과 대조했다. constitution/workflow/tooling은 정책·도구 환경 변화가 없어 영향 없음. 과거 009/010 검증 근거 보존.

## 초기 구현 Converge와 한계

구현 후 spec/plan/tasks의 기능 요구 7개·성공 기준 4개·사용자 수용 시나리오 5개·작업 11개와 실제 코드를 대조했다. 입력 소유·명시적 player·의존성·자산 보존·상태 전이·화면·수명·문서·증분 커밋 계획을 충족하며 추가 구현 작업 없음. 통합 전 첫 증분은 c2a5ab3에 보존했다.

전체 회귀·다른 세 smoke는 공통 엔진을 바꾸지 않아 선택하지 않았다. 초기 구현 당시 타이틀 모드·적/피해·콤보·물리·VFX·새 아트는 범위 밖이었다. 베기 VFX는 아래 후속 요청으로 포함했다. 왼쪽 공격은 수평 반전이며 공격 원본의 알려진 형태 흔들림은 그대로다. idle/Run 이동 경계를 유지하므로 화면 끝에서 검·공격 여백 일부가 잘릴 수 있다. 사용자 직접 확인 전 009 임시 자료를 삭제하지 않는다.

## 후속 증분: 720p·아웃라인 공격·베기 VFX

사용자 후속 요청으로 FR-007/008·SC-004와 US3를 명세·계획·T012~016에 연결하고 analyze 대조했다. 추가 요구 2개 모두 작업/검증에 대응, 충돌 없음. 기존 제외 범위 중 베기 VFX만 이번 요청으로 대체했다. 시작 시 작업 트리는 깨끗했으며 기존 구현/아트 기록은 이미 커밋됐다. `git fetch origin` 후 `git merge --no-commit origin/main`: Already up to date.

게임 기본 창은 game/scene.py에서 Engine(1280,720)으로 지정한다. 공통 엔진 기본값과 논리 높이 600은 보존한다. attack.png는 v6 아웃라인 있음 원본으로 교체했고 전기 베기 v4를 복사했다. 사용자 후속 지시에 따라 pixelfx 라이선스는 licenses/pixelfx-LICENSE.txt에서 공통 관리한다. 원본 파일은 수정하지 않았다. 공통 라이선스·고지를 보존하며 게임·자산 README에는 별도 제작 도구 사용 문구를 두지 않는다. 새 라이브러리 설치·이미지 생성 없음.

### 선택한 검증과 실제 결과

게임 `.venv/Scripts/python.exe`로 아래 4개를 한 번 실행해 모두 통과했다(`-B -m unittest <아래 메서드 4개> -v`).

- `tests.integration.test_character_scene.CharacterSceneTests.test_sword_trails_keep_attack_position_and_expire_independently`: 효과 생성 0초·14×50ms·뒤쪽 레이어·좌측 반전·공격 후 이동과 방향 변화에도 위치/방향 고정·후속 효과 공존·700ms 개별 제거·장면 종료 시 이미지 해제.
- `tests.integration.test_character_scene.CharacterSceneTests.test_real_asset_draw_and_fresh_scene_lifetime`: 실제 새 PNG 로딩·출력·장면 이미지 수명.
- `tests.integration.test_character_scene.CharacterSceneTests.test_window_commands_and_resize_bounds`: 변경한 기본 창의 F6/F11·경계 보정.
- `tests.unit.test_character.CharacterTests.test_attack_starts_at_first_frame_ignores_clicks_and_resumes_held_key`: 기존 공격 정지·첫 프레임·유지 키 복귀 보존.

`-B tests/smoke/character_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/11/01a1cac2-b470-7663-9b16-80b99460d51f/720p-trail` → 종료 0/PASS. 실제 창 1280×720, 좌우 공격·잔상 잔존/소멸, focus-loss·F6/F11·Escape·자원 정리 확인.

위 폴더의 character-attack-left.png·character-attack-right.png·character-attack-resume-right.png를 열어 양 방향 외곽선 공격·캐릭터 뒤 전기 베기·이동 후 남은 잔상을 관찰했다. 출력 1280×720을 확인했으며 아트 목업이 아닌 실제 SDL 렌더 캡처다.

pathlib/hashlib/struct 대조로 공격 원본/복사 SHA-256 `e7a9a24a46feff5d20ffb20f032b57b9bbd67754c0263e8f5fb162458b7891e6`, 베기 `379ebfc70867974cdb0afdf4b37bb5c5a5f5ccd931479d04857f887f1d48dc30` 일치. 셀 192², 공격 7열·350ms/베기 14열·700ms, 기준점 (96,120) 보존. 공통 pixelfx 라이선스는 원본 CREDITS의 MIT License 절과 텍스트 일치. 에셋별 라이선스 사본·제작 도구 사용 문구 없음. 문서만 정리했으므로 게임 검사는 재실행하지 않고 위 결과를 재사용한다. 변경 Markdown 로컬 링크 누락 0, `git diff --check` 통과.

### 최종 문서 대응·Converge

FR-007→DEFAULT_SIZE/실제 창, FR-008→SwordTrail/독립 수명·합성·자산, SC-004→해시·창 캡처·표적 검사. spec/plan/tasks의 총 9개 기능 요구·5개 성공 기준·16개 작업을 대조해 미구현 필수 항목 없음. 후속 변경은 docs/architecture·systems/basic-gameplay·art-direction·progress·README·assets 출처 및 011 문서에 반영했다. 게임 규칙 본체와 기존 350ms 공격 잠금은 유지한다.

원본 베기는 검끝을 추종하지 않는 고정 호이고 v6에서도 이를 보존했다. 왼쪽은 수평 반전, 화면 가장자리에서는 효과 일부가 잘릴 수 있다. 전체 회귀·다른 smoke는 공통 엔진 변경이 없어 선택하지 않았다. 사용자 직접 조작·최종 미술 품질, 피해 판정·새 아트 제작은 이번 검증/구현 범위 밖이다.

## 표시 배율 1배 (2026-11-13)

사용자 요청 FR-009/SC-005→T017/T018 대조, 충돌 없음. 기존 브랜치 fetch·merge 결과 Already up to date. DISPLAY_SCALE=1을 기존 출력·이동 경계·효과 생성이 공유한다. 기본 창의 최종 배율은 720/600=1.2: idle/Run 셀 153.6×124.8px, 공격/베기 셀 230.4×230.4px(투명 여백 포함). 이동 속도·시간·원본 PNG는 변경하지 않았다.

게임 Python으로 `-B -m unittest tests.unit.test_character.CharacterTests.test_bounds_include_idle_and_run_extents_and_center_when_narrow tests.unit.test_character.CharacterTests.test_draw_flips_idle_left_and_uses_dedicated_run_frames -q` 실행: 2개 통과.
`-B tests/smoke/character_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/11/01a1cac2-b470-7663-9b16-80b99460d51f/scale-1` 실행: 종료 0/PASS. 실제 출력 character-idle.png·character-attack-right.png를 열어 축소 크기·발 접점·베기 정렬을 확인했다.

architecture·progress·spec/plan/tasks와 코드의 현재 배율을 대조했고 Converge에서 추가 필수 작업 없음. 변경 문서 파일 링크·git diff --check 통과. 루트 README는 수정하지 않았다. 단순 배율 변경으로 전체 회귀는 생략했고 사용자 직접 크기 평가는 미확인이다.

## 점프 (2026-11-13)

사용자 요청 FR-010~012·SC-006→US4/T019~022. Space·상승 0.4초·공중 A/D·동시 점프 우선은 기술 기본안, 키3배·제자리/달리기·idle/Run 재사용·공중 공격 제외는 사용자 결정으로 구분했다. analyze 대조에서 누락·충돌 없음. 기존 브랜치 fetch 후 origin/main merge: Already up to date.

### 높이와 선택한 검사

도구 Python `.local-tools/python/Scripts/python.exe`의 기존 Pillow로 assets/warden/idle.png를 128×104셀 48개로 읽어 알파 bbox 측정: 첫 프레임 (24,11,78,93), 높이 81~83, 전체 y 범위 [10,93). 런타임 의존성/PNG를 변경하지 않았다. 높이83×현재배율1×3=249, 기본 창에서 298.8 출력픽셀이다.

게임 `.venv/Scripts/python.exe -B -m unittest`에 아래 메서드 5개를 지정했다. 정점·시간분할·입력 경계 위험에만 표적 검사를 선택했다.

- `tests.unit.test_character.CharacterTests.test_jump_reaches_three_body_heights_and_lands_with_split_time`: 정점249, .4초와 40분할 동일, .8초 정확한 바닥 착지, 유지 키 재점프 방지·다시 누르기·큰 dt 착지.
- `tests.unit.test_character.CharacterTests.test_running_jump_steers_and_draws_at_airborne_position`: 달리기 점프·공중 방향 변경·해제/idle·실제 y 출력.
- `tests.unit.test_character.CharacterTests.test_airborne_inputs_are_not_buffered_and_attack_blocks_jump`: 동시 점프 우선, 공중 클릭/재점프 무시와 예약 없음, 지상 공격 중 점프 차단.
- `tests.unit.test_character.CharacterTests.test_focus_loss_clears_pending_jump_but_airborne_character_lands`: 포커스 미시작 요청 정리, 무효 출력 신규점프 차단, 비행은 유지키 없이 착지.
- `tests.unit.test_character.CharacterTests.test_attack_starts_at_first_frame_ignores_clicks_and_resumes_held_key`: 지상 공격 기존 전이 회귀.

최초 실행은 4개 통과·1개 실패. 테스트의 합성 공격이 100ms인데 정확히 100ms 뒤에도 attack을 기대한 검사 오류였다. 공격 중 검사 시점을 50ms로 수정하고 해당 메서드만 재실행해 통과했다. 제품 코드는 바꾸지 않았고 나머지 4개의 결과를 재사용한다. 최종 선택 5개 모두 충족.

`-B tests/smoke/character_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/11/01a1cac2-b470-7663-9b16-80b99460d51f/jump` → 종료 0/PASS. 실제 SDL 입력 경로에서 제자리/달리기 점프·공중 방향 전환·클릭 차단·착지, 기존 공격·focus·창 크기/전체화면·종료 정리 확인. character-jump-idle.png·character-jump-run-right.png·character-jump-landed.png를 열어 기존 클립의 공중 표시와 바닥 복귀 관찰. 사람의 직접 플레이 체감과 구분한다.

### 문서 영향·한계

game-design·systems/basic-gameplay·architecture·progress 및 011 spec/plan/tasks/data-model/quickstart를 현 동작과 대조했다. engine/game_framework·이미지·루트 README는 변경 없음. 전체 회귀·다른 smoke는 공통 엔진 변경이 없어 선택하지 않았다. 점프 전용 모션·공중 공격·플랫폼 충돌·가변 높이·코요테 타임은 추가하지 않는다. 상승/체공 시간의 사용자 직접 감각은 미확인이다.

독립 읽기 전용 리뷰에서도 진행 차단 결함 없음. 입력 두 순서×초기 dt 0/.1, 착지 직전 예약 차단, 최대100ms의 200개 시간 분할에서 정점/착지를 확인했다. 주 검증 5개에 합산하지 않는다. Converge에서 이번 FR-010~012·SC-006·US4 수용 시나리오3개·T019~022를 실제 코드/검증과 대조해 추가 필수 작업 없음. 변경 Markdown 파일 링크·git diff --check 통과.

## 점프 높이 수치 조정

2026-11-13 사용자 요청으로 높이 배수를 3→2로 변경했다(83×2=166 월드 단위). 상승 0.4초·전체 체공 약 0.8초는 유지한다. 관련 현재 문서와 기존 테스트의 배수 기대값·이름을 맞췄다. 사용자 지시로 테스트·실제 창 검사는 실행하지 않았다. 위 점프 검증은 변경 전 3배 결과이며 새 높이의 실행 검증으로 취급하지 않는다.

## 측면 idle 교체 (2026-11-13)

FR-013/SC-007→T023/T024를 원본·설계·구현·검증에 대조했다. 기존 브랜치 fetch/merge는 Already up to date. 오른쪽 시트를 idle.png에 바이트 보존 복사했고 pivot만 (58,92)→(64,92)로 변경했다. 좌우 48개 셀의 RGBA 수평 반전 일치, 1024×624 시트·128×104 셀·48프레임·2000ms를 확인했다. SHA-256은 `6cd0b5133576e6f73cb492a0f36e114c160371c33115bda0272d877f7735d506`. 알파 높이는 81~83px로 동일하여 점프 높이166을 유지한다. 좌측 원본의 픽셀 인덱스 anchor63 대신 기존 연속 좌표 pivot64 반전을 사용한다. 새 상태/로더/의존성은 없다.

- `.venv/Scripts/python.exe -B -m unittest tests.integration.test_character_scene.CharacterSceneTests.test_real_asset_draw_and_fresh_scene_lifetime -v`: 1개 통과. 실제 PNG·시간·새 pivot·렌더·장면 수명 확인.
- `.venv/Scripts/python.exe -B tests/smoke/character_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/11/01a1cac2-b470-7663-9b16-80b99460d51f/side-idle`: 종료0/PASS. 이동·공격·복귀·제자리/달리기 점프·착지·창 전환·정리 확인.
- 해당 폴더의 character-idle.png와 character-idle-left.png를 열어 새 측면 모습·좌우 방향·바닥 정렬을 관찰했다. 사용자 직접 플레이/최종 아트 품질 평가와 구분한다.

assets 출처, docs/art-direction·architecture·progress 및 011 spec/plan/tasks를 현재 통합 상태에 맞췄다. 원본 아트·루트 README는 보존했다. Converge 대조에서 추가 필수 작업 없음. 변경 문서 링크와 git diff --check 확인. 전체 회귀는 자산/pivot 교체 범위를 넘어 실행하지 않았다.
