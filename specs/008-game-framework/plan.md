# Implementation Plan: 게임프레임워크 — 분리 계획 안내

2026-11-10 최신 인계: 독립 P1/P2만 별도 브랜치·워크트리에서 병렬 진행한다. P2 브랜치는 feature/display-management다. P3는 P1/P2 검증 커밋을 C:/Users/Developer/.codex/worktrees/cbb2/circuit-warden의 feature/world-rendering에 통합한다. 이후 P4와 P5는 별도 브랜치를 만들지 않고 같은 워크트리/브랜치를 P3 → P4 → P5 순서로 재사용한다. 선행 종료 전에 다음 쓰기를 시작하지 않으며 기존 브랜치·워크트리는 보존한다.

**현재 실행 근거**: 2026-11-10 사용자가 각 계획을 새 채팅에서 구현하고 독립 계획을 별도 워크트리에서 병렬 진행하도록 지시했다. 이전 검토 대기는 해제됐다. P1/P2부터 착수하고 P3는 P1/P2, P4는 P3, P5는 P1~P4의 검증된 커밋에 의존한다. 상세 기술 선택은 제안 기본값으로 구현하며 별도 사용자 확정으로 과장하지 않는다.

**Branch**: feature/game-framework | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)
**Status**: 구현 승인 — P1/P2 병렬 착수, P3~P5 선행 결과 대기

## Summary
사용자가 광범위해진 계획을 여러 계획으로 분리하도록 제안했다. 한 번에 객체·출력·월드 렌더링·UI를 구현하던 초안을 아래 다섯 계획으로 나눈다. 분리 자체를 기술 설계 승인이나 구현 재개로 간주하지 않는다. 현재는 2026-11-10 지시로 P1/P2를 구현하며 후속 계획은 선행 검증 커밋을 통합한다. 한 계획의 승인으로 다른 계획까지 승인됐다고 간주하지 않는다. 사용자가 여러 계획 또는 전체를 함께 승인하면 그 범위 안에서 재승인 없이 진행한다.

## Technical Context
Python 3.14 + Pico2D 1.5.1, Windows와 기존 게임 .venv 유지. 기존 001 엔진이 출발점이다. 새 엔진·의존성·외부 에셋 생성은 없다. 현재 feature/game-framework와 활성 specs/008-game-framework를 유지한다. 계획 분리만을 위해 브랜치·워크트리·활성 기능 포인터를 만들거나 바꾸지 않는다.

## Constitution Check
- [x] Spec Kit의 spec → plan → tasks → analyze → implement → docs → converge 흐름을 유지한다.
- [x] 모든 계획의 구현이 승인됐으며 P2 implement와 자동 검사를 수행했다. 다른 계획의 결과는 담당 채팅에서 인계한다.
- [x] 각 계획에 담당 범위·제외·파일·인계 계약·독립 완료 조건·검증·docs 갱신을 명시했다.
- [x] 연구·설계 근거는 보존하고 중복 작업 체계를 만들지 않는다.

## Plans & Dependencies

| 계획 | 목적 | 선행 조건 | 완료 확인 |
|---|---|---|---|
| [P1 게임 객체·레벨·규칙](plans/01-core.md) | Level/GameObject/GameMode, 생성·삭제·등록순·업데이트 | 없음 | 창 없는 수명·규칙 자동 검사 |
| [P2 창·출력 기반](plans/02-display.md) | 창/출력 픽셀·DPI·전체화면·SDL 이벤트 | 기존 엔진 | 기존 도형 장면의 크기/모드 변경·입력 확인 |
| [P3 월드 렌더링](plans/03-world-rendering.md) | 카메라 좌표·뎁스·화면 밖 제외·반투명 | P1 + P2 | UI 없는 월드 데모 |
| [P4 Canvas UI](plans/04-canvas.md) | UI 트리·논리 좌표·배율·anchor·형제 순서 | P2 + P3의 그리기 경로 | 게임 규칙 없는 UI 검사 화면 |
| [P5 통합·최종 검증](plans/05-integration.md) | 복합 수명·공동 스냅샷·실행 화면·전체 회귀 | P1~P4 | 통합 데모와 SC 전체 판정 |

권장 검토/구현 순서는 P1 → P2 → P3 → P4 → P5다. P1과 P2는 논리적으로 독립이며 전용 워크트리에서 병렬 구현한다. P3~P5는 공통 파일을 확장하므로 순차 통합한다. 독립 완료 조건은 선행 계약이 없어도 모두 구현할 수 있다는 의미가 아니다.

## Requirements Ownership

| 요구사항 | 담당 |
|---|---|
| FR-001~003 | P1. Level/Canvas 공동 순회는 P5 |
| FR-004 | P1 객체·P3 월드 장면·P4 UI 정리, P5 복합 실패 |
| FR-005 | P3 월드, P5 실행 화면 통합 |
| FR-006 | 각 계획의 검증 근거, P5 전체 판정 |
| FR-007 | P3 월드 이미지 순서, P4 UI 계층 순서, P5 두 패스 연결 |
| FR-008 | P3 월드 범위, P4 UI 범위, P5 통합 |
| FR-009 | P3 공통 알파/상태 복원, P4 UI 적용, P5 겹침 |
| FR-010 | P2 출력/입력 기반, P3 월드 투영, P4 Canvas 배율/좌표, P5 통합 |
| SC-001/002/DOC | 각 계획의 해당 부분 + P5 전체 충족 |

## Shared Design & Interfaces
[architecture](../../docs/architecture.md#게임프레임워크-계약-제안-미구현)가 목표 설계 제안, [research](research.md)가 조사 근거, [data-model](data-model.md)과 [contracts](contracts/framework.md)가 최종 결합 모델이다. 이 문서들에 모든 형식이 함께 등장해도 P1에서 미래 Canvas/Renderer/카메라까지 구현하라는 뜻이 아니다. 각 하위 계획이 도입하는 범위만 구현한다. 기존 자료 구조·좌표·반투명 제안은 분할 때문에 변경하지 않는다.

P2는 출력/리셋 정보를 제공하고 P3가 자신의 그리기 자원을 관리한다. P3의 월드 전용 LevelScene은 독립 완결하며 P5에서 Canvas 결합을 추가한다. P4의 Canvas 단독 검사에는 Level/GameMode를 강제하지 않는다. game_framework.py는 필요한 클래스가 단계별로 추가되며 새 패키지 계층을 미리 만들지 않는다.

## Documentation Impact (mandatory)
각 계획 완료까지 docs·검증·커밋을 미루지 않는다. 검증된 증분마다 담당 코드와 architecture/progress/verification을 갱신·커밋한다. quickstart/README는 실제 가능한 실행만 안내한다. 전체 spec과 연구 근거는 008에 유지하고 tasks.md를 유일한 작업 목록으로 사용한다. verification.md는 계획별 상태를 갱신하며 실행 로그를 누적하지 않는다.

## Verification & Risks
계획 분리 문서의 링크·요구사항 분담·의존 관계·보류 상태를 검사한다. P2 자동/실제 SDL 검사는 실행했으며 결과는 verification에 기록했다. 다른 계획의 런타임 결과는 담당 채팅에서 확인한다. 기존 합성 컨테이너 실험은 전체 구현 성능 근거가 아니다. 월드 화면비 정책은 P3, UI 기준 크기는 P4, 전체화면/검증 환경은 P2 검토 사항이며 P1을 막지 않는다. 실제 게임 규모·성능 예산은 미정이다. 모든 필수 미완료를 해결해야 P5에서 전체 완료를 판정한다.
