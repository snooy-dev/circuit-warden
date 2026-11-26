# Verification: 첫 보스 전원 조립체

## 공유 전투 판정

`.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy tests.unit.test_collision tests.integration.test_power_supply_enemies`에서 기존 훈련장·전원 구역의 검, 돌진, 접촉, 보호와 R 검사 53개가 통과했다. [기술 구조](../../docs/architecture.md)에 두 축의 상대 이동을 기록했다. 보스 통합과 직접 창 검증은 다음 증분에서 진행한다.

## 전원 조립체와 출력

| 범위 | 실제 검사와 결과 |
|---|---|
| FR-001~FR-004 | `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy tests.unit.test_collision tests.integration.test_power_supply_enemies tests.integration.test_power_supply_boss` 59개 통과. 기존 일반 적 배치·판정 외에 케이블 방향 고정, 전기탄의 연속 접촉과 단일 피해, 공중 보스 아래 통과 가능 고도, 지상 검의 높이 제한, 착지 면적, 퇴각·셔터·R을 확인했다. |
| SC-001, SC-002 | `.\.venv\Scripts\python.exe -B -m tests.smoke.power_supply_smoke --boss-only --visible --output-dir .local-tools/power-supply-boss/visible-final` 통과. 실제 1280×720 창에서 초기 시험 위치를 잡고 SDL 키로 복구, 닫힌 동쪽 문, 세 패턴, 검 8회 적중과 퇴치, 출력, R을 확인했다. |
| SC-002 | `.\.venv\Scripts\python.exe -B -m tests.smoke.power_supply_smoke --output-dir .local-tools/power-supply-boss/routes-final` 통과. 가상 60Hz SDL 키·마우스 입력으로 흡기실부터 냉각 경로와 콘덴서 경로의 복구 및 보스 처치, 출력과 R을 연속 실행했다. 두 경로의 일반 적 8개체는 모두 생존했다. |
| 에셋 | ImageGen 원화와 Forge hi-bit 19색 기본 몸체를 작업 기준에 맞췄다. 몸체 15셀과 탄 4셀의 이진 알파·잘림 0과 SHA-256을 확인했다. `node .local-tools/pixelfx/tools/check.mjs lightning/ball-lightning lightning/thunderclap`에서 효과 2개 통과, 경고 0. [출처](../../assets/enemies/power-assembly.provenance.json). |
| SC-DOC | [게임 설계](../../docs/game-design.md#첫-레벨-전원-구역), [보스 전투](../../docs/systems/basic-enemy.md#첫-보스-전원-조립체), [아트 기준](../../docs/art-direction.md#전원-조립체-보스), 기술 구조와 021·025의 최신 출구 조건을 대조했다. |

경로의 연속 조작과 실제 창의 시각 확인을 구분했다. 전체 회귀와 사용자 직접 미술·난이도 평가는 진행하지 않았다.
