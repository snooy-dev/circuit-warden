# Implementation Plan: 일반 몬스터의 이동과 첫 배치

**Date** 2026-11-26 | **Spec** [spec.md](spec.md) | **Status** Ready

## Technical Context

맵 JSON의 첫 스폰과 이동 범위를 조정한다. 일반 적의 기존 상태·스윕·클립으로 위치 복귀와 방 재진입을 처리한다. 팬은 예고 시 통과 가능한 거리를 기존 .46초에 맞춘다. 지형·충돌·접촉 피해와 R은 현재 로직에서 확인한다.

## Constitution Check

- [x] 기존 맵 분기와 캐릭터 아트·보스 처치 조건을 기준으로 삼았다.
- [x] 맵 좌표와 복귀 속도를 조정값으로 구분했다.
- [x] 양쪽 경로 및 적별 행동을 기존 SDL 검사에서 확인하도록 계획했다.

## Documentation Impact (mandatory)

[기본 적 전투](../../docs/systems/basic-enemy.md), [진행 상태](../../docs/progress.md), [검증 기록](verification.md)에 동작과 결과를 반영한다.
