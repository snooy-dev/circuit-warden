# Implementation Plan: 전투 조작과 플랫폼 테스트 맵 재구현

**Date**: 2026-11-23 | **Spec**: [명세](spec.md) | **Status**: Ready

## Summary

워든의 공격 재생과 수평 이동을 함께 진행시킨다. 입력을 놓으면 플레이어가 시작한 점프의 양의 속도만 줄인다. 기존 Level의 블로킹과 오버랩을 이용해 플랫폼·벽·이동하는 검을 구현하고 LevelScene의 투영 중심을 움직인다.

## Technical Context

- Python/Pico2D와 기존 애니메이션, 입력 버퍼, 월드 좌표, AABB 충돌을 사용한다.
- Space를 놓으면 남은 상승을 줄인다. 세부 값은 아래 후속 조정을 따른다. 지상 공격의 자동 전진은 제거한다. 카메라 시간 상수와 맵 치수는 테스트 튜닝 값이다.
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

## Follow-up: 이동과 점프 반응 조정

할로우 나이트의 방향 유지 달리기와 버튼 유지 점프를 참고한다. 워든의 시험값으로 기본 이동을 240 월드 단위/초로 높이고, 시작 클립 12프레임을 30ms로 압축한다. 상승 중 Space를 떼면 그 순간의 상승 속도에 0.65를 한 번 곱한다. 이륙 전 해제에도 같은 비율을 적용한다. 착지의 웅크림 연결은 기존 자세에 맞추고, 최대 점프 높이·중력·대시·순간이동은 기존 값을 쓴다. `game/character.py`, `assets/warden/animations.json`을 수정하고 관련 표적 검사와 SDL 훈련장 검사로 확인한다. 기본 게임플레이·기술 구조·진행 상태를 갱신한다.
