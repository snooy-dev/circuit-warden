# Verification: 착지·검격·피격 조작 반응

**Date** 2026-11-26

## 표적 자동 검사

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_jump_animation tests.unit.test_input_buffer tests.unit.test_character tests.unit.test_basic_enemy tests.integration.test_basic_enemy tests.integration.test_power_supply_flow tests.integration.test_power_supply_boss tests.integration.test_power_supply_enemies -q
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_charge_scene tests.unit.test_charge_teleport -q
```

조작·전투 108개와 전하 26개 통과. 착지 접촉 전후 이동과 갱신 분할, 일반 착지 공격·대시·재점프, 대시 도중 착지, 지상·공중 검격과 실제 활성 시작·종료, 피격 뒤 예약 공격·대시, 활선의 중복 피해 방지와 섬광을 확인했다. 전하 선택, 도착, 연계와 공격 취소를 함께 확인했다.

## SDL 실행

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.power_supply_smoke --output-dir tmp/warden-responsive-routes
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.combat_reimplementation_smoke --output-dir tmp/warden-responsive-combat
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.charge_smoke --output-dir $chargeProof
```

고정 60Hz SDL에서 냉각 경로 84.48초와 콘덴서 경로 70.08초에 출력에 도달했다. 두 경로 모두 릴레이 복구, 보스 처치와 R을 거쳤다. 일반 적 전투와 창 출력도 확인했다.

실제 훈련장 창에서 지상·공중 검격, 공격 뒤 방향 대시, 짧은 점프 약 80과 긴 점프 약 166 높이, 착지 직후 달리기와 재점프, 벽 충돌을 확인했다. 실제 전하 검사에서는 전하 이동 9회, 예약 연계 2회와 공중 명중·돌진 회피를 확인했다.

실제 전원 구역 창은 `PowerSupplySmoke`를 기본 Engine에서 실행하고, 포커스 이벤트를 출력하여 다시 확인했다. 첫 실시간 시도에서 흡기실 주행이 중단됐고, 재실행은 냉각 경로 84.50초와 콘덴서 경로 70.06초에 출력까지 통과했다. 일반 적 검사에서 콘덴서 방전 직후 워든의 섬광을 화면에서 확인하고, 반동 중 누른 공격이 잠금 해제 후 나가는 것을 확인했다.

## 문서 영향

공용 조작은 [기본 게임플레이](../../docs/systems/basic-gameplay.md), 피해·섬광은 [기본 적 전투](../../docs/systems/basic-enemy.md), 갱신 경계와 입력 보관 시간은 [기술 구조](../../docs/architecture.md), 구현 상태는 [진행 상태](../../docs/progress.md)에 반영했다. 전체 회귀와 사람이 느끼는 조작감 평가는 실행하지 않았다.

## 지상 검격 중 이륙

게임 가상환경의 `python -B -m unittest`로 아래 세 통합 검사만 실행했고 모두 통과했다.

- `tests.integration.test_jump_animation.JumpAnimationTests.test_jump_can_lift_a_ground_attack_without_restarting_it`
- `tests.integration.test_jump_animation.JumpAnimationTests.test_air_attack_landing_can_consume_jump_at_contact`
- `tests.integration.test_jump_animation.JumpAnimationTests.test_attack_recovery_dash_uses_direction_and_keeps_last_sweep`

검격 중 Space 입력에서 상승이 시작되고 검격 클립이 이어지며 종료 뒤 낙하 모션으로 돌아갔다. 기존 공중 검격 착지와 대시 연결도 확인했다. 실제 창 플레이와 게임 전체 조작감 평가는 미확인이다.
