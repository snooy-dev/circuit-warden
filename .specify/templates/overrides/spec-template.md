# Feature Specification: [FEATURE NAME]

> 적용 범위: 게임 기능 개발용. 반복 스프라이트 생성·보정에는 이 템플릿이나 Spec Kit 문서화 흐름을 사용하지 않는다.

**Created**: [DATE]
**Status**: Draft / Ready / Approved / Superseded
**Input**: $ARGUMENTS
**Design approval**: [실제 승인 근거 또는 별도 승인 없음. Ready는 사용자 승인 의미가 아님]
**Implementation authorization**: [개발 요청 범위·근거 또는 명시적 보류. PR 외 별도 승인 대기 없음]

## Intent & Scope

[플레이어 경험·목표·제외 범위. 미정은 미정으로 남기며 추측으로 확정하지 않는다.]

## Documentation Contract (mandatory)

| 기준 docs 문서·항목 | 현재 규칙/결정 | 제안 변경 | 승인·구현 상태 | 갱신할 문서 |
|---|---|---|---|---|
| [경로·제목] | [중복 대신 참조] | [변경] | [상태] | [경로] |

관련 docs를 먼저 읽고 설계 결정 즉시 해당 문서의 현재 내용을 갱신한다. 이 spec은 진행 중인 변경의 작업 문서이며 docs를 대체하지 않는다. 현재 선택의 이유는 짧게 남기고 과거 변경 경위는 Git으로 확인한다. 변경 없는 문서는 영향 없음의 이유를 적는다.

## User Scenarios & Testing (mandatory)

### User Story 1 - [행동/경험] (Priority: P1)

**Why this priority**: [이유]
**Independent Test**: [최소 검증 방법]

**Acceptance Scenarios**:
1. **Given** [조건], **When** [행동], **Then** [관찰 가능한 결과].

### Edge Cases

[경계값·동시 입력·상태 전이·실패 조건 등 실제 필요한 경우만.]

## Requirements (mandatory)

### Functional Requirements

- **FR-001**: [관찰 가능한 규칙. 기준 docs와 연결.]

### Constraints

- Python + Pico2D, Codex, 문서 보존·갱신 및 검증 증거 기록은 필수다.
- Agent Sprite Forge / pixelfx는 필요한 에셋 작업에만 사용한다. 스타일은 별도 결정이다.

## Success Criteria (mandatory)

- **SC-001**: [테스트 가능한 결과]
- **SC-DOC**: 관련 docs·결정·진행 상태·spec/plan/tasks·검증 결과가 일치하고 추적 가능하다.

## Assumptions & Open Decisions

[가정·사용자 미결정·검증 방법. 작업에 영향을 주는 미정은 구현 전에 해결.]
