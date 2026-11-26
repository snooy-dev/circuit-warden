# Verification: 공중 아래 베기

**Date** 2026-11-26

## 표적 자동 검사

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_downstrike tests.integration.test_jump_animation.JumpAnimationTests tests.unit.test_input_buffer tests.unit.test_basic_enemy tests.integration.test_power_supply_boss tests.integration.test_charge_scene -q
```

관련 검사 92개 통과. 아래 베기의 키보드와 마우스 입력, 프레임 안의 첫 유효 접촉, 일반 적과 보스 피해, 공중 대시 회복, 발판에 의한 차단, 헛스윙·착지·순간이동 종료, 지상 공격과 전하 우선순위를 확인했다.

## 실제 SDL 화면

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.combat_reimplementation_smoke --output-dir tmp/warden-downstrike
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.combat_reimplementation_smoke --downstrike-only --output-dir tmp/warden-downstrike
```

실제 훈련장 창에서 SDL 키 입력으로 아래 베기를 발동하고 발밑 전기 궤적·접점 방전·상승과 공중 대시 회복을 확인했다. 전체 훈련장 시나리오는 재시도에서 가변 점프, 착지 선입력, 지상·공중 검격, 벽 정지와 R 및 아래 베기를 통과했다. 다른 시도에서는 기존 회복 대시·짧은 점프 단계가 간헐적으로 실패했다. 아래 베기만 실행하는 검사에서도 통과했다.

아래 베기의 전기 표시를 별도로 제작했다. 워든 몸체는 공중 자세 프레임을 사용한다. 조작과 피해는 [기본 게임플레이](../../docs/systems/basic-gameplay.md)와 [기본 적 전투](../../docs/systems/basic-enemy.md)에 반영했다. 전체 회귀와 사람의 조작감 평가는 실행하지 않았다.
