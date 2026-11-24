# Verification: 오프닝 스토리 컷신

## 2026-11-24

| 구분 | 실제 명령 | 결과 |
|---|---|---|
| 실제 SDL 창과 입력 | `$env:PYTHONPATH='.'` 설정 후 `.\.venv\Scripts\python.exe -B tmp/story_intro_smoke.py` | 기본 진입점을 네 번 실행했다. 1280×720에서 두 컷·자막·자동 종료, 1024×720에서 Skip 클릭, 1536×864 전체화면에서 Escape 건너뛰기, `--training`의 직접 진입을 확인했다. 자동 종료와 두 건너뛰기 경로는 각각 전원 구역에 한 번 진입했다. 컷신 중 R·이동과 건너뛰기와 같은 프레임의 Space가 레벨에 전달되지 않았다. 낙뢰 등장, R 재시작, 이동 입력으로 조기 등장, 컷신의 이미지·Canvas 해제를 확인했다. |
| 화면 관찰 | SDL의 `SDL_RenderReadPixels`로 `tmp/story-intro-*.png`를 저장해 확인 | 두 자막과 건너뛰기 표시, 축소 창 상하 검은 여백, 전체화면 배치, 실제 레벨 낙뢰를 캡처에서 확인했다. |
| 집중 자동 검사 | `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_ui_input tests.unit.test_engine.EngineTests.test_quit_and_escape_skip_remaining_work tests.unit.test_engine.EngineTests.test_pending_fullscreen_uses_old_output_for_click_then_refreshes -v` | 4개 통과. 클릭 확정·포커스 이동, Escape/종료, 화면 모드 변경 시 클릭 좌표를 확인했다. |
| 변경 공백 | `git diff --cached --check` | 커밋에 포함되는 변경에서 공백 오류가 없었다. |

두 원화는 ImageGen 내장 도구에서 제작한 PNG를 `assets/story-intro/`로 복사했다. 기존 글꼴·장면 전환을 사용했으며 게임 의존성은 그대로다. 문서에는 [게임 흐름](../../docs/game-design.md#오프닝-스토리-컷신), [장면 책임](../../docs/architecture.md#코드-폴더-구조), [아트 기준](../../docs/art-direction.md#오프닝-스토리-컷신), [진행 상태](../../docs/progress.md)를 반영했다. 사용자 직접 시청과 첫 플레이어의 이야기 이해도는 미확인이다. 전체 회귀는 이번 변경 범위에 포함하지 않았다.
