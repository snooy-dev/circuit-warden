# Feature Specification: PNG 효과 재생

**Created**: 2026-11-15
**Status**: Ready
**Input**: pixelfx 효과를 PNG로 구워 성능 개선.
**Design approval**: 색·굵기·광륜·타이밍을 유지하면서 PNG 회전·조합의 미세 차이를 사용자가 허용했다. 샘플 간격은 기술 가정이다.
**Implementation authorization**: 이번 개발 요청과 앞선 검증·커밋 지시. 런타임 통합이므로 Spec Kit 적용.

## Intent & Scope

전하·전류의 실행 중 픽셀 생성을 PNG 재생으로 대체한다. 캐릭터·베기·대시 원본과 이동·입력·순간이동 규칙을 유지한다. 새 디자인·엔진 교체·PR/push 제외.

## Documentation Contract (mandatory)

| 기준 docs | 현재 | 변경 | 상태 | 갱신 |
|---|---|---|---|---|
| docs/architecture.md | CPU 합성·래스터 | PNG 재생·공유 수명 | 구현 요청 | 구현 후 |
| docs/art-direction.md | 승인 전하·전류 | 원본 유지·게임용 파생본·미세 차이 허용 | 사용자 결정 | 구현 후 |
| docs/tooling.md | 게임 NumPy | 생성 도구에서만 사용 | 계획 | 구현 후 |
| docs/progress.md | 감사 완료 | 현재 작업·검증 | 진행 | 단계별 |

게임 설계·시스템의 조작 규칙과 루트 README는 변경하지 않는다.

## User Scenarios & Testing (mandatory)

### User Story 1 - 전하 전환 (Priority: P1)

**Why this priority**: 지속적인 합성 제거.
**Independent Test**: 안정 상태·중간 반전·공유 위상·종료 확인.
**Acceptance Scenarios**:
1. **Given** 전환 중, **When** 방향이 바뀌면, **Then** 상태값·속도·위상은 이어지고 가까운 PNG를 표시한다.
2. **Given** 안정 상태, **When** 재생하면, **Then** 원본 프레임이 유지된다.

### User Story 2 - 순간이동 전류 (Priority: P1)

**Why this priority**: 남은 CPU 래스터 제거.
**Independent Test**: 가로·세로·대각·역방향·짧은 거리의 끝점·첫 프레임·100ms 수명 확인.
**Acceptance Scenarios**:
1. **Given** 유효한 두 위치, **When** 순간이동하면, **Then** 양 끝점을 기존 시간으로 연결한다.
2. **Given** 연속 입력·장면 종료, **When** 효과가 소멸하면, **Then** 공유 자산을 안전하게 재사용·해제한다.

### Edge Cases

같은 위치·1px 미만 거리, 범위 경계, 역방향, 중간 반전, 긴 dt, PNG 누락·부분 로딩 실패, 반복 종료.

## Requirements (mandatory)

### Functional Requirements

- **FR-001**: 실행 중 전하·전류 픽셀 생성과 프레임별 텍스처 업로드 없이 PNG를 재생한다.
- **FR-002**: 전하 안정 상태 원본·24fps 위상·전환 상태/속도를 유지한다. 표시값만 유한 단계로 선택한다.
- **FR-003**: 전류 색·굵기·광륜·끝점·첫 프레임·100ms 수명을 유지하며 허용된 미세 차이를 보고한다.
- **FR-004**: 재현 가능한 생성기와 공유 로딩·실패/종료 해제를 제공한다.
- **FR-005**: 동일 장면 전후 시간·이미지 메모리·로딩 비용과 실제 창을 검사한다.

### Constraints

Python + Pico2D, 원본 pixelfx·라이선스 보존. 불필요해진 게임 NumPy 제거. 사용자 점프 PNG8개·tmp 보존.

## Success Criteria (mandatory)

- **SC-001**: 측정 장면에서 실행 중 효과 픽셀 생성·업로드 0회.
- **SC-002**: 동일 장비·시나리오 p95가 기존 NumPy 구현보다 감소하고16.67ms 이내. 기술 목표이며 타 장비 보장은 아니다.
- **SC-003**: 자동 검사와 방향별 실제 창 관찰 통과, 메모리·로딩 비용 보고.
- **SC-DOC**: docs·명세·코드·검증이 일치한다.

## Assumptions & Open Decisions

전하 표시33단계와 길이별 전류 PNG를 초기 기술 가정으로 삼고 시각 검사로 조정한다. 픽셀 일치는 안정 상태에만 요구한다. 게임 규칙은 바꾸지 않는다.
