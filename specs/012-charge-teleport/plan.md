# Implementation Plan: 전하 순간이동

**Date**: 2026-11-15 | **Spec**: [spec.md](spec.md) | **Status**: Ready

## Summary

기존 GameplayLevel에 전하 객체를 배치하고 CharacterScene의 event_to_world로 선택한다. GameplayMode가 공격보다 전하 선택을 먼저 처리하고 Character.teleport가 모든 행동을 공중 상승(상단 여유0이면 낙하)/idle로 전환한다. 승인된 전하 전환·400ms 원본 연결식을100ms 재생으로 압축해 Python으로 재사용한다.

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
- game/teleport_link.py: 승인 v4 끝점 생성식·100ms 시험 재생의 일회 효과. game/effects.py의 GameObject/RenderItem 패턴 재사용.
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

클릭 판정 확대: game/charge.py의 CLICK_RADIUS만24→48로 조정한다. GameplayMode의 일반 선택과 선입력이 같은 판정을 재사용하므로 호출부·자산·설정·의존성 변경은 없다. 기존 선택/중첩·배율·선입력 검사와 SDL smoke의 클릭 지점을 표시 밖으로 옮겨 넓어진 영역을 확인한다. 별도 테스트나 디버그 표시는 추가하지 않는다. 시스템 기준·progress·spec/plan/tasks/verification만 갱신하고 아트·기술 구조·게임 의도 문서는 변경 영향이 없다. 입력 영역 확대로 공격하려던 클릭이 인접 전하를 선택할 가능성은 사용자 플레이에서 평가한다.

[quickstart.md](quickstart.md)의 표적 검사와 SDL smoke를 수행한다. alpha 보간·부호 뒤집힘·상태 취소 누락·resize 오선택·종료 누수가 구체적 위험이다. 기존 jump/dash 선입력 관련 검사는 변경 영향이 있는 항목만 재사용/실행한다. 기존 즉시 낙하는 사용자 플레이에서 반응 시간이 부족하다는 피드백을 받았다. 새 상승 관성과 활성 거리/배치/재사용의 최종 조작감은 사용자 재확인 전이다. 전체 회귀는 선택하지 않는다.

후속 입력 규칙: GameplayMode가 진행 중 TeleportLink와 마지막 예약 전하를 보관한다. 활성 기준점은 진행 중 효과의 도착점이며 시작 이벤트에서 즉시 전하 상태를 갱신한다. CharacterScene은 Level 갱신 후 모드의 예약 실행을 호출해 효과 종료와 같은 프레임에 다음 이동을 시작한다. 첫 프레임 시간은 생성 시점과 최초 출력 여부를 반영한다. 논리 활성과 승인 상태 보간은 분리한다.

공중 도착 관성 조정: game/character.py의 teleport에서 기존 수직 속도를 GRAVITY×0.24으로 교체하고 rise 모션을 재사용한다. 상단 여유로 허용되는 속도 sqrt(2×GRAVITY×여유)로 제한한다. 기존 _update_jump/_advance_vertical은 그대로 사용하며 공중 대시 이력·100ms 전류/진행·목표 기준 활성화·선입력은 유지한다. tests/unit/test_charge_teleport.py의 정점·분할 시간·복귀·상단·비누적 검사, tests/integration/test_charge_scene.py의 예약 연결과 tests/smoke/charge_smoke.py의 실제 상승/낙하 관찰을 선택한다. 해당 코드/테스트와 시스템·기술 구조·게임 설계·progress·012 문서를 한 증분으로 커밋한다. 새 아트/의존성/공용 엔진 변경이 없어 나머지 검사는 기존 근거를 재사용한다.

후속 상승 강화: 더 높이 오르고 덜 빨리 떨어지게 해 달라는 사용자 요청에 따라 상승 시간만 조정한다. 일반 점프·중력·상단 제한·비누적·선입력은 유지한다. 기존 정점/복귀 검사 기대값을 바꾸고 상단 제한·행동 취소·예약 연결 검사와 SDL smoke를 실행한다. 시스템/progress 및 012 spec/plan/tasks/data-model/quickstart/verification을 동기화한다. Analyze: FR-004의 범위 안이며 호출부·설정·내보내기·자산 변경이나 새 의존성이 필요하지 않다.

우클릭 확장: GameplayMode.on_event의 후보 생성·실행/예약 분기를 공유하고 우클릭에서는 활성 기준점으로 거리를 정렬하며 클릭 반경 제한을 적용하지 않는다. 유효 출력 여부는 CharacterScene이 갱신한 view_bounds로 확인한다. 기존 활성 거리/도착 검증·동률 배치 순을 재사용한다. game/scene.py의 조작 안내, tests/integration/test_charge_scene.py의 표적 검사와 tests/smoke/charge_smoke.py의 우클릭 시나리오를 갱신한다. 시스템/basic-gameplay·architecture·game-design·progress 및 012 spec/plan/tasks/contracts/quickstart/verification이 문서 영향 범위다. 엔진·캐릭터 물리·자산·의존성·설정·내보내기는 변경하지 않는다. Analyze: FR-009는 FR-002의 왼쪽 선택과 FR-008의 마지막 유효 예약 계약을 유지한다.

마지막 도착 제외: GameplayMode.last_charge에 성공한 도착 전하를 기록하고 우클릭 후보만 객체 동일성으로 제외한다. 예약/실패 입력은 기록을 바꾸지 않고 다음 도착 성공으로 교체하며 on_end에서 해제한다. _teleport 호출부는 on_event/after_update 두 곳으로 공통 구현을 유지한다. 기존 혼합 선입력 검사와 신규 제외/좌클릭/단독 대상/종료 검사를 선택하고 SDL에서 연속 우클릭을 확인한다. 시스템/progress/architecture 및 012 spec/plan/tasks/contracts/quickstart/verification을 갱신한다. Analyze: FR-005 재사용은 좌클릭으로 유지하며 FR-008 예약을 훼손하지 않는다. 자산·설정·내보내기·엔진·물리 변경은 없다.

착지 후 제외 해제: 사용자 확인으로 공중 제외·착지 해제를 확정했다. CharacterScene.update가 호출하는 GameplayMode.after_update 끝에서 기존 grounded 판정을 재사용해 last_charge를 비운다. 지상 순간이동 도착도 즉시 비우고 공중 예약 실행은 새 도착 기록을 유지한다. 착지 모션 중 재사용·공중 제외·선입력·지상 도착을 표적 검사하고 SDL에 착지 후 같은 전하 재사용을 추가한다. 시스템/progress/architecture 및 012 spec/plan/tasks/contracts/quickstart/verification을 동기화한다. Analyze: FR-009만 수정하며 FR-003/008의 행동 취소·예약 처리는 유지한다. 공용 엔진·물리·자산·의존성은 변경하지 않는다.
