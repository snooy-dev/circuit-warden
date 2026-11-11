# 필요한 검사만 실행하기

작은 기능은 게임을 실행해 바뀐 동작을 직접 확인하면 된다. 자동 테스트를 만들거나 아래 명령을 모두 실행할 필요가 없다. 선택 기준은 [워크플로우](../docs/workflow.md#검사-실행-범위)를 따른다.

```powershell
.\.venv\Scripts\python.exe main.py
```

자동 검사가 필요한 구체적 위험이 있으면 해당 메서드를 지정한다. 예를 들어 유지 키 처리 변경은 다음처럼 검사한다(매 기능 공통 명령이 아니다).

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_character.CharacterTests.test_repeat_opposite_keys_and_release -q
```

| 확인할 위험 | 선택할 위치 |
|---|---|
| 캐릭터 이동·공격 전이·재생 | unit/test_character.py의 해당 메서드 |
| 이미지 로딩·실패/종료 해제 | integration/test_character_scene.py, test_scene_integration.py의 해당 메서드 |
| 루프·이벤트·장면 수명 | unit/test_engine.py, test_game_framework.py의 해당 메서드 |
| 좌표·컬링·알파·정렬 | unit/test_world_rendering.py, test_render_execution.py, integration/test_drawing.py의 해당 메서드 |
| 스프라이트 시간·자원 | unit/test_sprites.py의 해당 메서드 |

사각형 API는 게임 바닥과 UI도 사용하므로 좌표·알파·상태 복원 검사는 보존한다. 초기 데모 전용 검사, 패키지 분리 당시 구조 확인, 검사용 장면 자체의 자동 검사는 삭제했다. tests/fixtures는 필요한 실제 창 검사의 자료이며 게임에서는 import하지 않는다.

## 실제 창 검사가 필요한 경우

화면·입력·창 동작에 영향이 있을 때 필요한 스크립트만 실행한다. 출력 폴더는 먼저 만든다. 예: `$testOutput = Join-Path $env:TEMP 'circuit-warden-smoke'`, `New-Item -ItemType Directory -Force -Path $testOutput`.

| 변경 범위 | 선택 명령 |
|---|---|
| 캐릭터 출력·입력 | `.\.venv\Scripts\python.exe -B tests/smoke/character_smoke.py --output-dir $testOutput` |
| 월드·카메라·이미지 | `.\.venv\Scripts\python.exe -B tests/smoke/world_smoke.py $testOutput` |
| 독립 UI·앵커·트리 | `.\.venv\Scripts\python.exe -B tests/smoke/ui_smoke.py $testOutput` |
| 월드/UI 결합·장면 왕복 | `.\.venv\Scripts\python.exe -B tests/smoke/integration_smoke.py $testOutput` |

character_smoke는 실제 GameplayMode를 통해 양 방향 공격·추가 클릭 무시·유지 키 복귀와 첫 프레임 캡처를 포함한다.

SDL 이벤트 주입·픽셀 검사는 사람의 플레이 품질 평가와 다르다. 네 스크립트는 상시 통과 관문이 아니다.

## 넓은 통합 변경에만 전체 회귀

공통 엔진의 광범위한 변경이나 여러 기능 통합으로 영향 범위를 좁히기 어려울 때 선택한다. 매 기능·커밋·PR마다 실행하지 않는다.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -q
```

같은 코드와 환경에서 통과한 결과는 재사용한다. 문서 수정만으로 게임 검사를 반복하지 않는다. 과거 001/008 실행 기록은 당시 커밋 기준이다.
