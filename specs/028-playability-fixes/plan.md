# Implementation Plan: 첫 레벨 플레이 결함 개선

**Date** 2026-11-26 | **Spec** [spec.md](spec.md) | **Status** Ready

## Technical Context

`CharacterScene`의 기존 Canvas 안내 문구에 쓰러짐과 출력 완료를 연결한다. 승리·패배·재시작 판정은 기존 레벨 상태에서 읽는다. 출력 및 재시작은 실제 SDL 첫 레벨과 소프트웨어 렌더러 통합 검사로 확인한다.

컷신 종료와 플레이 시야 복구는 한 함수에서 처리한다. 전하는 거리 검사와 `Character.can_teleport`를 공유한다. 환경 전하 생성은 기존 배치 가능 검사로 유지한다.

## Constitution Check

- [x] 기존 전원 구역 진행과 승인된 전투 규칙을 기준으로 삼았다.
- [x] 의존성 변경 없이 기존 UI와 게임 상태를 사용한다.
- [x] 개선 범위, 문서 영향 및 표적 검사 기준을 기록한다.

## Documentation Impact (mandatory)

[기본 적 전투](../../docs/systems/basic-enemy.md), [전하 순간이동](../../docs/systems/charge-teleport.md), [게임 설계](../../docs/game-design.md)와 [진행 상태](../../docs/progress.md)에 화면과 입력 동작을 반영한다. [검증 기록](verification.md)에 첫 레벨·출력·조작 검사 결과를 정리한다.
