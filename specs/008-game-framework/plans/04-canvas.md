# Implementation Plan: P4 — Canvas UI 구조·표시

**현재 실행 근거**: 2026-11-10 사용자가 각 계획을 새 채팅에서 구현하고 독립 계획을 별도 워크트리에서 병렬 진행하도록 지시했다. 이전 검토 대기는 해제됐다. P1/P2부터 착수하고 P3는 P1/P2, P4는 P3, P5는 P1~P4의 검증된 커밋에 의존한다. 상세 기술 선택은 제안 기본값으로 구현하며 별도 사용자 확정으로 과장하지 않는다.

**Branch**: feature/game-framework | **Date**: 2026-11-10 | **Spec**: [공통 명세](../spec.md)
**Status**: 구현 승인 — 선행 조건 충족 시 실행
**Input**: [전체 계획](../plan.md), [기술 기준](../../../docs/architecture.md#게임프레임워크-계약-제안-미구현)

## Summary
화면 크기가 변해도 UI 트리의 수명·기준점·표시 순서가 유지된다.

## Technical Context
Python 3.14 + Pico2D 1.5.1, Windows. 새 의존성·외부 에셋 생성 없음. 게임 검사에는 원본 저장소 .venv/Scripts/python.exe를 명시한다. 성능 목표 수치는 아직 미정이다.

## Constitution Check
- [x] 계획 분리 요청과 기존 구현 보류를 구분했다. 이 문서는 구현 승인이 아니다.
- [x] 공통 Spec Kit 명세/작업 체계 안에서 범위·제외·선행 계약·검증·docs 영향을 정의했다.
- [x] 검증된 증분의 docs/verification 갱신·커밋과 PR 승인 경계를 유지한다.

## Scope & Dependencies
선행 조건: P2의 출력 상태와 P3의 그리기/알파 경로를 사용한다. 복합 게임 화면 연결은 P5에서 한다.

요구사항 담당: FR-007~010의 UI 계층·좌표·그리기 부분, FR-004/006의 UI 정리·검증.

- Canvas roots/children 목록 트리, UIElement 일회 부착·하위 트리 삭제·부모 로컬 위치/숨김.
- reference_size 기반 논리 좌표·균등 배율·루트 anchor, 자기 bounds/opacity와 UI→출력 변환.
- 형제 복사본 정렬 후 전위 DFS 렌더 목록, 패널 하위 트리 연속 표시·부모 밖 자식 안 처리.
- Canvas 단독 업데이트 스냅샷·실패 정리와 framework_demo.py의 독립 UI 검사 모드.

제외: UI 입력 소비/포커스·버튼 동작·자동 레이아웃·클리핑·reparent·그룹 불투명도·게임 HUD 내용은 포함하지 않는다. Level과 Canvas의 공동 업데이트 연결은 P5다.

## Project Structure & Interfaces
변경 대상: game_framework.py의 Canvas/UIElement와 Renderer UI 경로, tests/test_game_framework.py, framework_demo.py, tests/test_framework_demo.py. engine.py 출력 계약을 복제하지 않는다.

인계 계약: Canvas는 독립 소유/스냅샷/그리기 계약을 제공하고 월드 카메라에 의존하지 않는다. UI 전용 검사 장면은 Level·GameMode를 필요로 하지 않는다. 그리기 순서와 UI update 등록순을 구분한다.

## Verification & Completion
- 하위 트리 삭제/실패·재부착 거부·전체 DFS 스냅샷·숨김 범위·형제 동률/패널 연속성을 검사한다.
- reference_size/화면비별 균등 배율·anchor·위치/크기/폰트·bounds·입력 역변환과 최소화 안전성을 검사한다.
- 독립 UI 검사 화면에서 겹친 패널·부모 이동/숨김/삭제·창 크기 변경·반투명 UI를 확인한다.

완료 조건: UI 단독 검사 화면에서 수명·좌표·형제 순서가 맞고 P5 통합 없이 검증된다.

## Documentation Impact (mandatory)
docs/architecture.md의 이 계획 담당 계약과 구현 상태, docs/progress.md의 다음 검토/진행 계획, [verification.md](../verification.md)의 P4 상태·실제 명령/결과/미실행을 함께 갱신한다. 실행 방법이 바뀌면 quickstart.md와 README의 관련 안내만 갱신한다. 공통 spec/data-model/contracts와 어긋나면 같은 증분에서 수정한다. 미승인 정책을 구현 사실로 확정하지 않는다.

## Tasks & Review Decisions
작업은 [공통 tasks.md](../tasks.md)의 T014~T017가 단일 기준이다. 여기에서 별도 중복 체크리스트를 운영하지 않는다. 승인된 범위의 검증된 작은 증분마다 관련 docs·검증과 함께 커밋하며 PR은 별도 승인 대상이다.

미결: UI 제작 기준 크기·허용 화면비/최소 크기와 root anchor 제약을 검토한다. 실제 메뉴/게임 HUD 디자인은 결정하지 않는다.
