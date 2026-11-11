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

## Converge와 한계

구현 후 spec/plan/tasks의 기능 요구 7개·성공 기준 4개·사용자 수용 시나리오 5개·작업 11개와 실제 코드를 대조했다. 입력 소유·명시적 player·의존성·자산 보존·상태 전이·화면·수명·문서·증분 커밋 계획을 충족하며 추가 구현 작업 없음. 통합 전 첫 증분은 c2a5ab3에 보존했다.

전체 회귀·다른 세 smoke는 공통 엔진을 바꾸지 않아 선택하지 않았다. 타이틀 모드·적/피해·콤보·물리·VFX·새 아트는 요청 범위 밖이다. 왼쪽 공격은 수평 반전이며 공격 원본의 알려진 형태 흔들림은 그대로다. idle/Run 이동 경계를 유지하므로 화면 끝에서 검·공격 여백 일부가 잘릴 수 있다. 사용자 직접 확인 전 009 임시 자료를 삭제하지 않는다.
