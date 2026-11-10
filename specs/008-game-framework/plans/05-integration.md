# Implementation Plan: P5 — 게임 화면 통합·최종 검증

**현재 실행 근거**: 2026-11-10 사용자가 각 계획을 새 채팅에서 구현하고 독립 계획을 별도 워크트리에서 병렬 진행하도록 지시했다. 이전 검토 대기는 해제됐다. P1/P2부터 착수하고 P3는 P1/P2, P4는 P3, P5는 P1~P4의 검증된 커밋에 의존한다. 상세 기술 선택은 제안 기본값으로 구현하며 별도 사용자 확정으로 과장하지 않는다.

**Branch**: feature/world-rendering | **Date**: 2026-11-10 | **Spec**: [공통 명세](../spec.md)
**Status**: 공동 수명·스냅샷·렌더 연결 자동 검증 / 통합 화면·실제 창 검사 진행 중
**Input**: [전체 계획](../plan.md), [기술 기준](../../../docs/architecture.md#게임프레임워크-계약-제안-미구현)

## Summary
Level·Canvas·Renderer와 가변 출력 엔진을 하나의 실행 화면에서 일관되게 동작시킨다.

## Technical Context
Python 3.14 + Pico2D 1.5.1, Windows. 새 의존성·외부 에셋 생성 없음. 게임 검사에는 원본 저장소 .venv/Scripts/python.exe를 명시한다. 성능 목표 수치는 아직 미정이다.

## Constitution Check
- [x] 2026-11-10 모든 계획 구현과 공유 경로 순차 인계 지시로 진행한다. 기술 기본값 구현과 게임 정책 확정은 구분한다.
- [x] 공통 Spec Kit 명세/작업 체계 안에서 범위·제외·선행 계약·검증·docs 영향을 정의했다.
- [x] 검증된 증분의 docs/verification 갱신·커밋과 PR 승인 경계를 유지한다.

## Scope & Dependencies
선행 조건: P1~P4 완료를 확인했다. P4 최종 인계 `0f4bc9f6151e1fac705499d737da01901c6b28f8`와 깨끗한 상태를 확인한 뒤 `C:/Users/Developer/.codex/worktrees/cbb2/circuit-warden`의 같은 `feature/world-rendering`을 순차 인계받았다. 기존 준비 브랜치 `feature/game-screen-integration`과 작업트리는 보존했고 문서/선행 커밋을 중복 병합하지 않았다.

요구사항 담당: FR-001~010의 연결 동작, SC-001/SC-002/SC-DOC 전체 판정.

- LevelScene이 Level·Canvas를 각각 소유하고 진입/퇴장·부분 초기화 실패를 함께 처리.
- Level·Canvas 전체 스냅샷을 모두 콜백 전에 취득해 모드→월드 객체→UI update, 월드→UI 렌더 순서를 연결.
- 통합 framework_demo.py에서 생성/삭제·레벨 왕복·출력 모드 변경·입력 변환·반투명/경계 사례를 교차 확인.
- 문서·코드·요구사항·실제 검증 대응, 기존 검사 회귀와 누락/실패 해결.

제외: 새 게임 규칙·새 렌더 기능·관리자 계층·최적화를 추가하지 않는다. 통합에 필요하다는 이유로 이전 계획의 미완료를 숨기지 않는다.

## Project Structure & Interfaces
변경 대상: game_framework.py의 LevelScene 조합부, framework_demo.py, tests/test_framework_demo.py·tests/test_scene_integration.py와 필요한 기존 회귀 테스트. 앞 계획의 오류는 해당 책임 코드에서 수정하고 검증을 갱신한다.

인계 계약: P1~P4의 책임을 다시 구현하지 않는다. P3의 월드 전용 실행과 P4의 UI 단독 검사도 유지하며 통합 시 두 스냅샷 경계·정리·출력 프레임 상태를 맞춘다.

## Verification & Completion
- GameMode가 UI를 생성/제거하는 경우까지 포함해 동일 update 신규 참여 금지·제거 제외를 확인한다.
- Level/Canvas 한쪽 초기화·정리·draw 실패에도 다른 쪽 정리와 임시 참조 해제를 확인한다.
- 기존 회귀+새 전체 자동 검사와 실제 통합 화면 검사를 실행하고 자동/실화면/사용자 확인을 구분한다.
- 미실행 환경·실패·필수 미완료가 있으면 전체 완료로 표시하지 않는다.

완료 조건: SC-001/SC-002/SC-DOC가 모두 실제 근거를 가지며 각 계획과 전체 상태가 일치한다.

## Documentation Impact (mandatory)
docs/architecture.md의 이 계획 담당 계약과 구현 상태, docs/progress.md의 다음 검토/진행 계획, [verification.md](../verification.md)의 P5 상태·실제 명령/결과/미실행을 함께 갱신한다. 실행 방법이 바뀌면 quickstart.md와 README의 관련 안내만 갱신한다. 공통 spec/data-model/contracts와 어긋나면 같은 증분에서 수정한다. 미승인 정책을 구현 사실로 확정하지 않는다.

## Tasks & Review Decisions
작업은 [공통 tasks.md](../tasks.md)의 T018~T022가 단일 기준이다. 여기에서 별도 중복 체크리스트를 운영하지 않는다. 승인된 범위의 검증된 작은 증분마다 관련 docs·검증과 함께 커밋하며 PR은 별도 승인 대상이다.

미결: 새 기능 결정은 하지 않는다. 남은 필수 환경 검증과 앞 계획의 미결 정책이 있으면 완료 판정 전에 해결한다.
