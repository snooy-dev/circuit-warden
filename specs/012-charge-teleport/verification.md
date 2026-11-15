# Verification: 전하 순간이동

상태: 2026-11-15 사용자 요청에 따른 공중 도착 상승 강화와 우클릭 자동 선택 구현·검증 완료. 조작감은 사용자 재확인 전이다. 이전 기능 검증은 Git 이력과 [014 검증](../014-baked-effects/verification.md)에 보존한다.

## 변경·동기화

feature/charge-teleport 워크트리를 재생성하고 git fetch origin 후 git merge --no-commit origin/main으로 a5f47a8→c0664f3 fast-forward했다. 미커밋 사용자 변경·충돌은 없었다. 이번 런타임 변경은 game/character.py의 TELEPORT_RISE_SECONDS 한 값(.16→.24)이다. 기존 중력·일반 점프·상단 제한·속도 비누적·대시 소모 이력·선입력은 유지한다. 새 시험값의 소유자는 [전하 시스템](../../docs/systems/charge-teleport.md)이다.

## 자동 검사

새 워크트리에 .venv가 없어 기존 프로젝트 게임 Python을 명시해 사용했다. 아래 표적4개가 모두 통과했다.

```powershell
D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest tests.unit.test_charge_teleport.ChargeTeleportTests.test_lift_apex_return_partition_and_no_velocity_accumulation tests.unit.test_charge_teleport.ChargeTeleportTests.test_lift_fits_ceiling_and_zero_headroom_falls tests.unit.test_charge_teleport.ChargeTeleportTests.test_cancel_every_action_clears_requests_and_lands tests.integration.test_charge_scene.ChargeSceneTests.test_destination_activation_and_last_valid_buffer
```

- FR-004: 정점240ms·최대59.76 상승·480ms 도착 높이 복귀, 1회/24분할 갱신 일치, 연속 이동 속도 비누적, 상단 여유5/0 제한.
- FR-003: 모든 행동 취소·선입력 제거·A/D·대시 소모 이력·착지 유지.
- FR-008: 목표 기준 활성화·마지막 유효 선입력·종료 후 재이동 유지.

## 실제 SDL·화면 관찰

```powershell
D:/GitHub/circuit-warden/.venv/Scripts/python.exe tests/smoke/charge_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/15/01a1debe-3f98-73c0-a311-5027d1c2bb2e
```

PASS: 순간이동10회·선입력2회·공격/점프/대시 취소·상승/낙하·F6/F11 선택·종료 해제. max draw=0.3ms, median draw=0.1ms는 이번 측정값이며 프레임 성능 보장은 아니다. character-charge-lift-fall.png를 열어 도착 전하 위쪽에서 낙하 전환한 모습을 관찰했다. 자동 입력/상태 검사와 화면 관찰이며 사용자 직접 플레이 평가는 아니다.

## 문서·Converge·한계

시스템/progress·012 spec/plan/tasks/data-model/quickstart를 동기화했다. Analyze에서 FR-004와 기존 상단 제한·비누적·입력 계약의 충돌이 없음을 확인했다. Converge에서 T022/T023·FR-003/004/008·코드·검증·docs를 대조했으며 남은 필수 구현 작업은 없다. 기본 조작·기술 구조·아트·게임 의도·인터페이스는 바뀌지 않아 해당 문서는 수정하지 않았다. 전체 회귀와 새 테스트 추가는 단순 값 조정 범위에 필요하지 않아 선택하지 않았다. 기존 테스트의 정점/복귀 기대값만 수정했다.

화면 위쪽 여유가 작으면 기존 제한 때문에 상승량/시간이 줄어든다. 상승 강화의 최종 조작감은 사용자 확인 전이다. 새 아트·의존성·엔진·공용 프레임워크·README 변경 및 PR 게시는 하지 않았다.

## 착지 후 우클릭 제외 해제 검증

2026-11-15 사용자 직접 테스트에서 착지 후 우클릭 무반응을 보고했다. 실제 창 입력 기록에서 button=3이 들어왔지만 마지막 전하만 활성 거리 안에 있어 제외 후 후보가0인 상황을 확인했다. 사용자 후속 지시대로 공중 제외는 유지하고 착지 즉시 해제한다. 이전 제외 구현 검증은 5580d74에 보존한다. 시작 시 작업 트리는 깨끗했고 fetch/merge 결과 Already up to date였다.

GameplayMode.after_update 마지막에서 grounded이면 last_charge를 비운다. 지상 순간이동 도착도 즉시 비우며 공중 예약 실행으로 다시 상승하면 새 도착 기록을 유지한다. 착지 모션 종료를 기다리지 않는다.

```powershell
D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest tests.integration.test_charge_scene.ChargeSceneTests.test_landing_clears_exclusion_before_landing_animation_finishes tests.integration.test_charge_scene.ChargeSceneTests.test_ground_destination_clears_exclusion_immediately tests.integration.test_charge_scene.ChargeSceneTests.test_right_click_shares_last_valid_buffer_and_destination_origin tests.integration.test_charge_scene.ChargeSceneTests.test_right_click_only_last_target_is_noop_but_left_click_still_selects tests.integration.test_charge_scene.ChargeSceneTests.test_right_click_exclusion_changes_only_on_arrival_and_clears_on_exit
```

5개 통과. FR-009: 자연 낙하 후 land 단계에서 제외 기록 해제·같은 전하 우클릭 재사용·지상 도착 즉시 해제·공중에서는 제외 유지·후보 없음 무동작·좌클릭 선택·도착 성공 때 기록 교체·장면 종료 해제. FR-008: 혼합 예약·공중 도착 기준/기록 유지.

위 SDL 명령으로 순간이동13회·선입력3회·공중 전하2→3→2 우클릭 연결·착지 후 전하2 우클릭 재사용·기존 행동 취소·F6/F11·종료를 통과했다. max draw=0.2ms, median draw=0.1ms. character-charge-right-after-landing.png를 열어 착지 후 같은 전하로 재이동해 상승하는 화면을 관찰했다. SDL 자동 입력·화면 관찰이며 사용자 직접 재검사는 아니다.

Converge: FR-009/T029~T030과 mode·표적/smoke·시스템/progress/architecture 및 012 spec/plan/contracts/quickstart를 대조했다. 남은 필수 구현 작업은 없다. 변경 링크·git diff --check를 통과했다. 기본 조작·게임 의도·창 안내는 기존 우클릭 선택 설명을 유지하므로 변경 영향이 없고 물리·엔진·자산·의존성·README는 범위 밖이다. 전체 회귀·PR 게시·사용자 직접 재검사는 미실시다. 이전에 열어 둔 게임은 코드를 다시 읽지 않으므로 재시작해야 한다.
