# Implementation Plan: 전원 조립체

**Date** 2026-11-26 | **Spec** [spec.md](spec.md) | **Status** Ready

## Summary

공유 전투 스윕의 위치·이동을 두 축으로 확장한 뒤 기획서의 원화를 바탕으로 부하 시험실의 세 공격, 처치 및 출구를 연결한다.

## Technical Context

Python + Pico2D, 기존 이미지/스프라이트 로더와 에셋 격자를 사용한다. 도구 Python에서 원화를 2×2 표시용으로 가공한다. 검증은 기존 적 연속 판정, 보스 공격·문·체력, SDL 분기와 출력에 한정한다.

## Constitution Check

- [x] 설계 기반과 이번 구현값을 구분한다.
- [x] 기존 게임·적·아트 기준과 021·025 명세를 확인했다.
- [x] 증분별 자동·직접 검사 및 결과 기록을 포함한다.
- [x] 엔진·의존성·다음 레벨·별도 전투 모드를 추가할 필요가 없다.

## Decisions & Alternatives

맵 좌표 (1640,656)에 보스를 배치하고 중심은 x1248~2160에서 이동한다. 독립 지형 검토로 진입 시 가시 범위와 닫힌 문 `[2320,464,20,192]`의 천장~바닥 연결을 확인했다. 케이블을 포함한 가로폭만큼 기존 일반 적 위치에서 40만큼 왼쪽으로 옮긴다. 서쪽 출입구는 물러나는 길로 사용한다. 보스 몸통 스윕은 실제 수직 곡선을 프레임의 짧은 선분으로 전달한다. 케이블과 착지 범위 및 전기탄은 검격 대상 몸통과 별도이며, 기존 공격 ID와 피해 보호를 공유한다.

## Project Structure & Interfaces

- `game/enemy.py`, `game/scene.py`에서 위치·이동, 보스 상태와 검·피해·수명을 연결한다.
- `game/power_supply_map.py`, `assets/levels/power-supply/map.json`에서 닫힌 출구와 전하를 배치한다.
- `assets/enemies/`에 원화·런타임 PNG·클립·출처를 두고 기존 정수 픽셀 그리기를 쓴다.
- `tests/integration/test_power_supply_boss.py`와 기존 SDL 전원 구역 검사에서 전투 및 두 경로를 확인한다.

## Documentation Impact (mandatory)

| 증분 | 기준 | 검증 |
|---|---|---|
| 2축 공유 전투 판정 | 기술 구조 | 기존 적 전투·충돌 테스트 |
| 보스·셔터·에셋 통합 | 레벨·적·아트·진행 | 대상 자동 검사, 실제 SDL 전투와 양쪽 출력 |

`feature/power-supply-boss`에서 로컬 검증을 커밋한다. 배치·셔터의 독립 검토에 gpt-6.2-astra medium을 사용했다.

## Verification & Risks

도약 중 검·몸통과 착지 범위를 각각 검사한다. 전기탄의 연속 접촉과 보호 소비, 케이블 앞뒤, 셔터 우회 방지, 처치 직후 및 R을 확인한다. 실제 창에서 원화와 세 패턴의 가독성을 검사한다.
