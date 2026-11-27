# Verification: 오프닝 스토리 컷신

## 2026-11-24 실시간 재연출

| 구분 | 실제 명령 | 결과 |
|---|---|---|
| 실제 SDL 창·입력 | `$env:PYTHONPATH='.'` 설정 후 `.\.venv\Scripts\python.exe -X utf8 -B tmp/power_opening_smoke.py` | 정상 재생에서 팬 기동·정지·재기동, 낙뢰 타격, 조작 전 최종 카메라와 일반 카메라의 일치, 같은 레벨·워든의 유지와 첫 이동을 확인했다. 1024×720 클릭과 전체화면 Escape 건너뛰기에서 같은 장면의 즉시 조작을 확인했다. 연출 중 D와 R은 플레이에 적용되지 않았고, 인계 후 R·짧은 낙뢰·조기 이동과 `--training` 경로를 확인했다. |
| 출력 관찰 | SDL 실제 출력 프레임을 저장한 후 프로젝트 FFmpeg로 `tmp/power-opening-preview.mp4`와 `tmp/power-opening-sheet.png`를 생성 | 전선 스파크, 팬의 정지와 카메라 후퇴, 낙뢰와 워든 등장, 검은 띠가 걷히는 순서와 첫 움직임을 확인했다. |
| 집중 자동 검사 | `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_ui_input tests.unit.test_charge_teleport tests.unit.test_engine.EngineTests.test_pending_fullscreen_uses_old_output_for_click_then_refreshes -q` | 8개 통과. 컷신에 사용하는 버튼 입력과 화면 모드 좌표, 전하 조작을 확인했다. |
| 변경 공백 | `git diff --cached --check` | 커밋 대상의 공백 검사를 통과했다. |

정지 삽화는 이전 커밋 `45c9172`에 보존돼 있다. 현재 컷신은 같은 레벨의 팬·카메라·밝기·방전과 기존 낙뢰를 사용한다. 처음 본 플레이어의 이야기 이해도, 사용자 직접 평가는 미확인이다. 전체 회귀는 실행하지 않았다.

## 2026-11-24 정지 삽화 시안 기록

| 구분 | 실제 명령 | 결과 |
|---|---|---|
| 실제 SDL 창과 입력 | `$env:PYTHONPATH='.'` 설정 후 `.\.venv\Scripts\python.exe -B tmp/story_intro_smoke.py` | 기본 진입점을 네 번 실행했다. 1280×720에서 두 컷·자막·자동 종료, 1024×720에서 Skip 클릭, 1536×864 전체화면에서 Escape 건너뛰기, `--training`의 직접 진입을 확인했다. 자동 종료와 두 건너뛰기 경로는 각각 전원 구역에 한 번 진입했다. 컷신 중 R·이동과 건너뛰기와 같은 프레임의 Space가 레벨에 전달되지 않았다. 낙뢰 등장, R 재시작, 이동 입력으로 조기 등장, 컷신의 이미지·Canvas 해제를 확인했다. |
| 화면 관찰 | SDL의 `SDL_RenderReadPixels`로 `tmp/story-intro-*.png`를 저장해 확인 | 두 자막과 건너뛰기 표시, 축소 창 상하 검은 여백, 전체화면 배치, 실제 레벨 낙뢰를 캡처에서 확인했다. |
| 집중 자동 검사 | `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_ui_input tests.unit.test_engine.EngineTests.test_quit_and_escape_skip_remaining_work tests.unit.test_engine.EngineTests.test_pending_fullscreen_uses_old_output_for_click_then_refreshes -v` | 4개 통과. 클릭 확정·포커스 이동, Escape/종료, 화면 모드 변경 시 클릭 좌표를 확인했다. |
| 변경 공백 | `git diff --cached --check` | 커밋에 포함되는 변경에서 공백 오류가 없었다. |

두 원화는 ImageGen 내장 도구에서 제작한 PNG를 `assets/story-intro/`로 복사했다. 기존 글꼴·장면 전환을 사용했으며 게임 의존성은 그대로다. 문서에는 [게임 흐름](../../docs/game-design.md#오프닝-스토리-컷신), [장면 책임](../../docs/architecture.md#코드-폴더-구조), [아트 기준](../../docs/art-direction.md#오프닝-스토리-컷신), [진행 상태](../../docs/progress.md)를 반영했다. 사용자 직접 시청과 첫 플레이어의 이야기 이해도는 미확인이다. 전체 회귀는 이번 변경 범위에 포함하지 않았다.
