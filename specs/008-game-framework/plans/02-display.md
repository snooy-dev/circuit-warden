# Implementation Plan: P2 — 창·출력 크기·전체화면 기반

**현재 실행 근거**: 2026-11-10 사용자가 각 계획을 새 채팅에서 구현하고 독립 계획을 별도 워크트리에서 병렬 진행하도록 지시했다. 이전 검토 대기는 해제됐다. P1/P2부터 착수하고 P3는 P1/P2, P4는 P3, P5는 P1~P4의 검증된 커밋에 의존한다. 상세 기술 선택은 제안 기본값으로 구현하며 별도 사용자 확정으로 과장하지 않는다.

**Branch**: feature/game-framework | **Date**: 2026-11-10 | **Spec**: [공통 명세](../spec.md)
**Status**: 구현 승인 — 선행 조건 충족 시 실행
**Input**: [전체 계획](../plan.md), [기술 기준](../../../docs/architecture.md#게임프레임워크-계약-제안-미구현)

## Summary
창/전체화면·DPI 변화에 맞는 실제 출력 상태와 입력 기준을 엔진이 제공한다.

## Technical Context
Python 3.14 + Pico2D 1.5.1, Windows. 새 의존성·외부 에셋 생성 없음. 게임 검사에는 원본 저장소 .venv/Scripts/python.exe를 명시한다. 성능 목표 수치는 아직 미정이다.

## Constitution Check
- [x] 계획 분리 요청과 기존 구현 보류를 구분했다. 이 문서는 구현 승인이 아니다.
- [x] 공통 Spec Kit 명세/작업 체계 안에서 범위·제외·선행 계약·검증·docs 영향을 정의했다.
- [x] 검증된 증분의 docs/verification 갱신·커밋과 PR 승인 경계를 유지한다.

## Scope & Dependencies
선행 조건: 기존 001 엔진만 필요. P1 없이 기존 검사 장면으로 검증 가능.

요구사항 담당: FR-010의 창/출력/입력 기반, FR-006의 해당 실행 증거.

- Engine의 창 모드·크기 설정과 보더리스 전체화면/복귀, 실제 window_size/output_size/viewport 조회.
- 필요한 SDL 창·렌더 리셋 이벤트 보존, 프레임 경계 출력 갱신, 0 크기/최소화/전환 실패 처리.
- 창 입력 위치→출력 픽셀 변환, 휠 이동량 구분. Pico2D y 변환과 실제 출력 높이 연결.

제외: 월드 카메라·UI 논리 배율·게임 객체·자동 레이아웃은 포함하지 않는다. 독점 해상도 변경·다중 viewport도 제외한다.

## Project Structure & Interfaces
변경 대상: engine.py, tests/test_engine.py. 필요 최소 범위의 main.py와 tests/test_demo.py를 현재 출력 크기에 맞춘다. Pico2D 설치 파일은 수정하지 않는다.

인계 계약: 후속 Renderer가 소비할 프레임별 출력 크기/viewport와 출력 무효·리셋 상태를 제공한다. 리셋의 탐지/전달은 P2, 후속 이미지 자원의 복구/재업로드는 해당 자원을 소유하는 P3의 그리기 경로가 책임진다. 실제 Scene 콜백과 기본 실행 호출은 호환을 유지한다.

## Verification & Completion
- 모의 SDL로 크기/입력 비율·0 크기·전환 실패·필요 이벤트 전달·리셋 상태를 검사한다.
- 기존 도형 검사 장면으로 창 크기 변경·전체화면/복귀·최소화 후 복구·마우스 위치 일치를 실제 확인한다.
- 가능한 실제 DPI 환경과 모의 DPI 검사를 구분한다. 실물 환경 미확인은 결과에 남긴다.

완료 조건: 게임프레임워크 없이 도형 검사 장면이 출력 크기·모드 변경 뒤 올바르게 표시되고 입력 기준이 일치한다.

## Documentation Impact (mandatory)
docs/architecture.md의 이 계획 담당 계약과 구현 상태, docs/progress.md의 다음 검토/진행 계획, [verification.md](../verification.md)의 P2 상태·실제 명령/결과/미실행을 함께 갱신한다. 실행 방법이 바뀌면 quickstart.md와 README의 관련 안내만 갱신한다. 공통 spec/data-model/contracts와 어긋나면 같은 증분에서 수정한다. 미승인 정책을 구현 사실로 확정하지 않는다.

## Tasks & Review Decisions
작업은 [공통 tasks.md](../tasks.md)의 T006~T009가 단일 기준이다. 여기에서 별도 중복 체크리스트를 운영하지 않는다. 승인된 범위의 검증된 작은 증분마다 관련 docs·검증과 함께 커밋하며 PR은 별도 승인 대상이다.

미결: 보더리스 전체화면은 미승인 권장안이다. 지원/검증할 최소 창 크기와 실제 DPI 환경을 검토한다. 월드 시야·UI 기준 크기는 이 계획의 결정이 아니다.
