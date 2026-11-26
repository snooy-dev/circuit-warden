# Implementation Plan: 발판 이탈 직후 점프

**Date** 2026-11-26 | **Spec** [spec.md](spec.md) | **Status** Ready

## Technical Context

공유 `Character`의 일반 수평 이동에서 지면 접촉의 변화를 감지한다. 낙하 갱신에 유예 시간을 차감하고 유효한 점프 입력은 기존 상승 시작과 Space 해제를 재사용한다. 두 레벨에 같은 동작을 적용한다.

## Constitution Check

- [x] 사용자 요청 범위와 유예 시험값을 구분했다.
- [x] Python과 Pico2D의 기존 입력·충돌·표시 경로를 사용한다.
- [x] 관련 점프 검사와 문서 갱신을 포함한다.

## Documentation Impact (mandatory)

[기본 게임플레이](../../docs/systems/basic-gameplay.md)와 [기술 구조](../../docs/architecture.md)에 적용 범위와 시간 계산을 기록한다. [진행 상태](../../docs/progress.md)와 기능 검증에 결과 및 조작감 미확인 여부를 기록한다.

## Verification

훈련장 발판에서 걸어서 이탈한 뒤 Space를 누르는 시점을 나눠 검사한다. 직접 점프와 다른 공중 진입 경로, 가변 높이, 착지 재점프를 관련 점프 통합 검사로 확인한다.
