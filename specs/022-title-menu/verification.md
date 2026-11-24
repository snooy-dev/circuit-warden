# Verification: 게임 타이틀 메뉴

## 2026-11-24

| 구분 | 실제 명령 | 결과 |
|---|---|---|
| 집중 자동 검사 | `.\.venv\Scripts\python.exe -m unittest tests.unit.test_ui_input tests.unit.test_engine.EngineTests.test_quit_and_escape_skip_remaining_work tests.unit.test_engine.EngineTests.test_pending_fullscreen_uses_old_output_for_click_then_refreshes tests.unit.test_render_execution tests.unit.test_game_framework.CanvasTests.test_anchor_parent_offset_self_culling_opacity_and_subtree_hiding tests.unit.test_game_framework.CanvasTests.test_ui_culling_keeps_unknown_partial_boundary_and_pixel_margin tests.unit.test_game_framework.CanvasTests.test_render_mutation_and_failure_release_guards_and_references` | 8개 통과. 포커스·클릭 취소·앞 버튼 우선, 종료, 좌표·렌더 정리 검사 |
| 실제 SDL 창·타이틀 화면 | `$env:PYTHONPATH='.'` 설정 후 `.\.venv\Scripts\python.exe tmp/title_menu_smoke.py` | 임시 검사기로 기본 진입점을 실행하고 SDL 키·마우스 입력을 주입했다. Settings 진입, 전체화면 왕복, 1024×720 적용, 마우스 Back, Escape 복귀, New Game의 첫 레벨 첫 프레임과 창 크기 유지, Quit 및 장면 정리를 확인했다. 캡처한 타이틀과 설정 화면의 텍스트·배치를 확인했다. |
| 기존 UI 실제 SDL 검사 | `.\.venv\Scripts\python.exe tests/smoke/ui_smoke.py tmp/title-ui-regression` | UI 트리의 가시성·그리기 순서·알파·anchor·마우스·창 크기·전체화면·최소화·자원 정리 통과 |
| 훈련장 진입 경로 | `.\.venv\Scripts\python.exe -`에 `unittest.mock`으로 `--training` 인수와 `Engine.run`을 바꾼 검사 전달 | 초기 장면이 전원 구역이 아닌 기존 훈련장인지 확인했다. |

[기술 구조](../../docs/architecture.md), [게임 설계](../../docs/game-design.md), [진행 상태](../../docs/progress.md)에 현재 구현을 반영했다. 사용자가 직접 조작한 결과는 미확인이다. 전체 회귀는 요청 범위에 해당하지 않아 실행하지 않았다.

## 타이틀 시각 보정

| 구분 | 실제 명령 | 결과 |
|---|---|---|
| 실제 SDL 창과 캡처 | `$env:PYTHONPATH='.'` 설정 후 `.\.venv\Scripts\python.exe tmp/title_menu_smoke.py` | 1280×720 및 1024×720 창과 1536×864 전체화면에서 키 가이드 제거, 제목·메뉴·설정값 배치와 선택 표시를 확인했다. 키보드 선택, 크기 변경 후 마우스 선택, 설정 복귀, New Game, Quit을 다시 실행했다. |
| 집중 자동 검사 | `.\.venv\Scripts\python.exe -m unittest tests.unit.test_ui_input tests.unit.test_game_framework.CanvasTests.test_anchor_parent_offset_self_culling_opacity_and_subtree_hiding tests.unit.test_game_framework.CanvasTests.test_render_mutation_and_failure_release_guards_and_references` | 입력 2개와 Canvas 2개 통과 |
| 배포 글꼴 확인 | 두 TTF와 `licenses/barlow-OFL.txt`에 `git hash-object` 실행 | Google Fonts 원본 blob과 세 파일의 해시가 일치했다. |

[게임 설계](../../docs/game-design.md)와 [기술 구조](../../docs/architecture.md), [진행 상태](../../docs/progress.md)에 시각 보정 내용을 반영했다. 사용자 직접 평가는 미확인이다. 전체 회귀는 요청 범위에 해당하지 않아 실행하지 않았다.

후속 작업에서 `git switch -c feature/title-menu`로 전용 브랜치를 생성했다. 게임 코드·자산·테스트 변경 없이 기존 검사 결과를 재사용했다. `git diff --cached --check -- . ':(exclude)licenses/barlow-OFL.txt'`가 통과했다. 라이선스 원본의 줄 끝 공백 1개는 보존했으며 `git -c core.whitespace=-blank-at-eol diff --cached --check -- licenses/barlow-OFL.txt`로 나머지 공백을 확인했다.
