# Verification: 워든 전투와 일회성 전하

## 전투 규칙

- 거리 경계, 좌우 클릭, 예약 실패·소비, R, 기존 적 피해, 100ms 보호와 공중 진입→명중→공격 취소를 표적 검사했다. 실제 명령은 `.\.venv\Scripts\python.exe -m unittest tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_basic_enemy.BasicEnemySceneTests tests.unit.test_basic_enemy.EnemyChargeTests.test_teleport_guard_only_prevents_damage_before_contact_deadline`이며 24개 통과했다.
- spec·plan·tasks와 현재 game-design, 전하·기본 조작·적·architecture 문서에서 규칙과 기술 시험값을 대조했다.
- 실제 SDL 창과 새 효과 감사는 다음 증분에 포함한다. 전체 회귀와 사용자의 직접 조작감 평가는 미실행이다.
