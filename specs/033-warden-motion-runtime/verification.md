# Verification: 워든 게임용 모션 통합

**Date** 2026-11-28

## 자동 검사

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_character tests.unit.test_charge_teleport tests.unit.test_basic_enemy tests.integration.test_character_scene tests.integration.test_jump_animation tests.integration.test_dash_animation tests.integration.test_charge_scene tests.integration.test_basic_enemy tests.integration.test_downstrike -q
```

142개가 통과했다. 게임용 시트 로딩, 상태별 모션 선택과 방향, 점프·대시·검격·아래 베기·전하의 직접 영향 범위를 확인했다. (FR-001~FR-004, SC-001~SC-003)

## 실제 SDL 창

```powershell
.\.venv\Scripts\python.exe -B tests/smoke/character_smoke.py --output-dir <임시 경로>
.\.venv\Scripts\python.exe -B -m tests.smoke.combat_reimplementation_smoke --downstrike-only --output-dir <임시 경로>
```

- 캐릭터 검사 통과. 대기 접지, 좌우 이동, 좌측 대시, 지상 공격과 점프를 확인했다.
- 아래 베기 검사 통과. 시작 지점을 적 상단과 판정 도달 거리의 합보다 12월드 단위 높게 조정해 유효 접촉을 재현했다. 실제 화면에서 아래쪽 적의 적중 스파크와 워든의 상승 반동을 확인했다.
- 별도 Python 실행에서 `CharacterScene(power_supply=True)`에 직접 진입했다. 실제 SDL 2픽셀 출력으로 우향 대기, 크기와 접지를 확인했다. 장면 진입을 집중 확인하기 위해 메뉴와 컷신은 생략했다. (FR-001~FR-003, SC-001, SC-002)

## 화면에서 보이는 한계

아래 베기 적중 정지에는 새 시트의 두 번째 프레임을 쓴다. 원본 5프레임 중 검의 위치가 가장 낮은 자세다. 원본에는 발밑으로 길게 뻗는 검이 뚜렷하게 보이지 않아 수직 타격 범위와 화면의 검 궤적에 차이가 있다. 원본과 기존 판정을 유지했다.

## 문서 영향

[아트 기준](../../docs/art-direction.md#게임에서-사용하는-캐릭터-자산), [기술 구조](../../docs/architecture.md), [기본 게임플레이](../../docs/systems/basic-gameplay.md), [진행 상태](../../docs/progress.md), [이전 시트의 출처 안내](../../assets/warden/README.md)를 구현에 대조했다. 게임 의도와 전투·전하의 조작 규칙은 기존 시스템 기준을 적용한다. (SC-DOC)

## 사용자 직접 확인과 검사 범위

사용자 직접 플레이와 조작감 평가는 아직 이루어지지 않았다. 전체 회귀 검사는 요청 범위에 따라 생략했다.
