# Implementation Plan: 기술과 환경의 전하 생성

**Date**: 2026-11-23 | **Spec**: [명세](spec.md) | **Status**: Ready

## Summary

GameplayMode에서 E와 커서 월드 좌표를 연결하고 GameplayLevel에서 동시 한 개의 기술 전하를 관리한다. 환경은 기존 다섯 전투 구역 안에서 후보를 뽑고, 소모된 자리를 대기 후 새 Charge 객체로 교체한다. 두 생성원은 같은 순간이동 소비 경로를 쓴다.

## Technical Context

- Python/Pico2D의 SDL 마우스 좌표를 Display.window_to_output과 WorldTransform으로 변환한다.
- 생성 대상의 지형·적·창 검사는 Character.can_teleport를 공유한다. ChargeArt는 장면에서 한 번 로딩하고 장면 해제 때 참조를 정리한다.
- 기존 공중 진입과 이탈이 가능한 구역 안에서 위치를 변동시킨다. 랜덤 배치와 시간 경계는 고정된 후보 선택 및 dt로 검증하고 실제 창에서 조작을 점검한다.

## Constitution Check

- [x] 사용자 규칙과 기술 시험값을 구분했다.
- [x] 기존 기준, 적 충돌, 입력·공중 전투 영향 범위를 읽었다.
- [x] 영향 문서 갱신과 증분 검증을 지정했다.
- [x] 기존 엔진과 아트로 처리한다.

## Decisions & Alternatives

- 기술 생성은 현재 행동을 끊지 않는다. E가 실제 전하를 만든 시점에만 재사용 대기를 시작한다.
- 환경은 후보 좌표를 가진 고정 구역으로 범위를 제한한다. 구역별 기존 소비 객체를 숨기고, 교체 때 제거하여 다른 좌표의 새 객체나 예약과 분리한다.
- 죽은 워든에서는 레벨 갱신 자체가 정지한다. 적 처치 뒤에는 생성 시간이 계속 간다.

## Project Structure & Interfaces

game/mode.py, game/scene.py, game/charge.py와 관련 통합·SDL 검사만 바꾼다. feature/charge-generation에서 작업하며 GPT-6.2 Sol의 기본 추론을 기존 경로·테스트 검토에 사용한다.

## Documentation Impact (mandatory)

FR-001과 기술 소비는 전하·기본 조작 문서와 첫 증분으로 검증한다. FR-002와 환경 리셋은 게임 설계·기술 구조·기본 적·진행 상태 및 최종 증분에 기록한다. 전체 결과는 verification.md에 남긴다.

## Verification & Risks

E 키 반복, 쿨다운, 거리·몸통·전하 겹침, 환경 소모 후 대기·좌표 변경, R과 예약, 기존 공중 타격·돌진 회피·창 좌표를 검사한다. 전체 회귀는 실행 범위에 포함하지 않는다.
