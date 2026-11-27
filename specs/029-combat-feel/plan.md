# Implementation Plan: 전투 조작과 분기 안내

**Date** 2026-11-26 | **Spec** [spec.md](spec.md) | **Status** Ready

## Technical Context

`Character`의 기존 행동 소비와 상태 전이를 사용한다. 검격 유효 구간 끝은 현재 `ATTACK_ACTIVE_END`를 기준으로 삼는다. 대시 길이·준비·복귀, 점프 파라미터와 전하 규칙을 기준으로 삼아 회귀를 확인한다. 안내 구간은 맵 데이터, 안내 문구와 우선순위는 기존 `CharacterScene` Canvas에 둔다.

## Constitution Check

- [x] 공용 조작과 첫 레벨 안내를 현재 구현 흐름에 연결한다.
- [x] 기존 아트, 레벨 구조, 기획상 선택 가능한 양쪽 경로를 사용한다.
- [x] 조작·월드 안내의 직접 영향 범위만 자동 및 실제 SDL에서 검증한다.

## Documentation Impact (mandatory)

[기본 게임플레이](../../docs/systems/basic-gameplay.md)와 [첫 레벨 설계](../../docs/game-design.md#첫-레벨-전원-구역), [진행 상태](../../docs/progress.md)에 규칙과 확인 결과를 반영한다.
