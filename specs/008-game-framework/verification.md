# 검증 상태: 게임프레임워크

## 소스 기준 동기화 검증 (2026-11-11)

사용자가 feature/engine을 각 소스 브랜치로 가져와 충돌을 해결하는 것을 명시 승인했다. 기준은 a32333c964be1e81a3da30024efc094184c3e7c5이며 대상 브랜치 자체는 변경하지 않는다. docs README/progress·008 plan/tasks의 문서 충돌만 해결했다. 최신 대상의 정책·아트 기준·제작 스크립트는 그대로 보존하고 아래 검증된 공통 구조를 유지한다.

`git diff e3a0029 -- engine game_framework demos main.py framework_demo.py tests requirements.txt`가 비어 있어 런타임·검사·의존성이 동일하다. docs/workflow.md의 검사 실행 범위와 과도한 검사 방지 사용자 지시에 따라 기존 90개 자동 검사·독점 SDL16 결과를 재사용하고 재실행하지 않았다. feature/engine 대비 PR에서 변경한 문서의 링크·작업 ID·충돌 표식·diff 검사와 feature/engine 포함 관계·merge-tree 충돌 없음을 확인했다. 대상에서 그대로 가져온 art-direction의 로컬 원화 링크는 이 코드 작업트리에 비추적 art 파일이 없어 전체 링크 검사에서 제외했다. 원화나 대상 아트 문서 내용을 임의로 바꾸지 않았다. 다른 소스도 동일한 최종 트리를 사용하므로 브랜치마다 상충하는 현재 문서를 만들지 않는다.

## 엔진/게임 API 경계 정리 검증 (2026-11-11)

사용자 승인 범위: game-facing API를 game_framework에 두고 내부 실행을 engine 패키지로 분리하며 demos·tests/unit·integration·smoke를 분류한다. 상태: FR-011~013/SC-003/004 및 T023~T032 완료. 실행 폴더는 C:/Users/Developer/.codex/worktrees/game-framework/circuit-warden, 브랜치는 feature/game-framework다. 다른 작업트리·PR·대상 브랜치 수정은 범위 밖이다. 소스 브랜치로의 기준 병합은 아래 최신 명시 승인 범위다.

| 검사 | 실제 명령·방법 | 결과 |
|---|---|---|
| 사전 작업·체크리스트 | .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks, requirements.md 읽기 전용 확인 | 필수 문서 확인, 11/11 완료, extensions.yml 없음 |
| 전체 회귀/API/경계 | D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest discover -s tests -q | 90개 통과. 기존 87개와 엔진 독립/중립 실행 2개·지연 수집 실패 1개 |
| 엔진 구현 본문 | git show 595df01:engine.py와 현재 각 담당 모듈의 AST 함수/메서드 본문 비교 | 기존 모든 함수·메서드 본문 보존. 위치·클래스 기반·import만 변경 |
| 실제 SDL 통합 | 같은 Python으로 tests/smoke/integration_smoke.py C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c61f-5a75-7843-b6ce-610dc3aecc4c/framework-boundaries | 독점 최종 실행 종료 0, 16단계 integrated/snapshots/order/alpha/input/camera/resize/fullscreen/minimize/roundtrip/escape PASS |
| 실제 화면 관찰 | 위 출력의 p5-initial.png·p5-resized.png 열기 | 월드/UI source-over 겹침·크기 변경 배치와 오른쪽 기준점 관찰 |
| 정적 문서 검사 | 변경 Markdown의 로컬 링크·작업 ID·충돌 표식 검사, git diff --check | 통과 |

엔진 패키지 검사는 AST import와 새 Python 프로세스로 engine이 game_framework/demos를 import하지 않음을 확인한다. execute는 일반 tuple 목록만으로 안정 정렬·입력 순서·오류 전파를 검사한다. 기존 Renderer 검사는 두 패스·교차 변경/재진입 거부·그리기 실패 정리를 유지하며 새 generator 검사는 지연 수집 도중 실패에도 잠금과 임시 목록이 풀리는 것을 확인한다. SDL 도형/texture 알파와 실패 시 공유 상태 복원은 tests/integration/test_drawing.py에서 실제 소프트웨어 렌더러로 검사한다.

