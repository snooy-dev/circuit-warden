# Implementation Plan: 기본 적 금속 먼지 덩어리

**Date**: 2026-11-15 | **Spec**: [기본 적 전투](spec.md) | **Status**: Ready

## Summary

기존 플레이 레벨에 금속 먼지 덩어리 하나를 배치한다. 워든의 시간 분할 공격과 적의 돌진을 월드 좌표 AABB로 판정하고 체력 표시와 R 초기화를 연결한다.

## Technical Context

- **Language/Dependencies**: Python, Pico2D, 기존 transitions.
- **Runtime**: 게임 `.venv`, 도구 Python 분리.
- **Platform/Performance**: 현행 1280×720 기본 창. 워든과 적 한 마리의 상태와 판정만 갱신한다.
- **Testing**: 전투 경계와 기존 조작의 표적 자동 검사, 실제 SDL 창 검사를 수행한다.

## Constitution Check

- [x] 사용자 요청과 이번 적용 기본안을 구분했다.
- [x] 진행 상태·기획·기술 맥락과 기존 전투 커밋을 확인했다.
- [x] 문서 영향 및 실행 검증을 계획했다.
- [x] 기존 게임 환경과 프레임워크를 사용한다.

## Decisions & Alternatives

- 검 판정은 `feature/training-combat`의 `e343742`·`ebcad98`에서 옮긴다. 공격 경과 [0.10, 0.20)초, 시전자 전방 85 및 시전자 바닥 기준 높이 8~70, 적 체력 3, 피해 1, 피격 표시 0.18초를 적용한다.
- 현행 Character.update의 세부 프레임 진행을 유지한다. 활성 구간과 실제로 겹친 시점의 방향, 공격 ID와 공격 상자를 보존해 상위 업데이트가 종료된 뒤 사용할 수 있게 한다. 매 호출에 해당하는 결과만 내보낸다. 각 스윙과 각 돌진의 중복 피해를 한 번으로 제한한다.
- 적은 대기·접근·예고·돌진·회복 상태로 갱신한다. 접근 중 워든 방향을 따르고 돌진 방향은 예고 시점에 고정한다. 적의 단계별 이동 구간과 워든의 프레임 시작/끝 경로를 같은 시간에 비교한다. 워든 경로는 선형 근사이며 최초 접촉 시각으로 보호를 판정한다. 일시 보호는 워든 쪽 한 타이머로 관리한다.
- 단일 RGBA PNG를 기존 리소스 캐시에 연결한다. 128×96 캔버스, 알파 범위 (37, 25, 114, 80), 표시 높이 55, 하단 중앙 피벗 (76, 80)을 사용한다. 좌우 표시와 예고·회복의 표현은 단일 이미지를 재사용한다.

## Project Structure & Interfaces

| 경로 | 역할 |
|---|---|
| `game/character.py` | 기존 행동 시간 분할에서 활성 공격의 ID와 판정 상자를 전달하며 워든 체력·피격 보호·체력 표시를 담당한다. |
| `game/combat.py` | 선형 이동의 첫 접촉 시각과 공통 체력 표시를 제공한다. |
| `game/enemy.py` | 적 이동·시간 전이·피해·피격 표시를 담당한다. |
| `game/scene.py`, `game/mode.py` | 레벨 배치, 양방향 피해, 정지 및 R 초기화를 연결한다. |
| `assets/enemies/metal_dust.png`, `art/enemies/reference/metal-dust-concept.png` | 게임용 hibit 이미지와 원화 출처다. |
| `tests/unit/test_basic_enemy.py`, `tests/integration/test_basic_enemy.py`, `tests/smoke/basic_enemy_smoke.py` | 표적 규칙 및 실제 창 검증이다. |

자세한 상태는 [데이터 모델](data-model.md)에, 실행 순서는 [검증 절차](quickstart.md)에 기록한다. 공개 API 변경은 없다.

## Documentation Impact (mandatory)

`feature/basic-enemy`의 전용 워크트리에서 진행한다. 문서, 원화·아트, 전투 구현의 파일 담당을 분리한다. 연결 후 주 에이전트가 화면·테스트와 문서를 함께 검증하고 변경과 검증 결과를 커밋한다.

| 요구사항 | 기준 docs | 갱신할 내용 | 시점 | 검증 방법 |
|---|---|---|---|---|
| FR-001~006 | `docs/systems/basic-enemy.md`, `docs/systems/README.md`, `docs/game-design.md` | 기본 전투 규칙과 출처 | 설계 및 동기화 | 명세와 실제 규칙 비교 |
| FR-001·002 | `docs/art-direction.md`, `docs/architecture.md` | 아트 출처·판정 전이 | 적 배치와 검 판정 검사 후 | 리소스 검사와 명중 검사 |
| FR-003~006 | `docs/architecture.md`, `tests/README.md` | 양방향 피해·수명·표적 검사 | 통합 후 | unittest와 SDL 결과 |
| SC-DOC | `docs/progress.md`, `verification.md` | 현재 구현 범위와 미확인 사항 | 계획 및 구현 후 | 링크·실행 결과 대조 |

공개 README는 기능 사용 설명 변경 요청이 없으므로 유지한다.

## Verification & Risks

검 활성 구간 양끝, 긴 업데이트, 한 공격당 1회, 양방향·공중 회피, 대시 중 피격, 체력 0, R 초기화를 표적 자동 검사한다. 기존 캐릭터·장면 및 점프·대시 테스트로 입력 회귀를 확인한다. 실제 SDL에서 이미지 정렬, 체력 표시, 예고→돌진→회복, 워든 체력 0 및 R을 확인한다. 조작감과 최종 미술 판단은 사용자 직접 확인 상태를 따로 기록한다.
