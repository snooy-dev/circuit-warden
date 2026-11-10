# 검증 상태: 게임프레임워크

**현재 실행 근거**: 2026-11-10 사용자가 P1~P5의 새 채팅 구현과 독립 계획의 별도 워크트리 병렬 작업을 지시했다. 이전 구현 보류는 해제됐다. 상세 기술 선택과 사용자 게임 정책 확정은 구분한다.

**상태**: P1/P2 검증 커밋 통합·P3 구현 및 자동/실제 SDL 검증 완료. 전체 프레임워크 완료 아님.
**P1 브랜치**: `feature/gameplay-core`
**기준 커밋**: `1940dd423daf423a84637b9ccec7d23eb92d722f`
**P1 구현 커밋**: `d3c4ed06f2efa199c41a15f525b161d9e894f7b3` (코드·검사·docs·명세·검증 포함). 후속 인계 문서 커밋까지 포함한 `feature/gameplay-core` 브랜치를 통합하면 된다.

## 계획별 상태

| 계획 | 이 작업트리의 상태 | 실제 근거 / 다음 단계 |
|---|---|---|
| P1 객체·규칙 | 구현·자동 검증 완료 | 새 core 검사 16개 + 기존 16개 통과. FR-001~004의 월드 소유·규칙·전달 수명 담당 범위 충족 |
| P2 창·출력 | 검증 커밋 통합 | 별도 27개 자동·실제 SDL 검증 근거 보존 |
| P3 월드 렌더링 | 구현·자동/실제 SDL 검증 완료 | 전체 60개와 아래 실제 창 검사 통과 |
| P4 Canvas UI | 선행 결과 대기 | P3 후 구현 |
| P5 통합 | 선행 결과 대기 | P1~P4 후 SC-001/002/DOC 전체 판정 |

## 실제 명령과 결과

전용 작업트리 `C:/Users/Developer/.codex/worktrees/0ff6/circuit-warden`에서 실행했다.

| 명령 | 결과 |
|---|---|
| `git status --short`, `git cat-file -t 1940dd423daf423a84637b9ccec7d23eb92d722f` | 시작 시 깨끗한 작업트리·기준 commit 확인 |
| `git switch -c feature/gameplay-core 1940dd423daf423a84637b9ccec7d23eb92d722f` | 전용 브랜치 생성. 최초 제한된 Git 관리 경로 쓰기는 거부됐고 승인된 확장 실행으로 성공 |
| `$env:SPECIFY_FEATURE_DIRECTORY=(Resolve-Path specs/008-game-framework).Path; ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` | 성공. 최초 SPECIFY_FEATURE만 지정한 시도는 디렉터리 미해결로 실패했고 명시 디렉터리로 해결 |
| `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest discover -s tests -v` | 32개 통과: P1 16개, 기존 엔진·데모 16개 |
| `git diff --check` | 통과 |
| 게임 Python 표준입력 pathlib/re 검사: 변경 Markdown의 로컬 링크 대상·줄 끝 공백 | 11개 문서 통과 |

## 요구사항·검사 대응과 인계 API

