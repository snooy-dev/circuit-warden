# Implementation Plan: 착지·검격·피격 조작 반응

**Date** 2026-11-26 | **Spec** [spec.md](spec.md) | **Status** Ready

## Technical Context

공용 `Character`의 착지 상태 전이, SpritePlayer의 공격 재생률, 행동 선입력의 피격 예외를 수정한다. 남은 이동 시간은 실제 지면 접촉 이후 구간에서만 더한다. 검사에서 모션과 타격 판정 위치를 함께 본다. `GameplayLevel`의 기존 접점 효과가 활선 피해에서도 발생하도록 연결하고 현재 PNG와 클립을 재사용한다.

## Constitution Check

- [x] 현재 승인된 이동 경로와 아트, 가변 점프 궤적을 기준으로 삼았다.
- [x] 시간과 크기 변경을 시험값으로 구분했다.
- [x] 접촉·피격·발판 경계와 두 진행 경로의 검증을 포함한다.

## Documentation Impact (mandatory)

[기본 게임플레이](../../docs/systems/basic-gameplay.md), [기본 적 전투](../../docs/systems/basic-enemy.md), [기술 구조](../../docs/architecture.md), [진행 상태](../../docs/progress.md)의 현재 기준을 갱신한다.
