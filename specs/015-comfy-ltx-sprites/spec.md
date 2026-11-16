# Feature Specification: ComfyUI LTX-2.5 스프라이트 연결

**Created**: 2026-11-16
**Status**: Ready
**Input**: “2.5용 I2V 워크플로 확보해서 스프라이트 스킬에 연결해 줘”
**Design approval**: 별도 승인 없음. 세부 설정은 기술적 가정이다.
**Implementation authorization**: 위 사용자 요청으로 도구 연결·필요한 검증을 진행한다.

## Intent & Scope
설치된 로컬 LTX-2.5로 원화·동작 프롬프트를 영상으로 만들고 기존 video2dsprite 후처리에 전달한다. 공식 I2V·첫/끝 프레임 워크플로를 보존한다. 유료 서비스, 모델 추가 다운로드, 게임 코드·자산 교체, 새 캐릭터 제작은 제외한다. 실제 생성 검증은 연결 확인용 짧은 로컬 클립만 사용한다.

## Documentation Contract (mandatory)
| 기준 docs | 현재 규칙 | 변경 | 상태 | 갱신 문서 |
|---|---|---|---|---|
| docs/tooling.md | 외부 영상 인증 미구성 | 로컬 경로·복원·실패 복구 | 요청 범위 | docs/tooling.md |
| docs/progress.md | 활성 작업 | 도구 연결 상태 | 요청 범위 | docs/progress.md |
게임 규칙·기술 구조·아트 채택 기준·루트 README는 바꾸지 않는다.

## User Scenarios & Testing (mandatory)
### User Story 1 - 로컬 영상 연결 (Priority: P1)
**Why this priority**: 기존 스프라이트 처리에서 설치 모델을 사용해야 한다.
**Independent Test**: 서버의 모델·노드를 확인하고 짧은 영상을 생성·디코딩한다.
**Acceptance Scenarios**:
1. **Given** 원화·프롬프트, **When** 로컬 생성, **Then** 영상·경로·모델·해시·실제 길이를 받는다.
2. **Given** 끝 포즈, **When** 생성, **Then** 첫/끝 프레임 워크플로를 선택하고 사용 여부를 보고한다.
3. **Given** 기존 sprite_set 작업, **When** 로컬 생성기를 지정, **Then** 동일한 결과 계약으로 후처리에 전달한다.
### User Story 2 - 실패 확인과 재개 (Priority: P1)
**Why this priority**: 긴 작업의 오류가 중복 생성·덮어쓰기로 이어지면 안 된다.
**Independent Test**: HTTP 클라이언트 대역과 기존 호출기로 오류·시간 초과·재개를 검사한다.
**Acceptance Scenarios**:
1. **Given** 서버/모델/노드 누락, **When** 실행, **Then** 구체적 오류로 종료하며 유료 경로로 전환하지 않는다.
2. **Given** 제출 후 시간 초과, **When** 재개, **Then** 재제출 없이 결과를 회수한다.
3. **Given** 기존 출력 폴더, **When** 새 생성, **Then** 덮어쓰지 않는다.
### Edge Cases
이미지·프롬프트 오류, 미지원 해상도/길이, 노드/모델 누락, 제출 응답 유실, 시간 초과, 출력 누락, 서버 중단, 동시 사용자 작업.

## Requirements (mandatory)
### Functional Requirements
- **FR-001**: 공식 원본·고정 버전·해시·라이선스와 API용 변경 이유를 보존한다.
- **FR-002**: 원화·프롬프트·길이·해상도·선택 끝 포즈를 받아 기존 생성기 호환 영상 결과를 출력한다.
- **FR-003**: 입력·모델·노드를 검증하고 점검/준비만으로 GPU 작업을 제출하지 않는다.
- **FR-004**: 작업 ID와 입력 정보를 저장하고 재개는 중복 제출 없이 처리한다. 기존 산출물을 덮어쓰지 않는다.
- **FR-005**: 로컬 서버만 사용하고 유료 fallback·전역 중단·전체 대기열 삭제를 하지 않는다.
- **FR-006**: 스프라이트 스킬에 로컬 경로를 연결하고 스킬 갱신 후 재적용할 수 있게 한다.
- **FR-007**: 서버·짧은 생성/디코딩·기존 생성기 계약·실패 처리를 검증하고 docs를 갱신한다.
### Constraints
게임/도구 환경을 분리한다. 새 의존성·서버·DB를 추가하지 않고 ComfyUI 설정·사용자 워크플로를 덮어쓰지 않는다.

## Success Criteria (mandatory)
- **SC-001**: 원화부터 디코딩 가능한 영상까지 1회 이상 성공하고 기존 생성기가 결과를 받아들인다.
- **SC-002**: 점검·준비·재개 시 추가 생성 0회이며 실패를 성공으로 표시하지 않는다.
- **SC-DOC**: 도구 기준·스킬 안내·활성 상태·검증 결과가 일치한다.

## Assumptions & Open Decisions
기본 주소 http://127.0.0.1:8188, 설치 모델 LTX-2.5 22B Distilled INT8, 24fps다. 모델 프레임 규격에 맞춰 길이를 반올림하고 요청/실제를 남긴다. 프롬프트 자동 확장은 끈다. 미술 승인은 생성 성공과 별개다.

