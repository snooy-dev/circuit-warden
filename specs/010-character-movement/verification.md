# Verification: 캐릭터 표시와 좌우 이동

상태: 표시·이동 구현 및 자동/실제 SDL 검증 완료. 사용자 직접 조작·플레이 품질은 미확인. 엔진 PR #2와 feature/character-movement 분기 완료.

## Analyze

FR-001/006→T003/004, FR-002~005→T005~007, FR-DOC/SC-DOC→T002/008/009. 7개 요구 모두 작업과 연결되며 명세·계획·작업 간 차단 충돌은 없다. 임시 수치와 게임 규칙 미정을 구분했다. 확장 hooks 파일 없음. 최종 미확인: 사용자 직접 조작·플레이 품질. 실제 SDL 자동 입력·화면 관찰은 아래에 기록한다.

## P1 에셋 배치

표준 pathlib/struct/hashlib/json으로 원본과 복사 PNG 3개의 SHA-256 일치, PNG IHDR 크기·셀 개수·프레임 시간·기준점을 확인했다. idle 1024×624=48셀·2000ms, Run 좌/우 각 1024×208=16셀·480ms이며 셀은 모두 128×104다. 게임 이름에 버전이 없고 출처·해시를 assets/warden/README.md에 보존했다. 메타데이터의 제작용 previewSpeed·이벤트는 가져오지 않았다. .gitattributes는 PNG binary이며 LFS/의존성 추가 없음.

architecture·art-direction·progress·docs/README에 검사 범위/게임 복사본과 구현 중 상태를 반영했다. 실제 게임 코드 검증은 다음 증분이며 P1을 게임 동작 완료로 표시하지 않는다.

## P2 표시·이동 검증 (정리 전 결과)

| 명령·검사 | 실제 결과 |
|---|---|
| 구현 전 새 캐릭터 검사 실행 | 예상 실패 2개: game 모듈 없음 |
| 게임 Python -B -m unittest discover -s tests -v (게임 사본 cwd) | 전체 **116개 통과** (기존 106 + 신규 10) |
| runpy로 main·demos.check 진입점 검사, Engine.run 대역 | 각 장면으로 진입하는 호출 확인 |
| 게임 Python -B tests/smoke/character_smoke.py --output-dir 프로젝트 밖 기존 폴더 (실행 시 절대 경로) | 실제 창 검사 종료 0. idle/우Run/반대입력/좌Run/해제/포커스상실/resize/fullscreen/Escape/cleanup PASS |
| character-run-right.png·character-idle-left.png 관찰 | 바닥선의 발 기준점, 전용 Run, 반전 idle, 투명 배경·시트 자르기 관찰 |
| 실제 main.py를 루트 main 작업 폴더에서 절대 경로로 실행 | 게임 창과 idle 출력 확인, art 경로 없이 실행됨 |
| 데스크톱 창 캡처 | 실제 캐릭터 창을 관찰했으나 다른 창이 일부 가림. 이후 전경 활성화는 `foreground window did not report a process id`로 실패해 데스크톱 키 입력 검증 근거로 쓰지 않음 |

smoke의 첫 호출은 출력 폴더가 없어 사전 인자 검사로 종료 2였다. 폴더를 만든 뒤 동일 검사로 통과했으며 런타임 결함이 아니다. 자동 SDL 이벤트와 실제 물리 키 입력·사용자 확인은 서로 다르다. 위 PNG는 실제 SDL 렌더러에서 읽은 출력이며 게임 에셋을 합성한 목업이 아니다.

## 요구사항·문서 대조

- FR-001/006·SC-001: 에셋 증분 baaeb2c. 원본/복사 해시 일치 및 PNG binary 속성의 diff/merge/text unset 확인. 이름·규격·시간·출처 보존.
- FR-002: main 게임 진입, demos.check 별도 진입, __file__ 기준 경로. 실제 PNG 로딩/출력과 장면 재생성 시 새 이미지·실패 후 이미 로딩한 texture 해제를 확인했다.
- FR-003·SC-002: 같은 방향 별칭·반복 입력·상쇄·일부 해제·마지막 방향·분할 dt의 이동량을 검사했다.
- FR-004: 48/16/16프레임, 원본 시간과 pivot·행 우선 영역·전용 좌우 Run·왼쪽 idle 반전·같은 클립 시간 유지·전환 첫 프레임을 검사했다.
- FR-005: 포커스 상실·최소화 유지 키 제거, 경계 clamp, 창 축소·너무 좁은 화면의 중앙 배치를 검사했다. 실제 SDL focus-loss 주입도 통과했다.
- 최종 리뷰에서 boolean pivot이 숫자처럼 나눗셈되는 잘못된 설정 수용을 재현했다. 숫자 타입 검사를 추가하고 회귀 검사에서 설정 파일/클립 오류 문맥과 이미 로딩한 이미지 정리를 확인했다. 전체 116개 통과. 유효 에셋 경로의 동작은 그대로다.
- FR-DOC·SC-DOC: README·docs/README·architecture·art-direction·progress·010 문서를 현재 출력/조작 상태로 갱신한다. game-design/systems는 게임 정책 확정이 없어, tooling/requirements는 환경 변경이 없어 수정하지 않는다.

## Converge와 한계