- FR-001/002: Level별 GameMode 격리, 초기 배치→모드 시작, 등록순 dict·ID 조회·증가 ID, 단일 소유·재등록 금지, 동일성 기반 제거와 반복 제거, 재열기 시 새 배치.
- FR-003: 이벤트/update 시작 스냅샷, 모드→등록순 객체, 모드/객체의 생성·자기/다른 객체 제거, 다음 전달 참여, 교차 재진입 거부, 오류 후 가드 복구.
- FR-004 담당 범위: 실패한 spawn 소유 해제·한 번 정리, 실패 객체 재사용 거부, 초기 배치/모드 시작 실패의 전체 정리, 복수 오류 보존, 닫는 중 등록/재열기 거부, 닫기 중 일부 오류에도 전체 정리 시도, 전달 종료/실패 후 제거 객체 참조 해제.
- `Level(mode=None)`, `Level.on_open()`, `open()/close()`, `spawn(obj)`, `get(id)`, 읽기 전용 `objects/mode`를 제공한다. `objects`는 등록순 tuple이며 순회 자체의 소유 변경은 하지 않는다.
- `GameObject.level/id`, `on_spawn/on_destroy/handle_event/update`, `destroy()`와 `GameMode.level`, `on_start/on_event/on_update/on_end`를 제공한다. 위치·게임 상태는 구체 객체가 가진다.
- 모드는 Level 생성 때 연결되며 다른 Level에서 공유·재사용하지 않는다. 닫힌 Level의 입력/update는 무시한다. `on_open` 뒤 `on_start`, 열기 실패에도 `on_end`를 시도한다. 단일 오류는 그대로, 복수 오류는 BaseExceptionGroup으로 전달한다.
- P5 공동 스냅샷 API는 아직 없다. 현재 `Level.update()`가 내부 스냅샷을 취득한다. P5가 Canvas 결합 시 담당 계약을 확장한다.

## 문서 갱신·analyze·converge

P1 계획·T003~T005·spec/plan/data-model/contracts/quickstart와 docs/architecture·progress·README를 실제 API·검증 상태에 맞췄다. 공통 문서의 이전 구현 보류 문장을 최신 지시로 정리하되 다른 계획의 구현 완료를 주장하지 않았다. architecture는 목표 설계와 P1 구현을 구분하며 이전 링크 앵커를 보존했다.

analyze에서 P1은 렌더/Canvas/SDL 없이 FR-001~004의 담당 범위를 구현할 수 있음을 확인했다. 구체 승패·업데이트 후 판정은 제외다. 테스트 초안은 예전 GameMode 소유 모델이므로 복사하지 않고 현재 Level 계약으로 새 검사를 작성했다. 독립 읽기 전용 Luna/high 검토에서 재현 가능한 P1 결함은 없었으며 core 16개를 별도로 통과했다. 지적된 모드 시작 중 닫기 검사 공백을 보완하고 전체 32개를 다시 통과했다. converge에서 P1 요구사항·실제 API·검사·문서 대응과 제외 범위를 대조했고 P1 필수 미완료는 없다. 기존 engine.py/main.py/requirements.txt와 원본 작업 폴더는 변경하지 않았다. systems·game-design·art-direction은 게임 규칙·아트를 변경하지 않아 영향 없다. 외부 서비스·생성·새 의존성·PR 없음.

## 미실행·한계

P1은 창 없는 core 계획이므로 새 실제 창·UI 자동 조작·사용자 직접 확인은 수행하지 않았다. P2~P5의 실제 출력·렌더·Canvas·복합 장면 검증을 대체하지 않는다. 실제 게임 규모·성능 예산은 미정이며 새 성능 주장을 하지 않는다. 오류 traceback이나 외부 변수가 잡고 있는 참조의 즉시 메모리 해제는 보장하지 않는다.


## P2 통합과 검증 근거


