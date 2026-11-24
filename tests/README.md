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
| 기본 적의 타격·돌진·모션 시간 경계·피격 보호·재시작 | unit/test_basic_enemy.py, integration/test_basic_enemy.py |
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
| 기본 적의 이동·공격 포즈·양방향 전투·회피·체력·재시작 | `.\.venv\Scripts\python.exe -B -m tests.smoke.basic_enemy_smoke --output-dir $testOutput` |
| 이동·공중 명중·돌진 회피·전하 생성과 소비·창 좌표 | `.\.venv\Scripts\python.exe tests/smoke/charge_smoke.py --output-dir $testOutput` |
| 캐릭터 출력·입력 | `.\.venv\Scripts\python.exe -B tests/smoke/character_smoke.py --output-dir $testOutput` |
| 월드·카메라·이미지 | `.\.venv\Scripts\python.exe -B tests/smoke/world_smoke.py $testOutput` |
| 독립 UI·앵커·트리 | `.\.venv\Scripts\python.exe -B tests/smoke/ui_smoke.py $testOutput` |
| 월드/UI 결합·장면 왕복 | `.\.venv\Scripts\python.exe -B tests/smoke/integration_smoke.py $testOutput` |

character_smoke는 실제 GameplayMode에서 좌우 지상·공중 공격과 유지 키 복귀를 확인하고, 첫 프레임과 베기 구간을 캡처한다.

SDL 이벤트 주입·픽셀 검사는 사람의 플레이 품질 평가와 다르다. 각 스크립트는 상시 통과 관문이 아니다.

## 사용자 요청 시 전체 회귀

전체 회귀는 사용자가 명시적으로 요청한 경우에만 실행한다. 기본적으로 이번 구현에서 바꾼 동작과 직접 영향을 받는 동작에 맞춰 검사를 선택한다.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -q
```

관련 코드·테스트·의존성·실행 환경에 변화가 없어 유효한 결과는 재사용한다. 문서 수정만으로 게임 검사를 반복하지 않는다. 과거 001/008 실행 기록은 당시 커밋 기준이다.

전하의 거리·상태 취소·선입력·반전은 tests.unit.test_charge_teleport, 구운 전류 원본 샘플·짧은 거리/방향별 끝점·수명은 tests.unit.test_teleport_link, 실제 자산·좌표·PNG 공유/로딩 실패·장면 해제는 tests.integration.test_charge_scene을 선택한다. 회전 그리기의 alpha/blend 복원은 tests.integration.test_drawing에서 확인한다. charge_smoke는 SDL 키·클릭으로 지상·공중 전투, 기술 전하 생성·소비, 환경 전하의 다른 위치 재생성, 100ms 안의 예약, F6/F11을 확인하고 화면을 캡처한다.

감사 회귀의 실제 창 검사는 `tests/smoke/audit_smoke.py --output-dir $testOutput`이다. SDL 큐의 F6 다음 묶음 클릭과 예약 공격 첫 프레임을 검사하며, 공격 시간 경계만 고정 dt로 재현한다.

효과 성능 비교는 `.\.venv\Scripts\python.exe -X utf8 -B tests/performance/charge_benchmark.py`다. 기준은 NumPy 최적화 커밋 `eb082e5`이며 Git 이력이 필요하다. 새 게임 의존성에는 NumPy가 없지만 이전 구현을 실행하는 이 비교에만 필요하므로, 벤치마크를 수행할 환경에서 `.\.venv\Scripts\python.exe -m pip install numpy==2.5.4`로 준비한다. 일반 게임/테스트를 위해 설치할 필요는 없다.

기존 재사용 전하 배치의 같은 클릭 시나리오를 양쪽에서 별도 워밍업한 뒤 기본 5쌍 교대 측정한다. 비교에 쓰는 장면에서 전하 소비, 추가 적중·소모 효과와 적 행동을 끈다. 양쪽 순간이동12회와 변경 후 업로드0회를 확인한다. 측정은 update/draw/SDL 소프트웨어 present이며 이벤트 처리·SDL_RenderClear·실제 창/GPU/VSync·프레임 대기는 제외한다. p95는 실행별95백분위의 중앙값이고 최대/초과는전체900프레임 기준이다. 로딩은 장면 enter 시간, RGBA는 구운 이미지 크기의 합계이며 프로세스 최대 메모리가 아니다. 시각 차이가 허용되므로 전후 전체 출력 바이트 일치를 요구하지 않는다.

제작 합성과 사전 생성 PNG 검사: `.\.local-tools\python\Scripts\python.exe -X utf8 -B scripts/bake-effects/check.py --output-dir $testOutput`. 기존 합성1,944샘플 기준·원본154프레임·구운2,376프레임을 확인하고648전환 샘플의 색 차이와 비교 이미지를 출력한다. 전류 생성기는 승인 원본을 직접 호출하고 첫 섬광 끝점·기존48px RGBA SHA를 자체 검사한다. 생성/검사 방법은 [도구 구성](../docs/tooling.md#효과-png-재생성)을 따른다.
