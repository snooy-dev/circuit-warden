# Feature Specification: 전하 이동과 피격 피드백

**Created**: 2026-11-23
**Status**: Ready
**Input**: 실제 플레이에서 발견한 전류 끝점, 순간이동 직후 모션, 지상·공중 접촉과 피격 개선.
**Design approval**: 세 증상의 수정은 사용자 요청이다. 반동·표현 시간은 기술 시험값이다.
**Implementation authorization**: 기존 전투 장면과 워든 피격 표현을 수정한다.

## Intent & Scope

짧은 이동에서도 출발·도착과 캐릭터 위치가 읽히고, 지상·공중에서 접촉과 체력 손실을 구분할 수 있게 한다. 순간이동 사거리·일회성 소비·선입력, 돌진 피해와 검 타격은 현 규칙을 따른다. 할로우 나이트 공식 자료에서 접촉 위험을 명확히 전달하고 자세로 짧은 피격을 분리하는 방향을 참고한다. [Team Cherry의 King’s Pass 자료](https://www.teamcherry.com.au/blog/kings-pass-gameplay-playtests-conventions-team-cherrys-working-hard) · [보스 전투 데모](https://www.youtube.com/watch?v=MqHmosJcY0s).

## Documentation Contract (mandatory)

[전하 시스템](../../docs/systems/charge-teleport.md), [기본 적](../../docs/systems/basic-enemy.md), 기술 구조·아트 기준·진행 상태에 실제 규칙과 근거를 기록한다.

## User Scenarios & Testing (mandatory)

### User Story 1 - 전하 이동의 연결과 자세 (Priority: P1)

**Independent Test**: 대각선·수평 이동과 예약 이동에서 첫 화면 및 복귀 자세를 확인한다.
1. **Given** 유효한 전하를 선택했을 때, **When** 이동을 렌더하면, **Then** 전류가 출발 몸 위치에서 도착점에 이어지고 도착 자세가 해당 점에서 시작한다.
2. **Given** 공중 도착 후 상승할 때, **When** 이후 프레임을 재생하면, **Then** 현재 상승 속도에 맞는 시작 자세부터 움직이며 기존 공격·전하 입력을 받는다.

### User Story 2 - 접촉과 실제 피격 (Priority: P1)

**Independent Test**: 지상 몸통, 공중 옆면·상단, 돌진 피해와 보호 중 접촉을 비교한다.
1. **Given** 워든이 공중에서 적 상단에 내려올 때, **When** 접촉하면, **Then** 옆으로 끌려가지 않고 위로 짧게 튕긴다.
2. **Given** 적 돌진에 맞았을 때, **When** 피해가 적용되면, **Then** 진행 행동이 끊기고 별도 피격 자세·반동이 나온 뒤 지상/공중의 현재 조건으로 이어진다.

### Edge Cases

벽 옆 반동은 지형 경계를 지킨다. 보호 중 몸통 접촉은 피해나 피격 자세를 시작하지 않는다. 대시 중단 시 잔상을 정리하며 R/사망 시 이전 효과를 정리한다.

## Requirements (mandatory)

- **FR-001**: 전류 첫 프레임의 양 끝과 이동 출발·도착 표시 기준을 맞춘다.
- **FR-002**: 도착 자세부터 상승·낙하로 연결한다. 물리·공중 공격 가능 시간은 유지한다.
- **FR-003**: 공중 위쪽 접촉을 옆면과 구분하고 지상·공중 실제 피해에 명시적인 자세와 반동을 재생한다.

### Constraints

Python/Pico2D, 워든 실루엣과 현재 아트 팔레트, 충돌·스프라이트 진입점을 재사용한다.

## Success Criteria (mandatory)

- **SC-001**: 실제 SDL 수평/대각/연속 이동에서 화면의 연결과 도착 표현을 확인한다.
- **SC-002**: 지상/공중 피해, 피해 없는 접촉, 벽·보호·공중 연계를 표적 검사한다.
- **SC-DOC**: 문서, 코드, 에셋 출처 및 검증을 대조한다.

## Assumptions & Open Decisions

돌진의 피해·기존 거리 수치는 유지한다. 접촉 상단의 반동과 피격 회복은 시험값이고 사용자의 체감 평가는 별도다.
