# Implementation Plan: 공중 아래 베기

**Date** 2026-11-26 | **Spec** [spec.md](spec.md) | **Status** Ready

## Technical Context

기존 검격과 독립 상태·시간·수직 판정을 구현한다. 첫 유효 접점과 적중 효과를 프레임 안에서 계산하고 상승 상태로 전환한다. 게임의 공통 입력 전달·충돌 스윕·그리기 API 위에서 동작한다. 발밑 전기 궤적과 접점 효과는 별도 렌더링으로 제작한다.

시각 보정은 동일 기준점으로 정렬한 전용 세 자세를 아래 베기의 준비·타격·회수 구간에 대응시킨다. 타격 셀의 검 궤적을 아래쪽에 등록하고 실제 게임 장면을 같은 배율로 검토한다.

입력 후 준비 자세와 판정 대기를 30ms로 맞춘다. 타격과 회수 길이는 각각 90ms로 두고 첫 타격 프레임부터 유효 접촉을 허용한다.

## Constitution Check

- [x] 기존 레벨과 전하 이동 조건을 적용한다.
- [x] 준비·타격·반동의 구현값을 플레이 시험값으로 구분한다.
- [x] 표적 자동 검사와 실제 SDL 화면 검사를 포함한다.

## Documentation Impact (mandatory)

[기본 게임플레이](../../docs/systems/basic-gameplay.md), [기본 적 전투](../../docs/systems/basic-enemy.md), [진행 상태](../../docs/progress.md)에 현재 조작과 검증을 반영한다.
