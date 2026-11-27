# Verification: 전원 구역 몬스터

## 금속 먼지 배치와 다중 판정

- `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy tests.unit.test_collision tests.integration.test_power_supply_enemies`에서 훈련장 적, 다중 검격, 발판·장치와 배치, 돌진·반동 경계와 R 초기화 50개가 통과했다.
- [기본 적 전투](../../docs/systems/basic-enemy.md)와 [기술 구조](../../docs/architecture.md)에 복수 적 판정을 반영했다. 첫 증분의 실제 SDL 동선과 새 적의 화면은 다음 증분에서 확인한다.

## 구역별 몬스터와 동선

| 범위 | 방법과 결과 |
|---|---|
| FR-001~FR-005, SC-001 | `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy tests.unit.test_collision tests.integration.test_power_supply_enemies` 53개 통과. 9개체의 지형·바닥·조작 구역, 동일 스윙의 개체별 피해, 팬의 양방향 이동, 콘덴서 예고와 실제 방전 범위, 점프·순간이동 보호, 전원 구역·훈련장 R을 확인했다. |
| FR-004, SC-002 | `.\.venv\Scripts\python.exe -B -m tests.smoke.power_supply_smoke --output-dir .local-tools/power-supply-enemies/route-verified` 통과. 가상 60Hz SDL에 키·마우스 입력을 주입했다. 냉각 경로 77.57초와 콘덴서 경로 61.67초 모두 적 9마리를 살려 둔 상태로 기존 복구·부하 시험실·출력까지 도달했다. 선택 해치와 중앙 귀환 지름길도 확인했다. |
| FR-002~FR-005, SC-002 | `.\.venv\Scripts\python.exe -B -m tests.smoke.power_supply_smoke --visible --encounters-only --output-dir .local-tools/power-supply-enemies/visible-final` 통과. 실제 1280×720 창의 훈련용 재현 위치에서 키로 금속 먼지에게 피해를 주고, 팬의 예고·비행, 콘덴서의 예고·방전 피해, R 복원을 확인했다. 두 분기 전체는 위 가상 60Hz SDL 검사에서 연속 조작했다. |
| 기본 진입 | `.\.venv\Scripts\python.exe -B .local-tools/power-supply-enemies/verify-new-game.py` 통과. 실제 타이틀에서 Enter로 New Game을 열었을 때 적 9마리가 등록되며 흡기실은 비어 있고, 오프닝 Skip이 조작을 넘긴다. |
| 에셋 | 내장 ImageGen 원화 2개와 hi-bit 가공 PNG를 확인했다. 팬 5셀, 콘덴서 10셀은 이진 알파이며 잘림이 없다. 원화·프롬프트·팔레트·런타임의 SHA-256은 [제작 정보](../../assets/enemies/field-enemies.provenance.json)와 일치한다. pixelfx `node .local-tools/pixelfx/tools/check.mjs lightning/thunderclap` 1개 통과, 경고 0. |
| SC-DOC | [게임 설계](../../docs/game-design.md#첫-레벨-전원-구역), [기본 적 전투](../../docs/systems/basic-enemy.md#전원-구역의-새-몬스터), [아트 기준](../../docs/art-direction.md#전원-구역의-새-몬스터), 기술 구조, 진행 상태와 021·025의 범위를 대조했다. |

Team Cherry의 [공식 교차로 소개](https://www.teamcherry.com.au/blog/the-forgotten-crossroads-a-hollow-knight-tour)와 [출시판 실전 영상 7:45 직후](https://www.youtube.com/watch?v=LNjXu87zmzg&t=465s)를 확인했다. 착지 직후의 여백, 낮은 통로의 지상 교전, 발판 높이가 달라지는 공간의 공중 교전을 전원 구역에 적용했다.

실제 게임 장면에서 두 새 적의 외곽과 위험 표지, 금속 먼지의 검 접점을 확인했다. 사용자의 직접 미술·난이도 평가는 남아 있다. 요청 범위의 표적 검사만 실행했다.