- 기준 커밋: `1940dd423daf423a84637b9ccec7d23eb92d722f`, 브랜치: `feature/display-management`.
- 명령: `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest discover -s tests -v`
- 결과: **27개 통과**, 기존 16개 회귀 포함. 모의 SDL로 window/output/viewport, 2배 DPI 좌표·휠 제외, 최소화/0 크기 update·종료 유지, 프레임 중 크기 변경 표시 생략, 리셋 이벤트/누적 세대, 전환 지연·실패 정리·창 크기 복귀를 검사했다. 실제 ctypes SDL_Event를 채워 창/마우스/키 반복 필터/두 종류 리셋 전달과 출력 조회 오류도 검사했다.
- 실제 SDL 명령: `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe tests/display_smoke.py C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c41a-3137-7f90-9330-4a9370e0b7ce`
- 결과: 종료 0, `PASS: resize/fullscreen/restore/minimize/mouse/render`. 640×480 → 960×540 → 1536×864 보더리스 → 960×540 복귀를 실제 window/output 조회와 assert로 확인했다. 최소화 상태 output_valid=False, draw 수 불변, 복구 후 SDL_WarpMouseInWindow에서 실제 이동 이벤트를 받아 출력 좌표 일치까지 확인했다. SDL_RenderReadPixels/IMG_SavePNG로 저장한 p2-stage-1/2/3/6.png를 직접 열어 도형·출력 경계·마우스 표시를 관찰했다. 자원 생성/이미지 복구는 P3 범위다.
- 자동 UI 도구로 main.py의 기본 창·도형을 관찰했다. F6 자동 키 입력 뒤 크기 변화는 확인하지 못했고 원인을 단정하지 않는다. 이후 실제 SDL 검사는 위 별도 스크립트에서 앱 내부 API로 수행했다. 사용자 직접 확인은 받지 않았다.
- 실제 window/output 비율은 1:1이었다. 모의 2배 DPI는 자동 검사로 통과했으나 실물 DPI 배율 변경·다른 모니터 이동·직접 키 조작/테두리 드래그는 미확인이다. 이 한계를 실물 검증 성공으로 표시하지 않는다.
- 정적 검증: `git diff --check` 통과, 변경된 Markdown 13개의 로컬 파일 링크 대상 존재 검사 통과. 최종 자동 검사 27개와 실제 SDL 검사도 재실행하여 모두 통과했다.


P2 구현 커밋 `6c92565bfe726d50458f1e6eeca64494258073f4`, 최종 인계 커밋 `c3eef90`을 Git merge했다. 이전 커밋 차단은 해결됐다. P1 최종 인계 `d23d1dbf0f990d260b72ce5e270fa20c9da9eb1b`도 포함한다.

## P3 검증과 인계

- 작업트리: `C:/Users/Developer/.codex/worktrees/cbb2/circuit-warden`, 브랜치: `feature/world-rendering`.
- P1 최종 `d23d1dbf0f990d260b72ce5e270fa20c9da9eb1b`, P2 최종 `c3eef90`을 Git merge했다. 통합 커밋 `e229bf2`에서 전체 43개 회귀를 통과했다. P3 월드 기본 경로 증분 `4a4426a`는 전체 55개를 통과했다. 최종 구현·검증 커밋: `76e9863cab36fa8e8c0e3db751b26f52b4ded53d`. 이 커밋의 코드·검사·docs와 후속 인계 문서 커밋을 포함한 같은 브랜치를 P4가 그대로 이어간다.
- 자동 명령: `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest discover -s tests -q` → **60개 통과**. 기존·P1/P2 43개와 P3 17개다. `tests/test_world_rendering.py`는 좌표 왕복/길이/화면비/0크기, 등록순/이미지별 안정 정렬/동률 복원, 부분·경계·1픽셀 여유·미확인 bounds와 update 유지, 렌더 중 수명/전달 재진입 거부, 실패 뒤 참조 해제, 리셋 명시 실패와 정리를 검사한다. `tests/test_framework_demo.py`는 클릭→update 단일 이동→draw 상태 불변, 레벨 왕복·규칙 격리, 카메라·뎁스·출력 요청을 검사한다.
- 실제 SDL 소프트웨어 렌더러 검사: 메모리 surface/texture와 `SDL_RenderReadPixels`로 source-over RGB, 이미지 자체 alpha×opacity, 공유 texture의 다른 opacity, texture/도형 draw 및 상태 설정 실패 뒤 원래 color/blend/alpha 복원을 확인했다. TARGET texture는 내용 복구 경로가 없어 명시 오류로 거부한다.
- 실제 창 명령: `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe tests/world_smoke.py C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c41a-a29f-77a0-905b-a7e7ea69059f` → 종료 0, `PASS: world/alpha/image/culling/input/camera/resize/fullscreen/roundtrip`. 실제 640×480 → 960×540 → 5120×1440 보더리스 → 960×540 복귀를 확인했다. SDL 입력 큐로 생성·삭제·카메라·A→B→A를 실행하고 레벨별 새 초기 배치·이전 소유 해제·마지막 장면/renderer 참조 정리를 assert했다. 2×2 RGBA 검사용 texture를 메모리에서 만들어 실제 이미지 합성 픽셀을 확인하고 각 레벨 종료 때 해제했다. 외부 에셋 생성은 없다.
- 실제 출력 `p3-initial.png`, `p3-boundary-entry.png`, `p3-resized.png`, `p3-level-B.png`를 위 출력 폴더에서 직접 열어 보았다. 중심이 밖인 보라색 도형의 부분 표시, 빨간 몸/파란 반투명/노란 무기 교차 순서, 화면 밖 초록 도형의 경계 진입, 카메라 이동 후 저장 좌표 유지와 크기/화면비 투영을 확인했다. 이미지 합성 기대값은 Pico2D의 실제 기본 배경색(200,200,210)을 기준으로 한다.
- 일반 `framework_demo.py` 창에서도 도형·움직임을 관찰했다. 자동 UI Space 입력은 전환을 확인하지 못했고 이후 마우스 자동 조작은 사용자 입력 감지로 중단됐다. 원인을 앱/도구 문제로 단정하지 않는다. 별도 실제 SDL 입력 큐 검사를 이 자동 UI 입력 성공이나 사용자 직접 확인으로 표시하지 않는다. 일반 관찰 창은 실행 세션 중단으로 닫았고 실제 smoke는 자체 종료·정리를 검사했다. 사용자 직접 확인·실물 DPI 변경·물리 키 조작은 미확인이다.

