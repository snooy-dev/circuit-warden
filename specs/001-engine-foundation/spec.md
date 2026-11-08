# Feature Specification: 기본 실행 기반

**Created**: 2026-11-08
**Status**: Approved
**Input**: 기본 실행 기반: 창·게임 루프·입력 전달·장면 전환
**Design approval**: 2026-11-08 사용자가 명세·계획 시각화 검토 후 “이 계획을 승인한다”고 확인했다.
**Implementation authorization**: 승인된 기본 실행 기반의 구현·검증 진행 허가. 게임 규칙·에셋은 제외한다.

## Intent & Scope

게임 규칙을 붙일 최소 실행 기반을 만든다. 창을 열고 입력·갱신·그리기를 반복하며 활성 장면을 교체한다. 전투·객체 관리·충돌·물리·카메라·리소스 관리자·에셋 제작은 제외한다. 도형 기반 검사 화면은 엔진 검증용이며 게임 플레이·아트가 아니다.

## Documentation Contract (mandatory)

| 기준 docs 문서·항목 | 현재 규칙/결정 | 제안 변경 | 승인·구현 상태 | 갱신할 문서 |
|---|---|---|---|---|
| docs/progress.md | 범위 확인 | 승인 범위·진행·검증 상태 | 계획 승인·검증 진행 | 동일 문서 |
| docs/architecture.md | 기술 설계 전 | 실행 흐름·장면 계약·기술 기본값 | 계획 승인·검증 진행 | 동일 문서 |
| docs/game-design.md | 게임 기획 미정 | 엔진만 승인되었음을 구분 | 게임 규칙 미승인 | 동일 문서 |
| docs/README.md, docs/workflow.md, README.md | 준비 단계 | 현재 상태·실행·테스트 안내 | 구현 후 갱신 | 해당 문서 |

systems·art-direction은 게임 규칙·에셋 변경이 없어 영향 없음. AGENTS·constitution의 허가 조건을 충족하며 정책 변경은 없다.

## User Scenarios & Testing (mandatory)

### User Story 1 - 실행과 안전한 종료 (Priority: P1)

**Why this priority**: 모든 실행의 전제다.
**Independent Test**: 검사 화면 실행과 창 닫기·종료 키를 각각 확인한다.
**Acceptance Scenarios**:
1. **Given** 환경 준비, **When** 실행, **Then** 창과 검사 도형이 표시된다.
2. **Given** 실행 중, **When** 창 닫기 또는 종료 키, **Then** 추가 갱신 없이 장면·창을 정리한다.
3. **Given** 장면 콜백 오류, **When** 예외 발생, **Then** 정리를 시도하고 오류를 호출자에게 전달한다.

### User Story 2 - 입력과 시간 기반 갱신 (Priority: P1)

**Why this priority**: 게임 동작을 연결하는 통로다.
**Independent Test**: 입력 순서·경과 시간을 자동 검사하고 실제 창에서 키·마우스와 도형 움직임을 확인한다.
**Acceptance Scenarios**:
1. **Given** 활성 장면, **When** 키·마우스 입력, **Then** 종료 요청 외 이벤트가 원래 정보·수신 순서대로 한 번 전달된다.
2. **Given** 실행 중, **When** 프레임 반복, **Then** 입력 후 시간 기반 갱신·그리기를 수행한다.

### User Story 3 - 활성 장면 교체 (Priority: P2)

**Why this priority**: 이후 메뉴·게임 화면을 독립적으로 연결한다.
**Independent Test**: 다른 도형의 두 장면을 왕복하고 진입·퇴장 횟수를 검사한다.
**Acceptance Scenarios**:
1. **Given** 활성 장면, **When** 다른 장면 요청, **Then** 프레임 경계에서 이전 장면 퇴장 후 새 장면에 진입한다.
2. **Given** 같은 프레임에 여러 전환 요청, **When** 프레임 종료, **Then** 마지막 요청만 적용하며 종료 요청이 우선한다.

### Edge Cases

창 생성 실패, 진입·입력·갱신·그리기·퇴장 오류에서 정리를 시도한다. 종료 이후 같은 묶음의 입력·갱신·그리기를 실행하지 않는다. 긴 정지 후 전달 시간을 제한하며 빠른 반복은 대기한다. 전환 퇴장 실패 시 새 장면에 진입하지 않고, 진입 실패 시 해당 장면 정리를 시도한다. 실행 중 중첩 실행은 거부한다.

## Requirements (mandatory)

### Functional Requirements

- **FR-001**: 창 생성과 정상·오류 종료 정리를 제공하며 오류를 숨기지 않는다. 기술 계약은 docs/architecture.md가 소유한다.
- **FR-002**: 입력 → 시간 기반 갱신 → 그리기를 반복하고 대기로 반복 속도를 제한한다.
- **FR-003**: 종료 이벤트는 엔진이 처리하고 나머지 입력은 원래 정보·순서대로 활성 장면에 전달한다.
- **FR-004**: 진입·퇴장과 프레임 경계의 지연 교체를 제공하고 종료를 교체보다 우선한다.
- **FR-005**: 에셋 없이 창·입력·시간 갱신·장면 왕복을 확인하는 실행 화면을 제공한다.
- **FR-006**: 제어 흐름 자동 검사와 실제 창 검증을 구분해 결과를 기록한다.

### Constraints

Python + Pico2D, 기존 .venv와 requirements.txt를 유지한다. 신규 의존성·외부 생성·비용 지출·게임 에셋 제작은 없다.

## Success Criteria (mandatory)

- **SC-001**: 실제 창에서 도형 표시·시간 변화·키·마우스 반응·장면 왕복·창 닫기·종료 키를 모두 확인한다.
- **SC-002**: 정상 순서·전환·시간 제한·오류 정리·종료 우선순위 자동 검사가 모두 통과한다.
- **SC-DOC**: docs·spec/plan/tasks·검증 결과가 일치하고 필수 미완료가 없다.

## Assumptions & Open Decisions

검사 화면 크기·프레임 제한·키 배치와 장면 전환·종료 정책은 승인된 기술 계획을 따른다. 게임 해상도·조작 설계의 확정도 아니다. 게임 규칙과 아트는 별도 후속 작업이다.
