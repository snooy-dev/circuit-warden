# Verification: 전투 조작과 분기 안내

**Date** 2026-11-26

## 변경 전 재현

- 실제 SDL 이벤트에서 A와 Shift를 함께 누르면 워든이 기존 방향인 오른쪽으로 166만큼 이동했다. 검격 원본 재생 위치 198ms 부근에서 누른 Shift는 100ms 뒤 만료됐다.
- 중앙 갈림길에서 x1650 출발 점프는 아래 냉각 경로로 떨어졌고, 발판 끝 x1718에서 출발한 점프는 x1900 근처 동쪽 바닥에 착지했다.

## 표적 검사

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_jump_animation.JumpAnimationTests tests.integration.test_power_supply_flow tests.unit.test_character -q
.\.venv\Scripts\python.exe -B -m unittest tests.integration.test_charge_scene tests.integration.test_power_supply_boss -q
.\.venv\Scripts\python.exe -B -m tests.smoke.combat_reimplementation_smoke --output-dir tmp/warden-combat-feel
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.charge_smoke --output-dir $chargeProof
```

- 자동 검사 42개 통과. 지상·공중 유효타 뒤 대시, 같은 갱신의 마지막 타격, 예약 만료와 공중 1회 제약, 착지 선입력과 전원 구역 기존 조작을 확인했다.
- 전하·보스 통합 검사 27개 통과. 전하 선택·예약·취소·도착, 보스 공격과 셔터 조건을 확인했다.
- 훈련장 실제 SDL 창에서 왼쪽 검격 뒤 오른쪽 대시를 확인했다. 짧은 점프 높이/거리 79.9/130.8, 긴 점프 165.8/192.0 월드 단위를 관찰했다. 착지 직전 Space 선입력, 공중 베기와 플랫폼 착지, 벽 충돌과 R도 통과했다.
- 실제 SDL 전하 검사에서 지상·공중 전투, 회피, 전하 생성·소비·재생성과 연계, 창 전환을 통과했다. 순간이동 9회와 진행 중 예약 2회를 확인했다. 출력에는 프로젝트 밖 임시 폴더를 사용했다.

## 전원 구역

```powershell
.\.venv\Scripts\python.exe -B -m tests.smoke.power_supply_smoke --output-dir tmp/warden-route-feel
.\.venv\Scripts\python.exe -X utf8 -B -m tests.smoke.power_supply_smoke --visible --output-dir tmp/warden-route-feel-live
```

- 고정 60Hz SDL에서 새 갈림길·귀환 안내, 냉각 경로 90.58초와 콘덴서 경로 74.83초의 출력 도달, R, 일반 적 전투가 통과했다.
- 실제 SDL 창에서 냉각 경로 89.85초, 콘덴서 경로 74.16초에 각각 출력에 도달했다. 두 경로에서 릴레이·보스·R을 확인했으며 갈림길과 복구 뒤 안내를 화면 캡처로 확인했다.
- SDL 소프트웨어 렌더러 진입 확인에서 타이틀 New Game, 컷신 Escape 건너뛰기, 같은 이벤트 묶음의 D 이동을 확인했다.

## 문서 영향

공유 조작 규칙은 [기본 게임플레이](../../docs/systems/basic-gameplay.md#대시), 첫 레벨의 안내는 [게임 설계](../../docs/game-design.md#첫-레벨-전원-구역), 적용 기록은 [진행 상태](../../docs/progress.md)에 반영했다. 전투와 경로 확인은 SDL 이벤트를 주입한 실행으로 진행한다. 사람의 조작감 평가와 전체 회귀는 실행하지 않았다.
