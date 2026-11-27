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

## 시각 보정

전원 구역의 중앙 연결부를 실제 SDL 창에서 띄워 기본 공중 베기와 아래 베기를 같은 카메라 배율로 비교했다. 전용 세 자세의 손·검 자루 연결, 타격 프레임의 pixelfx 곡선, 금속 먼지 적중점의 공통 섬광과 상승을 화면에서 확인했다. 워든 몸체는 ImageGen에서 효과를 제거한 자세를 16색으로 등록했다. 아래 베기 동작과 전하 우선순위 등 관련 단위·통합 검사 6개도 통과했다.

[런타임 시트](../../assets/warden/downstrike.png) · [원본 및 효과 출처](../../assets/warden/downstrike-source/provenance.json)

## 적중 자세와 궤적 보정

후속 타이밍 조정에서 준비를 30ms로 줄이고 타격과 회수를 각각 90ms로 두었다. `python -B -m unittest tests.integration.test_downstrike -q`를 게임 가상환경에서 실행해 6개가 통과했다. 입력 20ms에는 피해가 없고 50ms 이내에는 위쪽 적에게 첫 타격과 반동이 발생했다. 이번 타이밍의 실제 창 플레이는 진행하지 못했다.

전원 구역에서 `.\.venv\Scripts\python.exe -X utf8 -B tmp/warden-downstrike-visual/preview-contact.py`로 실제 SDL 창에 공중 S+J를 입력해 연속 13프레임을 캡처했다. 오른쪽을 향한 워든이 회복 중인 금속 먼지 위에서 자세를 준비하고, 발밑으로 검을 내리고, pixelfx 전류 끝에서 적중한 뒤 상승하는 순서를 화면에서 확인했다. 적중 직후에는 45ms 히트스톱 동안 베기 자세가 유지됐으며, 갱신이 재개되면서 상승 자세로 전환됐다. 공중 대시 회복 상태도 같은 장면에서 확인했다. 이번 보정에서는 전체 자동 회귀와 게임 전체 수동 플레이를 실행하지 않았다.

## 전용 10프레임 적용

측면 원화와 동일 검 원화에서 몸체·팔·검을 등록했다. 준비 30ms, 타격 90ms, 회수 90ms의 전용 자세를 사용한다. 새 잔상은 검 끝의 경로를 따라 배치했으며 적중 정지에는 중심 타격 자세를 사용한다.

게임 가상환경에서 `python -X utf8 -B tmp/warden-pogo-motion/capture.py`로 전원 구역 실제 SDL 창을 열고 키 이벤트를 주입했다. 연속 26프레임의 왼쪽 헛베기와 오른쪽 적중을 캡처해 발밑 검 궤적과 회수, 적중 정지 후 상승을 화면에서 비교했다. 헛베기에서는 낙하를 이어가고 적중에서만 위로 튀며 사용한 공중 대시가 회복됐다. 조작감에 대한 사람의 플레이는 별도로 확인하지 않았다.
