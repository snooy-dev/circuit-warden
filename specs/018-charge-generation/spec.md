# Feature Specification: 기술과 환경의 전하 생성

**Created**: 2026-11-23
**Status**: Ready
**Input**: 워든의 기술과 환경에서 전하 생성, 변하는 전하 배치, 순간이동 후 전하 소멸.
**Design approval**: 생성원 두 종류, 가변 배치, 일회성 소비는 사용자 결정이다. 입력·배치·제한 값은 기술 시험안이다.
**Implementation authorization**: 단일 플레이 레벨의 전하 생성과 기존 전투 경로 연결이 요청 범위다.

## Intent & Scope

플레이어는 주변 환경 전하의 위치를 보고 경로를 고르거나 직접 전하를 만들어 전투 위치를 바꾼다. 두 생성원은 기존 선택·선입력·이동·소멸 규칙을 공유한다. 기존 전하 아트를 재사용한다.

## Documentation Contract (mandatory)

| 기준 | 갱신 |
|---|---|
| [게임 설계](../../docs/game-design.md), [전하 시스템](../../docs/systems/charge-teleport.md) | 두 생성원, 배치와 시험값 |
| [기본 조작](../../docs/systems/basic-gameplay.md), [기본 적](../../docs/systems/basic-enemy.md) | E, R의 변화 |
| [기술 구조](../../docs/architecture.md), [진행 상태](../../docs/progress.md) | 생성 수명·좌표·검증 |

## User Scenarios & Testing (mandatory)

### User Story 1 - 커서에 기술 전하 생성 (Priority: P1)

**Independent Test**: 지상과 공중에서 E를 눌러 허용 위치에 전하를 만들고 좌클릭 또는 우클릭으로 사용한다.
1. **Given** 생성 가능한 위치에 커서가 있을 때, **When** E를 누르면, **Then** 그곳에 전하 하나가 생기고 이동 성공 후 소멸한다.
2. **Given** 이전 기술 전하가 살아 있거나 재사용 대기 중일 때, **When** E를 다시 누르면, **Then** 전하가 중복되지 않는다.

### User Story 2 - 환경에서 새 경로 열기 (Priority: P1)

**Independent Test**: 환경 전하를 사용하고 재생성 시간 경계와 재시작의 배치를 확인한다.
1. **Given** 환경 전하를 사용했을 때, **When** 대기 뒤 해당 생성 구역에 유효한 다른 위치가 있으면, **Then** 새 전하가 그 위치에 생성된다.
2. **Given** 전투를 재시작할 때, **When** R을 누르면, **Then** 기술 전하와 재사용 대기가 초기화되고 환경 전하의 시작 배치가 바뀐다.

### Edge Cases

- 커서가 창 밖, 생성 사거리 밖, 워든이나 다른 전하에 너무 가깝거나 적·지형과 겹치는 경우 생성을 거부한다.
- 막힌 환경 후보는 재시도한다. 소비한 객체에 대한 예약은 새 객체를 대상으로 바뀌지 않는다.

## Requirements (mandatory)

- **FR-001**: 살아 있는 워든은 E로 허용된 지상·공중 위치에 전하를 만들 수 있다. 기술 전하 한 개와 짧은 재사용 대기를 둔다.
- **FR-002**: 환경 구역은 여러 후보 위치를 사용하며, 재시작 및 재생성 시 다른 후보를 선택한다.
- **FR-003**: 성공한 순간이동만 전하를 한 번 소모한다. 모든 생성원에 기존 선택·선입력과 도착 검증을 공유한다.

### Constraints

- Python + Pico2D, 기존 Charge와 이미지 시트를 재사용한다.

## Success Criteria (mandatory)

- **SC-001**: SDL에서 E로 전하를 만들고 사용 후 없어짐을 확인한다.
- **SC-002**: 환경 대기 경계·다른 위치·R·막힌 위치와 기존 공중 전투를 검사한다.
- **SC-DOC**: 명세·계획·작업·검증과 현재 시스템 문서가 일치한다.

## Assumptions & Open Decisions

기술 전하 사거리는 현재 순간이동 사거리를 따르고, 동시 한 개·0.8초를 시험값으로 둔다. 환경은 전투용 다섯 구역·구역당 한 개·소모 후 2.5초를 시험값으로 둔다. 레벨별 구역·보상 또는 자원 기반 생성 조건은 후속 밸런스 결정이다.
