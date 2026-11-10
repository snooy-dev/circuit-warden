# Implementation Plan: P1 — 게임 객체·레벨·규칙

**현재 실행 근거**: 2026-11-10 사용자가 각 계획을 새 채팅에서 구현하고 독립 계획을 별도 워크트리에서 병렬 진행하도록 지시했다. 이전 검토 대기는 해제됐다. P1/P2부터 착수하고 P3는 P1/P2, P4는 P3, P5는 P1~P4의 검증된 커밋에 의존한다. 상세 기술 선택은 제안 기본값으로 구현하며 별도 사용자 확정으로 과장하지 않는다.

**Branch**: feature/framework-p1 | **Date**: 2026-11-10 | **Spec**: [공통 명세](../spec.md)
**Status**: P1 구현·자동 검증 완료 — 전체 프레임워크 완료와 구분
**Input**: [전체 계획](../plan.md), [기술 기준](../../../docs/architecture.md#게임프레임워크-계약-제안-미구현)

## Summary
창을 열지 않고 객체를 생성·갱신·제거하며 레벨별 규칙을 실행할 수 있다.

## Technical Context
Python 3.14 + Pico2D 1.5.1, Windows. 새 의존성·외부 에셋 생성 없음. 게임 검사에는 원본 저장소 .venv/Scripts/python.exe를 명시한다. 성능 목표 수치는 아직 미정이다.

## Constitution Check
- [x] 2026-11-10 새 채팅 구현 지시를 근거로 P1을 실행했다. 상세 게임 정책 확정과 구분했다.
- [x] 공통 Spec Kit 명세/작업 체계 안에서 범위·제외·선행 계약·검증·docs 영향을 정의했다.
- [x] 검증된 증분의 docs/verification 갱신·커밋과 PR 승인 경계를 유지한다.

## Scope & Dependencies
선행 조건: 기존 엔진과 무관하게 단독 검증 가능. P2~P5에 의존하지 않는다.

요구사항 담당: FR-001~004의 월드 소유·규칙·전달 수명.

- GameObject, Level, GameMode와 초기 배치. Level의 증가 ID dict·등록순·일회 등록 수명.
- 입력 이벤트/update 전달 전 스냅샷, 모드→객체 호출, 생성/삭제 반영 경계와 재진입 거부.
- 초기화·정리 실패, 반복 제거, 종료 중 등록 거부, 레벨 재진입 시 새 객체 구성.

제외: Renderer·RenderItem·Camera·Canvas·UI·창 크기/전체화면·SDL은 구현하지 않는다. 미래 객체의 빈 필드나 연결점을 미리 만들지 않는다.

## Project Structure & Interfaces
변경 대상: game_framework.py의 core 클래스, tests/test_game_framework.py의 순수 규칙 검사. engine.py와 main.py는 변경하지 않는다.

인계 계약: Level의 소유 조회와 입력/update/열기/닫기 계약을 제공한다. 후속 렌더링은 이 등록순 조회를 소비한다. 단계 스냅샷의 소유/검증 규칙을 유지하며 Canvas 결합은 P5에서 한다.

## Verification & Completion
- 순서·재등록 거부·자기/다른 객체 제거·규칙 격리·부분 실패를 창 없는 자동 검사로 확인한다.
- 객체 생성/제거 콜백이 예외를 내도 소유 정리·남은 정리 시도와 오류 전달을 확인한다.
- 기존 엔진 회귀 검사를 통과하고 새 런타임 코드가 아직 없는 상태를 완료로 표시하지 않는다.

완료 조건: Level 두 개가 규칙·객체를 격리하고 생성/제거가 순회를 깨뜨리지 않는다. P2~P5 없이 이 완료 조건을 판정할 수 있다.

## Documentation Impact (mandatory)
docs/architecture.md의 이 계획 담당 계약과 구현 상태, docs/progress.md의 다음 검토/진행 계획, [verification.md](../verification.md)의 P1 상태·실제 명령/결과/미실행을 함께 갱신한다. 실행 방법이 바뀌면 quickstart.md와 README의 관련 안내만 갱신한다. 공통 spec/data-model/contracts와 어긋나면 같은 증분에서 수정한다. 미승인 정책을 구현 사실로 확정하지 않는다.

## Tasks & Review Decisions
작업은 [공통 tasks.md](../tasks.md)의 T003~T005가 단일 기준이다. 여기에서 별도 중복 체크리스트를 운영하지 않는다. 승인된 범위의 검증된 작은 증분마다 관련 docs·검증과 함께 커밋하며 PR은 별도 승인 대상이다.

미결: 업데이트 후 승패 판정 같은 구체 규칙은 제외다. UI·화면비 결정을 기다릴 필요가 없다.