최초 smoke 호출은 출력 폴더를 만들지 않아 실행 전 assert로 중단했고 지정 폴더 생성 후 진행했다. 첫 창 실행은 전체화면 복귀에서 SDL_RenderReadPixels 실패, 동일 코드 재실행과 다른 SDL 창 없이 실행한 최종 검사는 모두 통과했다. 당시 다른 브랜치 SDL 검사가 겹쳤을 가능성이 있으나 원인은 확정하지 않는다. 실패를 숨기거나 통과시키도록 검사/런타임을 완화하지 않았다.

analyze: FR-012→T027/T028, FR-013→T029, SC-004→T030, SC-DOC→T031 대응. converge: 승인된 소유/실행 경계·게임 타입 의존 금지·공개 import/실행 명령·지연 수집/가드·오류 정리·docs를 대조했고 필수 잔여 작업 없음. world/level_scene가 본 구현이며 core/scene는 직전 하위 모듈 import 호환이다. SDL은 engine/rendering에서만 직접 실행하고 게임 drawing은 좌표/값 검사를 제공한다. 월드/UI/통합 예제는 공통 검사 객체 때문에 demos/framework.py에 함께 두었다. 새 추상 관리자·게임 기능·의존성을 추가하지 않았다.

README·docs README/architecture/progress·008 spec/plan/tasks/quickstart를 현재 구조·검사와 동기화했다. 초기 하위 계획의 단일 파일 경로는 당시 단위를 가리키며 현재 위치는 architecture 표가 기준이다. 아래 이전 검증 경로는 당시 실제 실행 근거다. 게임 설계·아트·의존성·도구 환경은 영향 없다.

독립 display/world/UI 실제 창 smoke는 이번 증분에서 재실행하지 않았다. 전체 자동 검사와 통합 실제 창 검사로 변경 경계를 확인했다. 사용자 직접 키·실물 DPI/다른 모니터는 미확인이다. Python __module__ 경로 변경으로 기존 pickle 저장물 호환을 보증하지 않는다(영속 저장 기능 없음). PR 생성·게시·병합은 하지 않았다.

## P1~P5 검증 기반

**상태**: P1~P5 구현·자동 검사·실제 SDL 창 검증 완료. 상세 게임 규칙·아트·성능 목표의 확정은 아니다.
**P1~P5 실행 근거**: 2026-11-10 사용자가 모든 계획의 구현·검증 증분 커밋과 독립 P1/P2 병렬·P3→P4→P5 동일 경로 순차 진행을 지시했다. PR 생성·게시·병합은 범위 밖이다.
**현재 통합 브랜치/작업트리**: `feature/engine`, `C:/Users/Developer/.codex/worktrees/engine-integration/circuit-warden`
**P1~P5 원본 검증 작업트리**: `feature/world-rendering`, `C:/Users/Developer/.codex/worktrees/cbb2/circuit-warden`
**감사 실행 기준**: `bda35a8b42333ee5148167272f3f98abc6b4586e`
**계획 분리 기준 커밋**: `1940dd423daf423a84637b9ccec7d23eb92d722f`

## feature/engine 통합 검증

2026-11-10 사용자가 엔진 기능을 feature/engine에 통합하도록 지시했다. latest main 47b721e와 P1~P5 bda35a8을 합치며 docs/README.md·docs/progress.md 충돌은 최신 아트/정책과 엔진 완료 결과를 함께 보존한다. 기존 준비 브랜치는 다시 병합하지 않는다. 원본 D:/GitHub/circuit-warden의 미커밋 변경 7개는 이 통합에 포함하지 않는다.

감사에서 bda35a8의 `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest discover -s tests -v`는 85개/0.047초 통과했다. 같은 Python의 `tests/integration_smoke.py <출력 폴더>`는 실제 SDL 16단계/종료 0이며 p5-resized.png를 열어 겹침/출력 배치를 관찰했다. 출력은 `C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c5e8-30ea-72d0-bce6-3073464ac646`에 있다. 코드 독립 검토와 창 없는 수명 경계 검사 3개에서도 재현 결함을 발견하지 못했다. 이후 실행 코드·테스트·의존성은 변경하지 않으므로 같은 검사를 반복하지 않는다.

