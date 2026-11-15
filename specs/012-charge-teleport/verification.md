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

## 우클릭 자동 선택 검증

시작 시 작업 트리는 깨끗했으며 git fetch origin 및 git merge --no-commit origin/main 결과 Already up to date였다. FR-009에 따라 활성 기준점 최근접/동률 배치 순·대상 없음 무동작·동일 위치 포함·기존 선입력을 구현했다. 기존 좌클릭 선택 분기를 공유하고 우클릭만 커서 좌표/클릭 반경을 생략한다.

```powershell
D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest tests.integration.test_charge_scene.ChargeSceneTests.test_right_click_nearest_ignores_cursor_and_filters_invalid_targets tests.integration.test_charge_scene.ChargeSceneTests.test_right_click_without_target_or_valid_output_does_nothing tests.integration.test_charge_scene.ChargeSceneTests.test_right_click_shares_last_valid_buffer_and_destination_origin tests.integration.test_charge_scene.ChargeSceneTests.test_right_click_same_position_does_not_create_link tests.integration.test_charge_scene.ChargeSceneTests.test_selection_priority_overlap_reuse_and_inactive_fallback tests.integration.test_charge_scene.ChargeSceneTests.test_buffer_clears_on_focus_invalid_output_or_invalid_destination
```

6개 통과. 최초 실행에서 무효 출력 검사가 좌표 변환 도우미의 None을 풀어 쓰다 실패했다. 무효 출력 상황에는 원시 마우스 이벤트를 전달하도록 검사 코드를 수정했고 같은6개를 재실행해 통과했다. FR-009의 커서 독립·동률·범위 밖/도착 불가/파괴된 대상 제외·대상 없음·무효 출력·동일 위치·좌우 클릭 예약 교체·진행 중 도착점 기준을 검증했다. FR-002/008의 기존 선택·예약 취소도 유지됐다.

위 SDL 명령을 수정한 smoke로 재실행해 순간이동10회(우클릭3회)·선입력2회·상승/낙하·F6/F11·종료를 통과했다. max draw=0.3ms, median draw=0.1ms. 우클릭 커서는 전하와 떨어진 (-400,200)에 두었고 캐릭터 최근접 전하로 이동했다. character-charge-attack-cancel.png를 열어 공격 취소 후 도착·전류 연결을 관찰했다. 실제 사용자 직접 조작감 평가는 아니다.

Converge: FR-009/SC-004와 T024~T026을 mode/scene·검사·시스템/basic-gameplay/architecture/game-design/progress 및 012 spec/plan/contracts/quickstart와 대조했으며 남은 필수 작업은 없다. 추가/수정한 문서 상대 링크와 git diff --check를 통과했다. 문서 전체 링크 검사에서는 기존 progress의 로컬 아트 review.html 참조가 이 워크트리에 없어 실패했으며, 이번 변경의 링크만 구분해 재검사했다. 기존 로컬 아트 참조는 수정하지 않았다. 새 자산·엔진·물리·의존성·README 변경은 없고 전체 회귀는 입력 선택의 제한된 변경이므로 선택하지 않았다. 같은 위치/직전 도착 전하도 최근접이면 다시 선택되므로 다음 전하로 자동 순환하는 기능은 아니다. PR 게시·사용자 플레이 평가는 미실시다.
