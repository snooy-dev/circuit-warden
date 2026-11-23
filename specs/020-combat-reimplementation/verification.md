# Verification: 전투 조작과 플랫폼 테스트 맵 재구현

## 레퍼런스 관찰

[할로우 나이트 무해설 플레이, 잊혀진 교차로 7:45–8:13](https://www.youtube.com/watch?v=LNjXu87zmzg&t=465s)를 실제로 재생했다. 지상 적 타격의 섬광, 횡이동 중 캐릭터 주변에 유지되는 화면 구도, 높이가 다른 플랫폼 사이의 이동과 점프를 확인했다. 영상에 키 입력이 표시되지 않아 점프 속도와 카메라 지연은 영상에서 역산할 수 없다. 카메라 0.22초 시간 상수, 점프 해제 시 속도 상한 48%, 지상 베기 100ms·공중 베기 117ms 시작은 Circuit Warden의 시험값이다.

## 분석과 수렴

FR-001~006과 US1~4를 모두 구현했다. 이동·대시·밀림의 지형 판단을 카메라 시야와 분리하고, 환경 전하도 카메라 밖에서 재생성되도록 보완했다. 타격 구간은 첫 100ms 경계와 200ms 종료 경계를 검사하며, 위치 스냅샷은 피격과 순간이동에서 지운다. 실제 플레이어 점프의 Space 해제는 대시 체공이 끝나 수직 적분이 재개될 때 적용할 수 있다. 전투 조작·적 전투·전하·기술 구조·아트 기준과 진행 문서를 갱신했다.

## 검증 근거

| 요구사항 | 자동 검사 및 관찰 |
|---|---|
| FR-001~002 | 좌우 이동·반전 중 공격 방향, 활성 시각 시작·종료, 상대 이동에서만 닿는 적, 지형에 막힌 검의 도달 거리, 공격당 1회, 공중 착지와 전하 취소를 표적 검사했다. |
| FR-003~005 | 카메라 추적 지연, 좌우 끝 벽과 월드 안 낮은 벽 정지, 화면→월드 클릭, 재시작, 적 돌진 벽 정지, 발판 착지·이탈과 점프 높이·거리 차이를 검사했다. |
| FR-006 | 지상·공중 베기 원본과 워든 몸체를 분리해 FX 최대 가시 높이 각각 83px을 확인했다. SDL에서 지상 베기의 주 획이 손 가까이 지나가고 공중 궤적이 칼끝을 잇는 프레임, 발판 착지, 낮은 벽 접촉 화면을 확인했다. |

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_character tests.unit.test_basic_enemy tests.integration.test_character_scene tests.integration.test_basic_enemy tests.integration.test_jump_animation tests.unit.test_input_buffer tests.integration.test_charge_scene
.\.venv\Scripts\python.exe -B -m tests.smoke.combat_reimplementation_smoke --output-dir .local-tools/verification/combat-reimplementation
$combatSmokeOutput = Join-Path $env:TEMP 'circuit-warden-character-020'
New-Item -ItemType Directory -Path $combatSmokeOutput -Force | Out-Null
.\.venv\Scripts\python.exe -B -m tests.smoke.character_smoke --output-dir $combatSmokeOutput
& .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
git diff --check
```

이전 버전에서 관련 자동 검사 112개가 통과했다. 대시 체공 중 키 해제를 수직 이동 재개 시점에 적용하는 후속 변경에서 공중 공격과 키 해제의 기대값을 갱신했다. 현재 버전에서는 아래 검사를 4개와 13개의 두 실행으로 나눠 모두 통과했다.

```powershell
$combatRecheck = @(
    'tests.unit.test_character.CharacterTests.test_air_attack_applies_jump_release_and_ground_attack_buffers_jump'
    'tests.unit.test_character.CharacterTests.test_jump_release_waits_for_vertical_motion_to_resume_after_dash'
    'tests.unit.test_character.CharacterTests.test_air_attack_preserves_jump_arc_and_resumes_fall'
    'tests.unit.test_character.CharacterTests.test_releasing_space_reduces_apex_and_lands_earlier'
    'tests.unit.test_character.CharacterTests.test_attack_starts_at_first_frame_and_resumes_held_key'
    'tests.unit.test_character.CharacterTests.test_attack_release_opposite_keys_and_focus_return_to_idle'
    'tests.unit.test_basic_enemy.BasicEnemyTests.test_active_window_once_per_swing_and_removal'
    'tests.unit.test_basic_enemy.BasicEnemyTests.test_moving_ground_attack_stops_at_wall_and_cannot_hit_past_reach'
    'tests.unit.test_basic_enemy.BasicEnemyTests.test_sword_hits_target_reached_only_during_active_horizontal_motion'
    'tests.unit.test_basic_enemy.BasicEnemyTests.test_split_long_update_keeps_active_attack_snapshot'
    'tests.unit.test_basic_enemy.EnemyChargeTests.test_enemy_entering_at_sword_window_end_is_not_hit'
    'tests.integration.test_character_scene.CharacterSceneTests.test_buffered_ground_attack_preserves_first_composite_frame_after_slow_frame'
    'tests.integration.test_character_scene.CharacterSceneTests.test_ground_attack_draws_moving_composite_with_fixed_orientation_and_clears_on_exit'
    'tests.integration.test_character_scene.CharacterSceneTests.test_camera_lags_motion_freezes_at_walls_and_resets_with_player'
    'tests.integration.test_character_scene.CharacterSceneTests.test_camera_freezes_at_low_wall_inside_world_bounds'
    'tests.integration.test_character_scene.CharacterSceneTests.test_jump_onto_training_platform_and_walk_off'
    'tests.integration.test_charge_scene.ChargeSceneTests.test_environment_retries_a_blocked_site_without_reusing_spent_object'
)
.\.venv\Scripts\python.exe -B -m unittest $combatRecheck[0..3]
.\.venv\Scripts\python.exe -B -m unittest $combatRecheck[4..16]
```

실제 1280×720 SDL 훈련장 창 검사는 키 이벤트를 전달해 통과했다. 평지의 짧은 점프는 높이 38.1·거리 69.1, 긴 점프는 높이 165.9·거리 144.0 월드 단위였다. 워든이 낮은 벽의 접촉점 x=916에 도달한 뒤 이동 키를 0.32초 이상 유지해 위치와 카메라가 그대로인 것을 관찰했다. 스프라이트 한 프레임의 타격 경로는 선형 근사이며, 지상 절정 프레임의 작은 파편은 발 기준선 아래로 최대 7px 내려온다. 사용자의 직접 조작감·미술 평가는 미확인이다.

기존 캐릭터 창 검사는 동시 검사 중 대시 캡처 목록 검증이 한 번 실패했다. 인수 후 `959e252`에서 다른 창 검사나 영상 재생 없이 새 임시 출력 폴더로 위 `tests.smoke.character_smoke` 명령을 단독 재실행했다. 종료 코드 0으로 통과했고 지상·공중 대시의 준비·이동·복귀 캡처 6장, 창 크기 변경·전체화면 전환·복귀와 종료를 확인했다. 이전 실패는 이번 실행에서 재현되지 않았으며 원인은 확인하지 못했다.

## 후속 검사와 Git

전하 진입 후 공중 명중·공격 취소 이탈과 순간이동 보호 종료 시점의 표적 검사 2개를 통과했다.

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_basic_enemy.BasicEnemySceneTests.test_low_charge_enables_an_air_hit_and_immediate_cancel_to_next_charge tests.unit.test_basic_enemy.EnemyChargeTests.test_teleport_guard_only_prevents_damage_before_contact_deadline
```

기본 권한에서는 `git switch -c feature/combat-reimplementation`의 `.git/refs/heads/feature/combat-reimplementation.lock` 쓰기가 거부됐다. 같은 명령을 권한 확장으로 실행해 브랜치를 생성했다. 앞선 SDL 결과를 재사용했고, 게임 코드를 변경하지 않아 창 검사를 다시 실행하지 않았다.

## 인수인계와 남은 확인

- **기준 커밋:** `feature/combat-reimplementation`의 `959e252`다. 위 일곱 모듈의 `unittest` 명령으로 최종 코드의 관련 검사 113개가 통과했다. 인수 후에는 게임 코드 변경 없이 기존 결과를 재사용하고 캐릭터 SDL 창 검사만 다시 실행했다.
- **남은 확인:** 사용자의 직접 플레이에서 이동 중 공격, 가변 점프, 카메라 반응과 베기 효과의 가독성을 평가한다. 전체 회귀는 검사 범위에 포함하지 않았다.
- **문서 범위:** `docs/progress.md`에 검증 결과를 반영했다. `docs/art-direction.md`와 `docs/progress.md`의 2026-11-18 공격 FX 타이밍 정정은 별도 작업 트리 변경으로 보존했다.