`git diff feature/world-rendering -- engine.py game_framework.py framework_demo.py main.py tests requirements.txt`는 차이 없음이다. `git diff main -- docs/art-direction.md AGENTS.md .specify scripts`도 차이 없음으로 최신 커밋된 아트·정책·제작 스크립트를 보존했다. 변경 Markdown 9개의 로컬 링크 대상·충돌 표식과 `git diff --check`가 통과했다. 당시 analyze/converge 대조에서 새 런타임 변경·필수 미완료·문서 충돌은 없었으며 당시 통합 작업을 완료했다. 두 선행 브랜치의 커밋을 보존하는 merge commit으로 기록한다. 실제 게임·실물 DPI·물리 키 조작·성능 한계는 여전히 미확인이다. 테스트 삭제는 제안만 하며 실행 파일은 보존한다.

## 계획별 결과·커밋

| 계획 | 상태·검증 근거 | 구현·인계 커밋 |
|---|---|---|
| P1 객체·규칙 | core 16개와 기존 회귀 16개 통과. 단일 소유·ID·스냅샷·규칙 격리·실패 정리 | 구현 `d3c4ed06f2efa199c41a15f525b161d9e894f7b3`, 최종 인계 `d23d1dbf0f990d260b72ce5e270fa20c9da9eb1b` |
| P2 창·출력 | 27개 자동·실제 SDL 크기/전체화면/복귀/최소화/입력 검사 통과 | 구현 `6c92565bfe726d50458f1e6eeca64494258073f4`, 최종 인계 `c3eef90` |
| P3 월드 렌더링 | 60개 자동·실제 SDL 픽셀/이미지/경계/레벨 왕복 통과 | 구현 `76e9863cab36fa8e8c0e3db751b26f52b4ded53d`, 최종 인계 `4696fb61317c29a2a91f0eafa9245a5160f78f7b` |
| P4 Canvas UI | 74개 자동·실제 SDL 트리/알파/anchor/입력/최소화 검사 통과 | 구현 `1a88cee34c751954836d676f4aa9012412498cb8`, 최종 인계 `0f4bc9f6151e1fac705499d737da01901c6b28f8` |
| P5 통합 | 전체 85개·실제 통합/월드/UI SDL 회귀 통과. 아래 명령·범위 참조 | 공동 수명·스냅샷 `b11e7a55c3f031720a991e2a9963ba6a79cc531f`, 통합 화면·최종 검증 `7bd9299305717f12243617db8f04e6ac6154e13b` |

P1/P2 검증 커밋은 `e229bf2`에서 Git merge했고 이후 P3/P4/P5는 같은 브랜치에서 순차 진행했다. P5는 P4 완료 채팅·최종 인계·깨끗한 작업트리를 확인한 뒤 쓰기를 시작했다. 기존 준비 브랜치 `feature/game-screen-integration`의 커밋은 보존하고 필요한 문장만 검토해 반영했다. 준비 브랜치 전체 merge·동일 선행 결과 중복 merge·새 checkout·기존 작업트리 삭제/아카이브는 하지 않았다. 원본 D:/GitHub 작업과 다른 작업트리의 미커밋 변경은 건드리지 않았다.

## P1~P5 구현 검증 명령·결과

아래 P1~P5 명령은 원본 검증 작업트리에서 원본 게임 Python으로 실행했다. 실제 창 검사는 동시에 실행하지 않았다.

