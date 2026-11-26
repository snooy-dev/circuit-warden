# Verification: 전원 구역 몬스터

## 금속 먼지 배치와 다중 판정

- `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy tests.unit.test_collision tests.integration.test_power_supply_enemies`에서 훈련장 적, 다중 검격, 발판·장치와 배치, 돌진·반동 경계와 R 초기화 50개가 통과했다.
- [기본 적 전투](../../docs/systems/basic-enemy.md)와 [기술 구조](../../docs/architecture.md)에 복수 적 판정을 반영했다. 첫 증분의 실제 SDL 동선과 새 적의 화면은 다음 증분에서 확인한다.