### 리셋 처리·검토·converge

실제 resize에서 TARGETS_RESET이 발생해 모든 리셋 오류 정책이 크기 변경을 막는 것을 확인했다. [SDL2 이벤트 정의](https://wiki.libsdl.org/SDL2/SDL_EventType)에 따라 타깃 리셋은 일반 도형/정적 이미지 재그리기를 허용하고 장치 리셋은 명시 오류로 종료한다. 원래 계획의 ‘복구 또는 명시 오류’ 안에서 처리하며 실패를 성공으로 바꾸지 않았다. TARGET texture는 그리기 전에 명시 오류로 거부한다. 전달받은 타깃 이벤트마다 세대를 하나만 올려 누락 device 후 후속 target이 누락을 덮지 못하도록 했다. 해당 재현 회귀를 추가해 전체 60개와 실제 창 검사를 다시 통과했다.

Luna/high 계약 준비 검토와 Sol/high 읽기 전용 코드 검토를 수행했다. Sol 검토에서 제시한 누락 세대 경계를 보완했고 SDL 설정 실패 4개 경계도 지속 자동 검사에 포함했다. analyze/converge에서 FR-004/005/007~010의 월드 담당 범위·실제 API·검사·docs를 대조했다. T010~T013의 필수 미완료는 없다. 전체 UI/통합 SC 판정은 P4/P5에 남아 있으며 이번 완료는 P3 범위다.

architecture/progress/README와 spec/plan/P3 plan/tasks/data-model/contracts/quickstart를 현재 API·실행·한계로 갱신했다. 게임 정책·아트·의존성을 바꾸지 않아 game-design/systems/art-direction과 requirements에는 영향이 없다. Pico2D 설치본·원본 D:/GitHub 작업·다른 워크트리는 변경하지 않았다. P4는 이 작업트리·브랜치를 순차 인계받고 P4 종료 후 P5가 이어간다. 빈 Canvas/추적 카메라/공간 인덱스/정렬 캐시/자원 자동 재업로드는 추가하지 않았다. 장치 리셋 때 새 자원 복구가 필요한 것은 명시된 제한이다. PR 생성·게시·병합은 하지 않았다.

정적 검증: 명시 SPECIFY_FEATURE_DIRECTORY로 check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks 성공. 변경 Markdown 15개의 로컬 링크·줄 끝 공백·충돌 표식 검사와 git diff --check 통과. P1/P4/P5 계획 헤더의 브랜치명도 최신 이름과 공유 인계 방식으로 맞췄다.
