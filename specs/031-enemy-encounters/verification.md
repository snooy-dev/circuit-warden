# Verification: 일반 몬스터의 이동과 첫 배치

**Date** 2026-11-26

## 배치와 행동

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_power_supply_enemies tests.integration.test_power_supply_boss tests.unit.test_basic_enemy -q
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_power_supply_enemies.PowerSupplyEnemyTests.test_fan_warns_then_crosses_fixed_lane_in_both_directions -q
```

- 관련 자동 검사 50개 통과. 배치와 이동 범위의 지형·방 경계, R, 좌우 비행, 금속 먼지 복귀, 방으로 돌아왔을 때 새 예고, 콘덴서 피해와 보스를 확인했다. 비행 끝에서 멈춰 있는 팬에 활성 공격 ID가 남지 않는지 별도로 확인했다.
- 중앙 금속 먼지의 첫 시안 (2200, 2096)에서 지름길 복귀 점프가 방해됐다. 최종 위치 (2320, 2096)의 이동 범위는 x2288–2490이다. 지름길 점프 출발 x2212와 적의 중심 최서단 사이 76은 두 몸 충돌의 합 66보다 10 넓다.

## SDL 실행

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.power_supply_smoke --visible --encounters-only --output-dir tmp/warden-enemy-live
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.power_supply_smoke --output-dir tmp/warden-enemy-routes
```

- 실제 SDL 창에서 금속 먼지 검 적중, 냉각 팬 예고·비행, 콘덴서 방전·반격과 R 초기화를 확인했다.
- 고정 60Hz SDL에서 냉각 경로 84.38초, 콘덴서 경로 70.23초에 릴레이 복구와 보스 처치를 거쳐 출력에 도달했다. 냉각 경로에서 수정한 지름길 복귀 점프도 통과했다.

현재 규칙은 [기본 적 전투](../../docs/systems/basic-enemy.md)와 [진행 상태](../../docs/progress.md)에 반영했다. 전체 회귀와 사람의 난이도 평가는 실행하지 않았다.