| 명령·검사 | 결과 |
|---|---|
| `git status --short`, `git branch --show-current`, `git rev-parse HEAD` | P4 인계 당시 깨끗함·feature/world-rendering·0f4bc9f 확인. 최초 제한 실행의 Git status는 경로 접근 제한으로 실패했고 확장 실행은 승인되어 성공 |
| 명시 `SPECIFY_FEATURE_DIRECTORY=specs/008-game-framework`, `SPECIFY_FEATURE_NO_PERSIST=1`로 `check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` | 성공. 필수 문서와 선택 문서 확인. 활성 포인터 변경 없음 |
| `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest discover -s tests -v` | **85개 통과**. 기존 P1~P4 74개, P5 공동 수명·순회 9개, 통합 데모 2개 |
| 같은 Python으로 `tests/integration_smoke.py <출력 폴더>` | 종료 0. 16단계 통합 검사와 Escape 종료·양쪽 소유/임시 참조 해제 assert 통과 |
| 같은 Python으로 `tests/world_smoke.py <출력 폴더>` | 종료 0. `PASS: world/alpha/image/culling/input/camera/resize/fullscreen/roundtrip` |
| 같은 Python으로 `tests/ui_smoke.py <출력 폴더>` | 종료 0. `PASS: ui/tree/order/alpha/anchor/mouse/resize/fullscreen/minimize/cleanup` |
| `git diff --check`, 게임 Python pathlib/re로 변경 Markdown 링크·줄 끝 공백·충돌 표식·작업/명세 ID 검사 | 통과. T001~T022와 FR-001~010/SC-001/002/DOC 대응 확인 |

출력 폴더는 `C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c41b-691b-7d90-a321-b0deae430b7d`다. P5 실제 창은 640×480→960×540→5120×1440 보더리스→960×540 복귀, 최소화/복구를 검사했다. SDL 입력 큐로 월드 생성/삭제·큰 월드 뎁스·카메라·UI 숨김/하위 트리 삭제·A→B→A·Escape를 실행했다. SDL_WarpMouseInWindow가 만든 실제 이동 이벤트에서 월드/UI 역변환이 같은 프레임 출력 상태와 일치함을 확인했다. 최소화 중 update는 유지되고 draw 횟수는 증가하지 않았으며 복구 후 재개됐다.

SDL_RenderReadPixels로 반투명 UI 아래 월드와 UI 패널 간 source-over 픽셀, 큰 월드 뎁스 위 UI, 화면 밖 이동 도형의 경계 진입, 오른쪽 anchor를 assert했다. p5-initial/resized/level-B/return-A.png를 직접 열어 월드 이미지·UI 겹침·카메라와 독립인 UI·화면비·새 초기 배치를 관찰했다. 검사용 픽셀/메모리 texture는 외부 에셋 제작이 아니다.

통합 smoke의 첫 실행은 타이머가 창 생성 전부터 진행해 첫 draw 전에 초기 캡처를 요구한 검사 코드 오류로 실패했다. 타이머를 enter 뒤로 옮겨 재실행했고 위 전체 16단계가 통과했다. 앱 동작·명세를 실패에 맞춰 바꾸지 않았다.

## 요구사항·성공 조건 대응

| 요구사항 | 현재 코드·검사 근거 |
|---|---|
| FR-001/002 | Level/GameObject/GameMode. tests/test_game_framework.py의 소유·ID·한 번 생성/정리·재등록·격리 검사 |
| FR-003 | Level._dispatch_snapshot, Canvas._update_snapshot, LevelScene.update. 두 스냅샷을 콜백 전에 취득하고 모드→월드→UI 전달. tests/test_scene_integration.py의 교차 생성/제거·재진입·실패 가드 복구 |
| FR-004 | LevelScene.enter/exit의 양쪽 정리·복수 오류 보존, Renderer finally 목록 해제. Level 시작/UI 준비 실패·복수 cleanup 오류·Engine.run 월드/UI draw 실패 검사 |
| FR-005 | 기본 FrameworkDemo와 통합/월드 smoke. 업데이트 단일 이동·draw 불변·왕복 초기 배치·모드 속도 격리 |
| FR-006 | 자동 검사·앱 내부 SDL 입력/API·실제 PNG 관찰·사용자 직접 확인을 이 문서에서 구분 |
| FR-007 | Renderer 월드 안정 정렬·UI 형제 DFS·두 패스. 기존 동률/이미지 교차 검사와 P5 큰 월드 뎁스 위 UI 픽셀 검사 |
| FR-008 | 이미지별 bounds+1픽셀 여유·UI 자기 bounds. 기존 부모 밖/자식 안 검사와 P5 실제 경계 진입·카메라 이동·UI 고정 |
| FR-009 | draw_rect/draw_image의 source-over·공유 상태 성공/실패 복원. 실제 SDL 메모리 texture 자동 검사와 통합 UI/월드 픽셀 검사 |
| FR-010 | Engine 출력 상태·WorldTransform/UITransform·event_to_world/ui. 모의 2배 DPI/0출력·실제 크기/전체화면/복귀/최소화/마우스·좌표 보존 검사 |
| SC-001 | 기존 16개 회귀를 포함한 전체 85개 자동 검사 통과 |
| SC-002 | 실제 SDL 통합 창의 크기/전체화면·좌표·시간 이동·생성/제거·순서·UI 겹침·경계·알파·왕복·Escape 종료를 검사하고 저장 출력 직접 관찰 |
| SC-DOC | docs와 spec/plan/tasks/data-model/contracts/quickstart/P5 계획을 실제 API·검사·미확인 환경에 맞춰 갱신하고 정적 대조 |

