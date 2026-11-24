# Implementation Plan: 워든 전투와 일회성 전하

**Date**: 2026-11-23 | **Spec**: [명세](spec.md) | **Status**: Ready

## Summary

전하의 수명과 이동 성공 조건을 기존 전하·모드에 연결한다. 지상 적 위를 스쳐 타격할 수 있는 진입점과 다음 전하를 배치하고 J로 검 입력을 보장한다. 실제 피해에서만 적중 효과를 만들고 성공한 이동의 도착점에서만 소모 효과를 만든다.

## Technical Context

- Python + Pico2D와 현재 게임 venv를 사용한다. 이미지 제작·감사는 로컬 도구와 내장 ImageGen으로 진행한다.
- 선택·소비·재시작·공중 타격·보호 경계는 표적 자동 검사로 확인한다. 입력 및 합성은 실제 SDL 창에서 검증한다.

## Constitution Check

- [x] 일회성 소비는 사용자 결정이고 키·보호 시간·배치는 기술 시험값이다.
- [x] 기존 지상 FX 타이밍 및 미승인 공중 FX는 보류 상태를 따른다.
- [x] 영향 문서와 범위 안의 검사만 갱신한다.
- [x] 기존 엔진 및 자료형을 재사용한다.

## Decisions & Alternatives

- 배치된 전하는 레벨이 소유하고 성공 시 소비 상태를 기록한다. 소비 후에는 선택과 렌더 목록에서 제외한다. R에서 배치와 공유 텍스처를 재사용한다.
- 기존 100ms 링크와 다음 대상 예약을 유지한다. 성공한 이동에서 돌진 피해용 별도 보호 시간을 시작하고 접촉 반동과 기존 피격 깜박임에는 영향을 주지 않는다.
- 전하 진입점을 낮춰 상승 중 검 사거리가 적과 겹치게 하고 다음 전하를 활성 거리 안에 배치한다. 캐릭터 클립과 기본 물리를 재사용한다.
- SpriteEffect로 판정과 단발 효과를 분리한다. 실제 피해 적용 좌표에 pixelfx 적중 스파크, 소비한 목표 좌표에 ImageGen 전하 소멸 효과를 배치한다. generate2dsprite로 시트를 처리·검사한다.

## Project Structure & Interfaces

- game/charge.py, game/mode.py, game/character.py, game/scene.py가 전하·입력·접촉을 연결한다.
- assets/combat, game/effects.py, game/scene.py, game/mode.py가 검 적중과 전하 소모 플립북을 로드하고 재생한다.
- tests/integration의 전하·적 전투, tests/unit의 접촉 경계, tests/smoke/charge_smoke.py의 실제 입력 시나리오를 갱신한다.

## Documentation Impact (mandatory)

| 증분 | 기준 docs | 갱신 및 확인 |
|---|---|---|
| FR-001–003 | game-design, charge-teleport, basic-gameplay, basic-enemy, architecture, progress | 실제 규칙·시험값 갱신, 자동 검사 후 커밋 |
| FR-004·SC-001–003 | art-direction, architecture, progress | 시트와 실게임 화면 감사 및 커밋 |
| SC-DOC | verification, tasks | 실제 명령·증거와 남은 선택 확인 |

feature/warden-combat에서 작업한다. 전투 경계 검토는 GPT-6.2 Astra 기본 추론의 읽기 전용 작업으로 분리한다.

## Verification & Risks

검 판정과 적 몸체는 포즈나 효과 픽셀에 의존하지 않는다. 소비 전하에 대한 좌우 클릭, 출발점과 도착점 사이의 돌진, 실패한 예약, 재시작, 한 스윙의 중복 적중, 100ms 보호 경계와 SDL 입력·장면 합성을 확인한다.