기능 요구 7개·성공 기준 4개·두 사용자 흐름·계획의 경계/수명/파일 담당·헌법 원칙을 코드와 테스트에 대조했다. 코드의 미구현 차단 항목은 없다. T004 에셋 커밋을 먼저 보존했고 게임 증분에 코드·검사·문서를 함께 담는다. 009의 이전 사용자 직접 확인과 임시 자료 정리 T013/T014/T016은 이번 010 결과로 완료 처리하지 않는다. main/원본 art/원본 main의 미커밋 정책·도구 변경을 보존한다.

최종 게임 이동 속도·미술 품질·사용자 직접 조작은 확정하지 않았다. 좁은 창에서 프레임 전체가 물리적으로 들어가지 않으면 기준점을 중앙에 둔다. 장치 리셋 자동 복구·실물 고DPI/모니터 이동·대량 객체 성능은 범위 밖이다. 게임 PR 생성/병합과 main 병합은 수행하지 않는다.

최종 주 에이전트 검사: 전체 116개 통과, 변경 문서 링크 누락 0개·공백 오류 0개, git diff --no-index --check 오류 출력 없음(변경 존재 종료 1), 원본/복사 PNG 3개 해시 불변. 원본 main 작업 폴더의 변경은 건드리지 않았다.

## 테스트 정리·검사 정책 (현재)

사용자는 작은 기능마다 수십 개 검사를 실행하는 흐름을 중단하고 현재 테스트를 정리하도록 지시했다. FR-007~010을 T010~014와 연결했다. 작은 기능은 직접 동작 확인을 기본으로 하며 복잡한 규칙·재발 버그 등 필요한 경우에만 개별 자동 검사를 선택한다. 전체 회귀·모든 smoke는 상시 완료 조건이 아니다.

| 정리 대상 | 결과·보존 근거 |
|---|---|
| 초기 CheckScene·test_demo·display_smoke·공개 데모 진입점 | 폐기된 데모 검사 3개와 중복 출력 smoke 삭제. 실제 창 출력·입력·최소화는 필요 시 UI/통합 smoke로 검사 |
| test_framework_package와 test_engine_package의 구조 확인 | 일회성 패키지 분리 검사 4개 삭제. 제품 테스트가 공개 API를 실제 사용. 렌더 안정 정렬·오류 전달 1개는 test_render_execution.py로 보존 |
| test_framework_demo 및 중간 이름 test_framework_scenes | 검사용 장면 자체 검사 8개 삭제. 실제 제품 수명·오류 해제는 test_scene_integration/test_game_framework/test_world_rendering이 유지. fixture 고유 조작은 필요 시 실제 smoke가 사용 |
| demos/framework.py | 실제 smoke에 필요한 장면만 tests/fixtures/framework_scenes.py로 이동. 모든 클래스 AST 동일, 공개 CLI 제거 |

현재 자동 검사 수는 **101개**(기존 116에서 15개 삭제)이며 숫자 감소를 위해 서로 다른 제품 회귀 검사를 합치거나 숨기지 않았다.

### 실제 수행과 재사용

검사 Python은 D:/GitHub/circuit-warden/.venv/Scripts/python.exe, cwd는 .local-tools/work/character-movement다.

- fixture 이동 직후 `-B -m unittest discover -s tests -q`: 113개 통과. 추가 12개 삭제와 정책 변경 전 결과이며 101개 전체를 새로 실행했다는 뜻이 아니다.
- 같은 단계에서 `-B tests/smoke/world_smoke.py ../cleanup-preview/world`, ui_smoke.py→../cleanup-preview/ui, integration_smoke.py→../cleanup-preview/integration을 실제 절대 경로 출력 인자로 순차 실행: 모두 종료 0/PASS. 월드 10단계·독립 UI 12단계·통합 16단계의 SDL 출력/입력/수명 assertion 통과. 이후 smoke와 fixture를 바꾸지 않아 결과 재사용.
- 최종 `-B -m unittest tests.unit.test_render_execution -q`: 이동한 검사 **1개 통과**. unittest.defaultTestLoader.discover('tests')로 실행 없이 101개 탐색·import 오류 0 확인.
- pathlib 바이트 대조: 정리 전 사본과 engine/game_framework/game/assets/main.py/character_smoke 동일. character smoke는 재실행하지 않고 P2 결과 재사용. Python AST 파싱·삭제한 demos import 검색 통과.
- 변경 문서 링크 누락 0·공백 오류 0. 활성 main 폴더에는 검사 정책만 덧붙여 다른 세션의 변경을 보존했다. 게임 브랜치에는 이번 정리와 정책만 함께 보존한다.

### 문서 대응·Converge

AGENTS·constitution 3.0.0·workflow·plan/tasks/checklist 템플릿·Spec Kit overlay의 자동 테스트 강제 문구를 제거하고 최소 검사 선택을 일치시켰다. README·tests 안내·architecture·progress·010 실행 안내도 같은 기준이며 001/008 quickstart는 과거 커밋 기록임을 표시했다. 코드·명세·작업과 현재 정책 사이 차단 충돌이 없다. 관련 없는 검사를 실행하지 않았다는 이유로 작업을 미완료 처리하지 않는다.

게임 규칙·런타임·PNG는 변경하지 않았다. 사용자 직접 플레이 품질과 이전 009의 직접 확인/임시 자료 정리는 여전히 미확인이다. 이번 변경은 새 게임플레이 구현·PR 생성/병합을 포함하지 않는다.
