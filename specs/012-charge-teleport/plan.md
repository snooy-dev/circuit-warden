# Implementation Plan: 전하 순간이동

**Date**: 2026-11-15 | **Spec**: [spec.md](spec.md) | **Status**: Ready

## Summary

기존 GameplayLevel에 전하 객체를 배치하고 CharacterScene의 event_to_world로 선택한다. GameplayMode가 공격보다 전하 선택을 먼저 처리하고 Character.teleport가 모든 행동을 낙하/idle로 전환한다. 승인된 전하 전환·400ms 연결식을 Python으로 재사용한다.

## Technical Context

- **Language/Dependencies**: Python 3.14, Pico2D 1.5.1, transitions 0.9.3. 의존성 추가 없음.
- **Runtime**: 게임 .venv/. 아트 생성·외부 서비스 없음.
- **Platform/Performance**: 기존 Windows SDL 창. 게임 성능의 별도 확정 목표 없음. 전하 5개의 보간·이펙트 비용을 실제 창에서 확인한다.
- **Testing**: 상태 취소·선입력·좌표·수명에 표적 unittest, 승인 색 보간에 픽셀 검사, 실제 창에 전용 smoke.

## Constitution Check

- [x] 사용자 답변(왼쪽 클릭 우선·모든 행동 취소)과 기술 시험값을 구분했다.
- [x] 기준 docs의 미정 입력은 이번 답변으로 해결하며 나머지는 최소 시험안으로 명시했다.
- [x] 증분별 docs·검증·커밋과 최종 converge를 계획했다.
- [x] 기존 엔진과 SDL을 유지하고 외부 서버·DB·새 의존성을 추가하지 않는다.

## Decisions & Alternatives

연구는 [research.md](research.md). 단순 source-over 겹침은 승인된 premultiplied 보간과 다르므로 작은 RGBA 텍스처에 CPU 보간 후 업로드한다. 연결은 고정 시트를 늘리지 않고 양 끝점 기반 생성식을 이식한다. 신규 일반 렌더 프레임워크를 만들지 않는다.

## Project Structure & Interfaces

- game/charge.py: 전하 상태·공유 위상·거리·픽셀 합성 및 장면 수명 자원.
- game/teleport_link.py: 승인 v4 끝점 생성식·400ms 일회 효과. game/effects.py의 GameObject/RenderItem 패턴 재사용.
- game/character.py: 중심·유효 도착·행동 취소. 기존 _advance_vertical/_show_jump 재사용.
- game/mode.py, game/scene.py: 선택 우선순위, 화면→월드, 전하 배치와 공유 이미지 수명.
- assets/charge/: 이미 승인된 상태 v5·전환 v2 파일. 사용자 점프 PNG·tmp 및 루트 README 변경 제외.
- tests/unit/test_charge_teleport.py, tests/integration/test_charge_scene.py, tests/smoke/charge_smoke.py: 표적 규칙·SDL·출력 확인.
- 인터페이스는 [contracts/controls.md](contracts/controls.md), 엔티티는 [data-model.md](data-model.md).

## Documentation Impact (mandatory)

브랜치 feature/charge-teleport는 origin/main 6568aa7에서 생성했다. 1차 증분은 상태 표시·선택·행동 취소·낙하를 검증/문서화/커밋한다. 2차 증분은 전류 연결·실제 창·수명과 전체 대응을 검증/문서화/커밋한다. 읽기 조사에는 gpt-6.1-sol/medium을 사용했으며 독립 효과 구현은 별도 워크트리·파일 담당으로 위임할 수 있다.

| 요구사항/결정 | 기준 docs | 바뀌는 내용 | 갱신 시점 | 검증 방법 |
|---|---|---|---|---|
| FR-001~005 | docs/systems/charge-teleport.md, docs/systems/basic-gameplay.md | 입력·취소·시험값·도착 | 설계/1차 구현 | 규칙 표적 검사 |
| FR-001,006~007 | docs/art-direction.md, docs/architecture.md | 승인본 연결·자원·좌표 | 구현 후 | 픽셀·수명·SDL |
| SC-DOC | docs/progress.md, docs/game-design.md, tests/README.md | 현재 상태·검사 안내 | 증분 완료 | 문서 대응·공백 |

## Verification & Risks

[quickstart.md](quickstart.md)의 표적 검사와 SDL smoke를 수행한다. alpha 보간·부호 뒤집힘·상태 취소 누락·resize 오선택·종료 누수가 구체적 위험이다. 기존 jump/dash 선입력 관련 검사는 변경 영향이 있는 항목만 재사용/실행한다. 활성 거리/배치/재사용·조작감은 사용자 플레이 전이다. 전체 회귀는 선택하지 않는다.
