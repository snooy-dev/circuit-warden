# Verification: 게임오브젝트 충돌

검증일 2026-11-23

| 대상 | 실제 결과 |
|---|---|
| FR-001~003 | 등록 객체와 복수 콜라이더, 상대 레이어 응답, 제거·위치 변경, 최초 접촉, 접선 이동과 이탈, 면적 오버랩과 활성 시간 끝 경계를 단위 검사로 확인했다. |
| FR-004 | 얇은 벽의 걷기·대시 블로킹, 천장 접촉과 발판 착지, 순간이동 도착 거부, 기존 검과 돌진의 피해·우선순위·무적 시간을 확인했다. |
| 실제 SDL 창 | 실제 `CharacterScene`에 얇은 테스트 벽을 렌더링하고 고정 시간으로 걷기·대시 정지, 순간이동 도착 거부, 적 돌진의 통과·피해, 객체 및 창 정리를 확인했다. 사용자 직접 플레이는 미확인이다. |
| 기존 캐릭터 smoke | 최초 1회 통과했고 재실행에서 오른쪽 달리기와 왼쪽 대시 복귀 단언이 각각 실패했다. 변경 전 `9200ddd`에서도 왼쪽 달리기 단언 실패를 재현했다. 실패 원인은 확정하지 않았다. |

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_collision tests.unit.test_character tests.unit.test_basic_enemy tests.unit.test_charge_teleport tests.unit.test_game_framework tests.integration.test_basic_enemy tests.integration.test_character_scene tests.integration.test_dash_animation tests.integration.test_jump_animation tests.integration.test_charge_scene
# 123개 통과
.\.venv\Scripts\python.exe -B -m tests.smoke.character_smoke --output-dir $collisionSmokeDir.FullName
# 위 표의 기존 smoke 결과 참조. collisionSmokeDir는 프로젝트 밖 임시 폴더다.
$env:SPECIFY_FEATURE_DIRECTORY='specs/016-collision'
./.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
# 기능 디렉터리와 명세·계획·작업 파일 확인
git diff --check
# 공백 오류 없음, 새 파일은 별도 검사
```

`docs/architecture.md`에 현재 API와 기하 계약을 반영하고 `docs/progress.md`에 요청 근거와 적용 상태를 추가했다. 공격 FX 문서 변경은 작업 트리에 보존했다.

이전 Git 시도에서는 `.git` 잠금 파일 생성이 거부됐다. 이번 사용자 요청으로 권한 승인을 받아 `feature/collision`을 만들었다. 위 단위·통합 검사 123개를 다시 실행해 모두 통과했다. SDL 창 검사는 기존 기록을 재사용했다.

## FR-005 적 몸통 접촉 반동

- 양방향 이동 중 반동과 통과 방지, 이동 입력 복귀, 돌진 피해·대시 취소, 피격 보호 중 벽에서 적 이동 제한, 높은 위치 통과, 적 몸통으로의 순간이동 거부, 치명타 처리 순서를 확인했다.
- 실제 SDL 창에서 대시로 적 몸통에 닿았을 때 두 몸통이 분리되고 대시 잔상이 제거되는 것을 화면 캡처로 확인했다. 기존 돌진 회피·피해·재시작·양방향 검·창 정리도 통과했다. 반동 속도와 거리의 사용자 조작감은 미확인이다.
- [전투 규칙](../../docs/systems/basic-enemy.md), [기술 구조](../../docs/architecture.md#2d-콜리전), [진행 상태](../../docs/progress.md)에 반영했다. 프레임 안 워든 경로는 시작과 끝 사이 선형 근사를 사용한다.

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_collision tests.unit.test_character tests.unit.test_basic_enemy tests.unit.test_charge_teleport tests.integration.test_basic_enemy tests.integration.test_character_scene tests.integration.test_dash_animation tests.integration.test_jump_animation tests.integration.test_charge_scene
# 98개 통과
$collisionSmokeOutput = Join-Path ([System.IO.Path]::GetTempPath()) ('circuit-warden-rebound-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe -B -m tests.smoke.basic_enemy_smoke --output-dir $collisionSmokeOutput
# PASS, character-enemy-contact-rebound.png 캡처 확인
$env:SPECIFY_FEATURE_DIRECTORY='specs/016-collision'
powershell -NoProfile -ExecutionPolicy Bypass -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
# 기능 경로와 작업 문서 확인
git diff --check
# 공백 오류 없음
```
