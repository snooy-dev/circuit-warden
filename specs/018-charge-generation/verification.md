# Verification: 기술과 환경의 전하 생성

## 워든 기술 증분

`.\.venv\Scripts\python.exe -m unittest tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_basic_enemy.BasicEnemySceneTests`로 26개를 통과했다. 공중 E, 좌표·범위·몸통·출력 거부, 키 반복, 동시 제한, 0.8초 경계, 소비·R·기존 공중 전투를 확인했다.

## 환경 증분 자동 검사

```powershell
.\.venv\Scripts\python.exe -m unittest tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_basic_enemy.BasicEnemySceneTests tests.integration.test_resize_input.ResizeInputTests tests.unit.test_basic_enemy.EnemyChargeTests.test_player_protection_expires_and_dead_player_can_reset tests.unit.test_charge_teleport.ChargeTeleportTests.test_distance_boundary_and_transition_reversal_partition
```

- 31개 통과. 2.5초 경계, 막힌 후보 재시도, 적 처치 뒤 재생성, 이전 객체 해제, 재시작 배치 변경, 창과 링크 수명을 확인했다. 이후 기술 전하의 우클릭 소비로 바꾼 해당 시나리오도 단독 재실행해 통과했다.
- 후보 선택을 세 단계로 고정해 기존 공중 타격과 이탈 테스트를 각각 재현했다. 3개를 통과했고, 낮은 후보와 오른쪽 위 후보의 9개 조합이 활성 거리 안에 있음을 확인했다.
- `.\.venv\Scripts\python.exe -X utf8 -B tests/performance/charge_benchmark.py --repeats 1` 통과. 과거 고정 배치 비교에서 환경 재생성을 분리했으며 양쪽 이동 12회, PNG 실행 중 업로드 0회를 확인했다.

## 실제 SDL 창

- `.\.venv\Scripts\python.exe tests/smoke/charge_smoke.py --output-dir $testOutput` 통과. 커서를 옮겨 E로 전하를 만들고 좌클릭으로 소비했다. 환경 전하를 사용한 뒤 비어 있는 화면과 다른 위치에 생성된 화면을 관찰했다. R, 공중 타격→이탈, 돌진 회피, F6/F11과 순간이동 9회·예약 2회도 확인했다. 첫 실행은 전체화면 복귀 뒤 커서 이동이 끝나기 전에 E를 입력했다. 검사에서 SDL 커서 도달을 확인한 뒤 입력하도록 보완했다.
- `.\.venv\Scripts\python.exe tests/smoke/audit_smoke.py --output-dir $testOutput` 통과. 현재 배치의 입력 좌표, F6 대기 순서와 예약 공격 첫 프레임을 확인했다.

## 대응 및 미확인

FR-001은 기술 입력·생성 제한, FR-002는 환경 배치·재생성, FR-003은 선택·예약과 소비 경로에 대응한다. docs·spec·plan·tasks·코드와 추가 링크를 대조했다. 사람의 직접 조작감과 최종 생성 밸런스는 미확인이다. 전체 회귀는 선택하지 않았다.
