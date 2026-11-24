# Verification: 전하 이동과 피격 피드백

## 전류와 도착

이전 공중 도착은 60Hz 한 프레임 약 8 월드 단위, 첫 100ms에 약 39.4 월드 단위 상승하는 동안 고정된 전류를 표시했다. 첫 렌더를 전류 도착 좌표와 공유하고 표시만 짧게 보간했다. 방향별 전류·위상·연속 이동·지상 복귀 및 공중 연계 표적 12개를 통과했다.

## 최종 표적 검사

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_basic_enemy tests.unit.test_charge_teleport tests.unit.test_teleport_link tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_basic_enemy.BasicEnemySceneTests tests.integration.test_jump_animation tests.integration.test_dash_animation tests.integration.test_resize_input
```

74개 통과. 움직이기 전의 첫 전류·도착 프레임, 지상 도착 자세와 복귀, 연속 이동, 공중 타격 연결, 상단 반동, 공중·지상 돌진 피격, 벽과 보호 시간, 대시·점프·창 입력을 확인했다. 착지 시간 검사를 적 몸통 위쪽의 새 반동과 분리했다.

`tests/performance/charge_benchmark.py --repeats 1`은 이전 비교 대상에서 경과 시간을 제공하도록 보완한 뒤 통과했다. 양쪽 이동 12회, PNG 경로의 실행 중 업로드 0회를 확인했다.

## 실제 SDL 창

- `tests/smoke/charge_smoke.py --output-dir $testOut` 통과. 수평에 가까운 이동과 대각선 및 예약 이동의 첫 섬광, 생성·소모, 기존 공중 타격 후 이탈을 확인했다. 순간이동 9회, 예약 2회였다. 첫 장면에서 고정 전류가 워든 몸에 이어지는 것을 캡처로 확인했다.
- `-m tests.smoke.basic_enemy_smoke --output-dir $testOut` 통과. 실제 돌진 회피 이후 지상 피격, 적 상단에서 무피해 반동, 공중 옆면 돌진 피격을 상황별로 재현했다. 적 상단·공중 피격 검사에는 시작 위치와 적 상태를 지정했다. 최초 지상 피격 검사는 점프 뒤의 상단 반동을 포함해 공중에서 맞았다. 지상 피격 시작 위치를 명시한 뒤 별도 캡처에서 피격 자세를 확인했다. 사망·R·좌우 검 공격·F6도 통과했다.

## 에셋 검증

기존 idle 프레임을 참조해 내장 ImageGen으로 피격 키 자세를 제작했다. 참조의 16색과 이진 알파로 128×104 셀에 등록했고 알파 범위는 `(30,12)–(104,92)`, 기준점은 `(64,92)`다. generate2dsprite의 `assemble_frames.py --strict`는 PNG/atlas RGBA 일치와 120ms 출력을 통과했고 단일 셀의 침범·반복 검사는 건너뛰었다. 검수용 미리보기와 실제 SDL의 지상·공중 캡처에서 몸체 비례, 방향, 발 기준 및 잘림을 관찰했다. [원본·프롬프트·해시](../../assets/warden/source/hurt.provenance.json).

## 대응 및 남은 확인

FR-001·002는 전류 좌표와 도착 프레임·기존 공중 연계, FR-003은 상단·옆면과 지상·공중 피격 결과에 대응한다. 관련 문서와 산출물 경로를 확인했다. 45ms 표시 전환과 120ms 피격은 기술 시험값이다. 전체 회귀와 사용자 직접 조작감은 확인 범위 밖이었다.

## 후속 사용자 재테스트

실전 플레이의 05:58, 06:10, 06:56과 공식 Ferocious Foes의 00:07–00:08 구간을 프레임으로 확인했다. 접근·베기·위치 재조정, 피해 때의 실루엣 변화, 피격 후 착지 전 공격을 기록했다. 입력 표시가 없는 영상으로 입력 지연은 측정하지 않았다. [관찰과 출처](research.md).

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy.BasicEnemySceneTests tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_jump_animation tests.integration.test_dash_animation
```

66개 통과. 새 상단 검사는 수정 전 첫 접촉에서 수평 위치가 그대로여서 실패했다. 수정 뒤에는 입력 없이 무피해·돌진 피격 상단에서 한 번 분리하고 바닥에 닿는지 확인했다. 벽이 한쪽을 막을 때의 방향 전환, 지상 피격 들림, 공중 피격 상태가 풀린 뒤 착지 전 공격, 대시·전하 연계도 확인했다. FR-004와 US2의 두 시나리오를 충족한다.

```powershell
.\.venv\Scripts\python.exe -m tests.smoke.basic_enemy_smoke --output-dir $testOut
.\.venv\Scripts\python.exe tests/smoke/charge_smoke.py --output-dir $testOut
```

실제 SDL 창 검사 두 건 통과. 적 상단의 반동에서 지상 복귀까지 `character-player-top-clear.png`, 공중 피격에서 회복한 뒤 J 입력으로 착지 전 공격하는 화면을 `character-player-air-counter.png`로 캡처했다. 위치와 적의 공격 단계는 테스트에서 지정했다. 전하 검사는 순간이동 9회와 예약 2회, 소모·재생성·공중 연계·창 크기 변경을 통과했다. 첫 기본 적 검사에서 캡처 한 건이 `SDL_RenderReadPixels`로 실패했고, 재실행에서 전체 캡처와 검사가 완료됐다.

