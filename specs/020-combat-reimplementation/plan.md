# Implementation Plan: 전투 조작과 플랫폼 테스트 맵 재구현

**Date**: 2026-11-23 | **Spec**: [명세](spec.md) | **Status**: Ready

## Summary

워든의 공격 재생과 수평 이동을 함께 진행시킨다. 입력을 놓으면 플레이어가 시작한 점프의 양의 속도만 줄인다. 기존 Level의 블로킹과 오버랩을 이용해 플랫폼·벽·이동하는 검을 구현하고 LevelScene의 투영 중심을 움직인다.

## Technical Context

- Python/Pico2D와 기존 애니메이션, 입력 버퍼, 월드 좌표, AABB 충돌을 사용한다.
- Space를 일찍 놓았을 때 남은 상승 속도의 상한은 초기 속도의 약 절반으로 잡는다. 지상 공격의 자동 전진은 제거한다. 카메라 시간 상수와 맵 치수는 테스트 튜닝 값이다.
- 기존 워든 몸체·공격 자세와 전하·대시·피격의 입력 및 취소 계약을 보존한다. 분리 가능한 효과는 몸체 대신 효과 픽셀만 수정한다.

## Constitution Check

- [x] 사용자 요청과 기술 시험값을 구분했다.
- [x] 변경 소유 문서·표적 검사·실제 SDL 검사를 지정했다.
- [x] 기존 변경을 보존하고 Git 쓰기 제한은 검증 근거에 기록한다.

## Project Structure & Interfaces

- `game/character.py`는 행동과 실제 이동, 공격 구간 및 점프 속도를 관리한다.
- `game/scene.py`는 지형을 등록하고 갱신 결과를 카메라에 반영하며 검과 적의 상대 궤적을 검사한다.
- `assets/warden/`은 캐릭터와 공격 효과를 런타임에 공급한다.

## Documentation Impact (mandatory)

`docs/systems/basic-gameplay.md`, `docs/systems/basic-enemy.md`, `docs/architecture.md`, `docs/art-direction.md`, `docs/progress.md` 및 필요 시 전하 시스템의 경계 설명을 맞춘다. [검증 기록](verification.md)에 조사 구간·명령·결과를 남긴다.
