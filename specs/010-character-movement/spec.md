# Feature Specification: 캐릭터 표시와 좌우 이동 검사

**Created**: 2026-11-11
**Status**: Ready
**Input**: 엔진 보완과 engine→main PR 생성 후 별도 게임 브랜치에서 idle v7·Run v4를 복사·이름 변경하고 캐릭터 이동을 구현한다. .gitattributes도 갱신한다.
**Design approval**: 상세 검사 기본값은 기술 가정이며 별도 사용자 승인으로 표시하지 않는다.
**Implementation authorization**: 사용자 구현 요청 및 중단 후 계속 지시. 선행 엔진 Draft PR #2 생성 완료. 브랜치는 feature/character-movement.

## Intent & Scope

캐릭터 하나를 실제 창에서 출력하고 좌우 이동·정지·방향 전환으로 기존 엔진과 프레임워크가 동작하는지 확인한다. 기존 잠정 승인 시트를 그대로 복사한다. 전투·검·VFX·걷기·점프·충돌·물리·카메라 추적·범용 입력 관리자는 제외한다.

## Documentation Contract (mandatory)

| 기준 docs | 제안 변경 | 상태·영향 |
|---|---|---|
| [architecture](../../docs/architecture.md) | 검사 장면 진입과 입력·애니메이션 연결 | 구현 후 갱신 |
| [art-direction](../../docs/art-direction.md) | 실제 사용 복사본 경로·출처 | 원본·잠정 승인 상태 유지 |
| [progress](../../docs/progress.md) | PR·브랜치·진행·미확인 | 즉시 갱신 |
| [game-design](../../docs/game-design.md) | 검사 기본값을 게임 규칙과 구분 | 실제 게임 규칙 변경 없음 |
| [문서 안내](../../docs/README.md) | 010 실행·검증 링크 | 갱신 |

## User Scenarios & Testing (mandatory)

### User Story 1 - 캐릭터 표시 (Priority: P1)

**Why this priority**: 조작 전에 에셋 출력·재생이 필요하다.
**Independent Test**: main 실행 시 투명 배경의 idle이 발 기준점에 표시되고 반복 재생한다.
**Acceptance Scenarios**:
1. **Given** 게임 복사본, **When** 실행, **Then** art 원본 없이 idle이 표시된다.
2. **Given** 장면 종료, **When** 다시 실행, **Then** 새 이미지 수명으로 정상 표시된다.

### User Story 2 - 지속 이동과 정지 (Priority: P2)

**Why this priority**: 입력·시간 갱신·애니메이션 연결을 실제 확인한다.
**Independent Test**: 좌우 키 유지·해제와 반대 키 조합을 자동 검사하고 실제 SDL 창에서 확인한다.
**Acceptance Scenarios**:
1. **Given** idle, **When** 방향키 유지, **Then** 해당 Run 시트로 지속 이동한다.
2. **Given** 이동 중, **When** 키 해제 또는 창 포커스 상실, **Then** 멈추고 마지막 방향 idle을 표시한다.
3. **Given** 좌우 동시 입력, **When** 한쪽만 해제, **Then** 남은 방향으로 이동한다.

### Edge Cases

같은 방향 별칭 키 두 개 유지 후 하나 해제, 반대 키 동시 입력, 반복 KEYDOWN, 포커스 상실·최소화, 좁은 창·경계 정지, 다른 실행 디렉터리, 누락/잘못된 에셋, 진입 실패 후 정리를 검사한다.

## Requirements (mandatory)

### Functional Requirements

- **FR-001**: idle v7·Run v4 좌우 PNG 3장을 변경 없이 assets/warden/idle.png·run_left.png·run_right.png로 복사하고 필요한 프레임 크기·순서·시간·기준점과 원본 출처·해시를 기록한다. 원본은 수정하지 않는다.
- **FR-002**: main에서 캐릭터 검사 장면을 실행하고 기존 엔진 도형 검사는 별도 실행 경로로 보존한다. 실행 위치와 무관하게 에셋을 찾고 종료 시 이미지를 해제한다.
- **FR-003**: 유지 키 상태와 경과 시간으로 좌우 이동하며 별칭 키·동시 반대 입력·해제를 일관되게 처리한다. 마지막 진행 방향은 정지 후 유지한다.
- **FR-004**: idle/좌우 Run의 원본 지속 시간과 발 기준점을 유지하고 같은 동작은 매 프레임 처음부터 재시작하지 않는다. 왼쪽 idle은 동일 시트 반전으로 표시한다.
- **FR-005**: 포커스 상실·최소화 시 유지 키를 비워 입력 고착을 막는다. 화면 경계에서 시트가 잘리지 않도록 위치를 제한한다. 화면이 시트보다 좁으면 중앙에 둔다.
- **FR-006**: .gitattributes에 PNG 바이너리 처리를 명시하고 게임 시트·메타데이터를 Git 관리한다. LFS나 새 의존성은 추가하지 않는다.
- **FR-DOC**: 자동 검사와 실제 창/SDL 입력 검사·사용자 직접 확인을 구분해 기록한다.

### Constraints

Python + Pico2D와 기존 이미지·렌더·장면 API를 재사용한다. 엔진 PR 생성 후 게임 브랜치에서 진행하고 main 병합은 하지 않는다.

## Success Criteria (mandatory)

- **SC-001**: 복사한 PNG 3개가 원본 SHA-256과 같고 런타임 이름에 버전이 없다.
- **SC-002**: 같은 경과 시간의 이동량이 갱신 분할과 무관하고 해제·동시 입력·포커스 상실 후 정지 검사를 통과한다.
- **SC-003**: 실제 창에서 idle·좌우 Run·전환·크기 변경·종료를 확인하고 미확인을 명시한다.
- **SC-DOC**: docs·명세·계획·작업·검증과 브랜치 상태가 일치한다.

## Assumptions & Open Decisions

첫 검사는 좌우 수평 이동만 제공한다. A/D 또는 좌우 방향키, 속도 180 논리 픽셀/초, 표시 2배, 기본 800×600, 고정 바닥선, 양쪽 입력 상쇄를 기술 기본값으로 사용한다. 원본 previewSpeed는 게임 속도로 채택하지 않는다. 최종 게임 이동 축·속도·경계 규칙과 미술 품질 평가는 미정이다.
