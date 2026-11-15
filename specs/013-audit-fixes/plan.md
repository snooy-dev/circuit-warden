# Implementation Plan: 감사 1~5 수정

**Date**: 2026-11-15 | **Spec**: [spec.md](spec.md) | **Status**: Ready

## Summary

예약 행동을 직접 전달해 중복 플래그를 제거하고 공격 진입 갱신의 첫 프레임을 보존한다. 대기 입력 처리 후 요청된 창 변경을 적용한다. 내부 순회 함수도 예외 시 스냅샷을 비운다. 전하 합성을 NumPy float64 연산으로 바꾸고 RGBA 동일성과 장면 전체 비용을 검증한다. 전류 래스터는 목표를 충족하면 변경하지 않는다.

## Technical Context

- **Language/Dependencies**: Python3.14 + Pico2D1.5.1 + transitions0.9.3. NumPy2.5.4는 사전 합성 실험에서 출력 동일성과 약10배 개선을 확인한 추가 의존성이다.
- **Runtime**: 게임 설치·검사는 .venv/Scripts/python.exe, 사전 배열 실험은 .local-tools/python/Scripts/python.exe로 분리한다.
- **Platform/Performance**: Windows·전하5개·연속 선택. 같은 입력 교대 측정에서 픽셀 계산 p95 30% 이상 감소,16.67ms 이하 목표. GPU 전체 FPS 보장과 구분한다.
- **Testing**: 예약 공격/표시 변경/예외 보관 회귀, 실제 PNG 합성·전류 SHA, 입력/캐릭터/장면 표적 검사. 공통 루프와 게임 입력이 함께 변하므로 마지막에 전체 unittest를 한 번 실행한다. 실제 SDL에서 공격·F6/F11·전하·종료를 관찰한다.

## Constitution Check

- [x] 요청한5개 수정·검증·로컬 커밋 범위만 진행한다.
- [x] 기술 구조·기본 조작·전하 기준을 확인했고 게임 규칙·자산은 유지한다.
- [x] 문서 갱신·검증·증분 커밋을 계획했다.
- [x] 다른 엔진·서버·자체 C DLL 빌드 체계를 추가하지 않는다.

## Decisions & Alternatives

공격 시작 뒤 남은 시간을 버리는 기존 즉시 공격 계약을 예약 공격에도 적용한다. 베기만 앞당겨 첫 프레임을 누락시키지 않는다. 표시 요청은 대기 이벤트를 기존 표시 기준으로 전달한 뒤 update/draw 전에 적용하고, 종료 시 적용하지 않는다. 내부 순회 finally는 목록 참조만 끊고 예외 자체는 보존한다. NumPy는 기존 산술 순서·float64·반올림을 유지하며 프레임·색·알파 양자화는 제외한다. 전류 자체는 먼저 유지하고 부족할 때만 출력 동일성 조건으로 추가 개선한다.

## Project Structure & Interfaces

- game/character.py, tests/unit/test_input_buffer.py, tests/unit/test_charge_teleport.py, tests/integration/test_character_scene.py: 행동 전달·첫 프레임.
- engine/loop.py, tests/unit/test_engine.py, tests/integration/test_charge_scene.py: 표시 전환 전 클릭.
- game_framework/world.py, game_framework/ui.py, tests/unit/test_game_framework.py: 예외 참조 정리.
- game/charge.py, requirements.txt: 배열 합성. tests/fixtures/charge_composition.json과 tests/performance/charge_benchmark.py는 기존 출력 해시와 동일 조건 비교를 제공한다.
- docs/architecture.md, docs/progress.md, tests/README.md와 이 기능 문서. 루트 README·PNG·tmp는 수정하지 않는다.

## Documentation Impact (mandatory)

feature/audit-fixes는 현재 코드에서 분기했고 최신 origin/main이 이미 포함됐다. 동일 checkout에서 파일 담당을 분리하며 같은 파일을 동시에 쓰지 않는다. gpt-6.1-sol/high가 캐릭터·엔진·성능을 독립 담당한다(시간 경계·출력 동일성 위험). 주 에이전트는 수명·의존성·문서·통합·커밋을 맡는다.

| 요구사항 | 기준 docs | 내용 | 시점 | 검증 |
|---|---|---|---|---|
| FR-001/005 | architecture.md | 단일 판정·공격 첫 갱신 | 증분1 | 입력·재생 후 커밋 |
| FR-002/004 | architecture.md | 입력/표시 순서·스냅샷 해제 | 증분2 | 루프·약한참조 후 커밋 |
| FR-003 | architecture.md, tests/README.md | 배열 합성·성능 명령 | 증분3 | 출력·교대 벤치·SDL 후 커밋 |
| FR-006/SC-DOC | progress.md, verification.md | 결과·미확인·범위 | 각 증분 | diff·자산 해시·converge |

## Verification & Risks

기준 해시는 변경 전 구현에서 생성하며 검사 통과를 위해 덮어쓰지 않는다. 같은 입력·자산의 전후 교대 측정과 자동·SDL 화면·사용자 조작감의 구분을 verification에 기록한다. 게임 환경 설치 후 사전 NumPy 실험을 재검증한다.