## analyze·검토·converge와 문서 영향

requirements 체크리스트 11개는 읽기 전용으로 확인했고 수정하지 않았다. 체크리스트는 최초 명세 품질 검토이며 현재 구현 상태는 tasks/verification이 소유한다. `.specify/extensions.yml`이 없어 전후 hooks는 없다. analyze에서 T018~T022가 FR-001~010·SC 전체를 담당하고 새 게임 정책·관리자 계층·최적화가 필요하지 않음을 확인했다.

공동 수명 증분은 신규 9개 미구현 실패를 확인한 뒤 전체 83개로 검증·커밋했다. 이후 기본 통합 화면·독립 --world/--ui·실제 SDL smoke와 통합 2개를 추가해 전체 85개가 통과했다. Sol/high 독립 읽기 전용 검토도 공동 수명/스냅샷/교차 변경/오류 보존과 데모 호출자 호환성을 확인하고 9개·83개·최종 85개를 각각 실행해 통과했다. 재현 가능한 결함은 없었으며 검토자는 실화면·최종 docs를 확인하지 않았다.

최종 converge는 FR 10개·SC 3개·사용자 시나리오·경계 조건·계획 책임·constitution을 현재 코드/검사와 대조했다. 필수 미구현·부분 구현·요구 위반·요청 밖 기능은 발견하지 못했다. 새 잔여 작업을 tasks에 추가하지 않는다. 검증된 범위에서 T018~T022를 완료 처리하고 문서·증거를 함께 커밋한다.

README·docs README/workflow/architecture/progress와 spec/plan/tasks/data-model/contracts/quickstart/P5 계획을 현재 동작에 맞췄다. game-design의 옛 구현 보류 문장도 최신 구현 지시와 검증 상태로 정정했다. 게임 규칙·아트는 그대로 미정이다. systems/art-direction·requirements·Pico2D 설치본·원본 폴더에는 영향 없다. 문서가 소유하는 동일 수치를 새 규칙으로 중복 정의하지 않았다.

## 미실행·한계

- 이번 008에서 사용자 직접 확인·물리 키 조작·테두리 드래그·실물 고DPI/다른 모니터 이동은 수행하지 않았다. 실제 window/output 비율은 1:1이고 2배 DPI는 모의 자동 검사다. SDL 입력 큐/API 검사를 자동 UI 입력 성공이나 사용자 확인으로 표시하지 않는다. 앞 계획에서 일반 창 자동 키 입력은 반응을 확인하지 못했고 원인은 미확정이다.
- 전달된 타깃 리셋은 일반 그림 재그리기와 한 세대 갱신을 허용한다. 장치 리셋·누락 세대는 명시 오류·양쪽 정리로 종료하며 자동 자원 재업로드는 없다. TARGET texture는 복구 로더가 없어 명시 오류로 거부한다.
- 게임 규모·성능 예산·게임 규칙·실제 HUD/메뉴·공통 UI 영속성은 미정이다. 물리·UI 입력 소비/포커스·자동 레이아웃·reparent·공간 인덱스·정렬 캐시를 추가하지 않았다. 실제 플레이 판단·성능 보증은 하지 않는다.
- P1~P5 구현 당시에는 PR 생성·게시·병합을 하지 않았다. 현재 엔진 브랜치 통합은 위 별도 지시를 따른다. 기존 준비 브랜치/작업트리는 보존한다. 필수 기능 미완료는 없으며 위 환경·제품 범위 한계와 구분한다.