새 피격 자세는 기존 idle을 참조해 내장 ImageGen으로 제작했다. 128×104 셀, 알파 범위 `(18,12)–(115,92)`, 발 기준점 `(64,92)`, 이진 알파와 idle 16색을 확인했다. `assemble_frames.py --strict`의 PNG·atlas RGBA 일치와 WebP 120ms를 확인했다. 단일 셀의 경계 침범과 반복 검사는 도구 적용 대상에서 제외되었다. 실제 화면에서 상체와 팔다리가 벌어지는 자세와 최초 접촉 섬광을 함께 관찰했다. [사용 에셋과 원본 해시](../../assets/warden/source/hurt-impact.provenance.json).

전체 회귀와 할로우 나이트 직접 조작 비교는 실행하지 않았다. 워든 피격 시간과 이탈 거리는 플레이 조정용 값이다.

## 돌진 피해의 실제 밀림

유튜브 pikatPlays 호넷전 14:26–14:28을 브라우저에서 느리게 재생하고 프레임을 전진해, 체력 감소와 접촉점 이후 기사 몸의 이동을 비교했다. [프레임 관찰과 출처](research.md#유튜브-호넷전의-실제-피해-반동).

수정 전에는 몸통 접촉과 돌진 옆면 피해가 평균 440의 수평 반동을 공유했다. 지장물이 없는 곳에서 최대 수평 반동은 52.8이었다. 재현 검사에서 접근 방향 키를 누른 지상 워든은 50ms 표본에서 좌우 각각 29.4를 이동했고, 공중은 80ms 표본에서 43.1을 이동했다. 새 검사 기준을 넘지 못했다. 피해 반동에 별도 수평 속도와 지상·공중 상승 속도를 적용하고 계산된 접촉 위치에서 시작하도록 수정했다.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy.BasicEnemySceneTests tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_jump_animation tests.integration.test_dash_animation
.\.venv\Scripts\python.exe -m tests.smoke.basic_enemy_smoke --output-dir tmp/hurt-knockback/sdl
```

관련 자동 검사 68개 통과. 지상 좌우 이동 키 유지, 공중 낙하 속도의 즉시 전환, 벽에서 통과 없이 상승, 착지 전 공격 복귀를 확인했다. 실제 SDL 창에서는 돌진 전 시작점에서 피격을 관측하고 약 70ms 더 진행했을 때 지상 114.2, 공중 113.1을 이동했다. 지상 재현은 전진 키를 계속 눌렀다. `character-player-ground-recoil-displacement.png`와 `character-player-air-recoil-displacement.png`에서 최초 접촉점과 떨어진 위치를 관찰했다. `tmp/hurt-knockback/warden-before-after.gif`는 이전 코드와 현재 코드를 동일한 조건으로 SDL에 그린 로컬 비교 영상이다.

FR-005에 대해 실제 피해, 무피해 몸통 접촉, 회복, 지형 제한을 확인했다. 전체 회귀와 사용자의 직접 조작감 판단은 실시하지 않았다.

## 공중 피격의 착지 궤적

수정 전에는 초기 수평 반동이 120ms 뒤 끝났다. 새 회귀 검사에서 상승 중 x=-120.0과 정점을 지나 하강 중 x=-120.0으로 같아서 실패했다. 수정 후에는 기존 중력을 따르면서 수평 속도를 정점과 하강에도 유지한다. 수직 이동이 착지로 끝난 시점까지 수평 관성을 적용한다. 피해 회복 뒤 공중 공격이 시작되면 공격 중 수평 정지 규칙을 적용한다.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy.BasicEnemySceneTests tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_jump_animation tests.integration.test_dash_animation
.\.venv\Scripts\python.exe -m tests.smoke.basic_enemy_smoke --output-dir tmp/air-recoil-arc/sdl
```

자동 검사 69개와 실제 SDL 창 검사 한 건을 통과했다. 표적 검사에서 입력 없는 상승·정점·하강·착지 및 착지 후 정지를 검증했다. 실제 창은 정점을 지난 하강 중 27.2 월드 단위를 옆으로 이동하고 착지 전 J 공격을 시작했다. 이전 `fd26c45`와 현재 코드를 같은 시작점과 60Hz 갱신으로 렌더해 발 위치를 덧그렸다. 비교 장면에서 정점부터 착지까지 옆으로 이동한 거리가 0에서 58.5 월드 단위가 됐다. 로컬 비교 영상은 `tmp/air-recoil-arc/warden-air-recoil-before-after.gif`에 있다. 전체 회귀와 사용자 직접 조작감은 확인 범위 밖이었다.

## 지상 기본 공격의 짧은 전진

사용자가 전진 시안을 더 자연스럽게 평가했다. 지상 기본 공격의 첫 100ms에 최대 12 월드 단위를 적용하고, 100ms부터 검 판정을 실제 도달 좌표에 만든다. 비교 시안의 140ms는 초기 타격과 전진이 겹치지 않도록 100ms로 조정했다.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_character tests.unit.test_basic_enemy tests.integration.test_character_scene tests.integration.test_basic_enemy tests.integration.test_charge_scene
.\.venv\Scripts\python.exe -m tests.smoke.character_smoke --output-dir $wardensAttackTest
```

자동 94개를 통과했다. 좌우 전진과 고정 방향, 타격 시작 좌표, 벽 앞에서 6 월드 단위에서 멈춘 경우, 공중 공격과 전하 취소를 확인했다. 실제 SDL 조작 검사는 기본 적의 자동 접근을 제외한 뒤 좌우 지상 공격과 일반 이동 복귀를 통과했다. 대상을 포함한 타격과 충돌은 자동 검사로 확인했다. 같은 입력과 렌더 조건에서 기록한 로컬 GIF는 `tmp/attack-lunge/attack-movement-comparison.gif`다. 전체 회귀와 사용자의 실제 적용본 조작감은 검사하지 않았다.
