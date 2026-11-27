# Implementation Plan: 워든 게임용 모션 통합

**Date** 2026-11-28 | **Spec** [spec.md](spec.md) | **Status** Ready

## Summary

게임용 모션 패키지를 플레이 장면의 공통 자산 로딩에 연결한다. 캐릭터의 기존 행동과 표시 진행을 대응시키고 스프라이트 교체 전후의 조작과 판정을 비교한다.

## Technical Context

- **Language/Dependencies** Python + Pico2D, 기존 `requirements.txt`.
- **Runtime** 게임 `.venv/`, 워든 모션 패키지는 `art/game-ready/warden/`.
- **Testing** 표적 테스트로 상태 경계와 행동 시간을 확인하고 SDL 플레이 장면에서 위치·방향·전환을 확인한다.

## Constitution Check

- [x] 런타임 통합 요청과 이동 속도 단계의 별도 설계 범위를 구분했다.
- [x] 기존 전투·이동 규칙과 표시 방식의 변경 범위를 구분했다.
- [x] 기준 문서 갱신과 게임 검증을 계획했다.
- [x] 기존 엔진과 장면·스프라이트 재생 경로를 사용한다.

## Decisions & Alternatives

- Git에 포함된 게임용 패키지를 제작 출력 위치에서 직접 읽는다. 이전 시트와 독립 효과가 있는 `assets/warden/`은 별도로 보관한다.
- 일반 측면 클립은 좌우 반전을 사용한다. 정면 순간이동은 반전 없이 표시한다.
- 이동·충돌·검 활성·입력 시계가 정하는 행동 시간을 유지하고, 표시의 경과 시간을 해당 자세에 대응시킨다.

## Project Structure & Interfaces

- `art/game-ready/warden/animations.json`과 상대 경로의 시트가 사용자가 지정한 게임용 패키지다.
- `game/character.py`는 기존 행동에 시트를 연결한다. `game/scene.py`는 장면 자원의 읽기와 수명을 담당한다.
- 실제 플레이 진입은 `main.py`의 기본 전원 구역과 `main.py --training`의 훈련장이다.

## Documentation Impact (mandatory)

`feature/warden-locomotion`에서 런타임 통합과 독립 문서 작업을 진행한다. 자산·게임 상태 연결을 표적 검증한 뒤 관련 코드·자산·문서·검증을 한 증분에 보존한다.

| 요구사항 | 기준 문서 | 반영 내용 | 확인 |
|---|---|---|---|
| FR-001 | [아트 기준](../../docs/art-direction.md#게임에서-사용하는-캐릭터-자산) | 게임 자산의 범위와 표시 규격 | 메타데이터와 실제 로더 |
| FR-002, FR-003 | [기본 게임플레이](../../docs/systems/basic-gameplay.md) | 행동별 화면 전환 | 장면 재생 |
| FR-004 | [기술 구조](../../docs/architecture.md) | 원본 시간과 행동 시간의 관계 | 표적 조작·시간 비교 |
| SC-DOC | [진행 상태](../../docs/progress.md) | 적용 상태, 검증 근거와 남은 확인 | [검증 기록](verification.md)과 문서 대조 |

## Verification & Risks

우선 새 게임 자산이 기존 진입점에서 로드되는지 확인한다. 정지·이동·전투·전하 경계에서 기존 동작이 이어지는지 필요한 개별 검사만 실행한다. SDL 출력으로 공통 기준점과 바뀐 자세의 표시를 관찰한다. 사용자 조작감 평가는 자동 검사 및 화면 관찰과 구분한다.
