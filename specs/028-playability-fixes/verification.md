# Verification: 첫 레벨 플레이 결함 개선

**Date** 2026-11-26

## 표적 통합 검사

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_power_supply_flow tests.integration.test_jump_animation.JumpAnimationTests tests.integration.test_charge_scene tests.integration.test_resize_input tests.unit.test_ui_input -q
.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_charge_teleport -q
```

통합·UI 검사 38개와 순간이동 단위 검사 5개 모두 통과. Escape와 Skip 클릭 다음 D 입력, 격벽과 하단 밖 도착, 유효 전하 활성, 우클릭·예약·소모, 전하 밝기 전환, 가변 점프·착지·발판 유예를 확인했다. 기존 점프 검사는 공중 공격의 70% 재생 중 정점에서 낙하로 전환하고 검격 종료 뒤 낙하 프레임을 표시하는 동작에 맞췄다.

## 전원 구역

```powershell
.\.venv\Scripts\python.exe -B -m tests.smoke.power_supply_smoke --visible --boss-only --output-dir $bossProof
.\.venv\Scripts\python.exe -B -m tests.smoke.power_supply_smoke --output-dir $routeProof
.\.venv\Scripts\python.exe -B -m tests.smoke.power_supply_smoke --visible --output-dir tmp/warden-playability
```

- 실제 창에서 닫힌 셔터, 보스 세 패턴·검 처치, 출력 완료 문구, 체력 0에서 쓰러짐 문구, R 초기화를 확인했다.
- 고정 60Hz SDL 실행에서 두 분기 모두 릴레이 복구→보스→출력 도달 및 R 초기화를 확인했다. 일반 적의 검 적중·팬 비행·콘덴서 방전도 통과했다.
- 최초 실시간 검사에서 상부 분기 검사 좌표 x2016에서 x2220으로 뛰면 발판을 놓치는 경우가 재현됐다. 시작점을 같은 발판 안쪽 x2050으로 옮겼다. 맵 지형·점프 수치는 기존대로 사용한다.
- 보정 후 실제 SDL 창에서 하부·상부 경로를 각각 90.41초와 74.81초에 출력까지 통과했다. 출력 화면 캡처에서 R 안내를 읽을 수 있었고 일반 적 전투와 초기화 검사도 통과했다.

## 문서 영향

컷신 인계는 [게임 설계](../../docs/game-design.md#오프닝-스토리-컷신), 전하 도착 조건은 [순간이동 규칙](../../docs/systems/charge-teleport.md), 화면 복귀 안내는 [기본 적 전투](../../docs/systems/basic-enemy.md)에 반영했다. [진행 상태](../../docs/progress.md)에 현재 적용 범위를 기록했다. 전체 회귀와 사람의 난이도·조작감 평가는 실행하지 않았다.

## 전하 선택과 마지막 목적지 안내

게임 가상환경에서 `python -B -m unittest`로 `ChargeSceneTests`의 겹친 전하 두 경우와 연쇄 순간이동, `PowerSupplyBossTests.test_gate_requires_both_relay_and_boss_and_resets`를 실행해 4개가 통과했다. 기준점에 겹친 전하만 있을 때 이동하지 않고, 다른 유효 전하가 있으면 그쪽으로 이동했다. 보스 처치 뒤 출력 안내가 나타나고 출력 완료 뒤 종료되는 것을 확인했다. 이번 변경의 실제 창 플레이는 하지 않았다.

## 두 분기와 일반 적의 실제 창 재확인

게임 가상환경에서 `python -X utf8 -B -m tests.smoke.power_supply_smoke --visible --output-dir tmp/warden-pogo-motion/full-stage`를 실행했다. 냉각 경로 85.14초, 콘덴서 경로 70.30초에 릴레이와 보스를 거쳐 출력에 도달했다. 두 경로를 합쳐 구현된 11개 방을 통과했고, 일반 적 검 적중, 팬 예고·비행, 콘덴서 예고·방전 피해, R 초기화가 통과했다. 입구, 중앙 갈림길, 냉각 굴뚝, 진단 고층, 보스 발사, 출력 장면의 실제 화면을 비교했다. 입력은 실행 도구가 전달했으며 사람의 조작감과 접근성 평가는 포함하지 않았다.
