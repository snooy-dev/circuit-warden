# Implementation Plan: 기본 게임플레이

**Date**: 2026-11-11 | **Spec**: [spec.md](spec.md) | **Status**: Ready

## Summary

engine/game_framework를 그대로 사용하고 game에 구체 GameplayMode와 idle/run/attack 상태 전이를 연결한다. 공격 정책은 [기본 조작](../../docs/systems/basic-gameplay.md)을 따른다.

## Technical Context

- **Language/Dependencies**: Python 3.14 + Pico2D 1.5.1, transitions 0.9.3 추가(설치 가능 여부 확인).
- **Runtime**: 게임 .venv만 변경. 도구·전역 Python은 변경 없음.
- **Platform/Performance**: Windows, 기존 dt 상한 100ms와 논리 좌표 유지. 새 성능 목표 없음.
- **Testing**: 상태 전이·큰 dt의 첫 프레임 누락·입력 중복은 표적 unittest, 실제 PNG/자원 수명은 기존 통합 검사, 입력/렌더는 character_smoke를 확장한다. 전체 회귀는 불필요.

## Constitution Check

- [x] 사용자 결정·기술 가정 구분, 개발 요청이 진행 근거이며 PR은 제외.
- [x] 기준 docs 읽음. 공격 중 정지는 사용자 답변으로 해결.
- [x] docs·출처·검증·증분 커밋 계획 포함.
- [x] 엔진 변경·범용 입력 관리자·타이틀 뼈대·외부 서비스 없음.

## Decisions & Alternatives

기존 poll_events → Engine → LevelScene → Level은 키·마우스를 전달한다. Level은 모드 다음 객체에 방송하며 소비 규칙은 없다. GameplayMode가 Character.control로 한 번 전달하고 Character.handle_event는 상속된 무동작으로 둔다. Level이 생성한 player 참조를 보관해 objects[-1] 가정을 제거한다.

SpritePlayer의 loop=False/finished/play(restart=True)를 사용한다. 게임 로더만 bool loop를 수용한다. transitions.Machine은 명시적인 idle/run/attack 전이에 사용하고 auto_transitions=False로 임의 상태 우회를 막는다. 조건문만으로도 가능하지만 사용자 라이브러리 제안에 따라 채택하며 엔진에는 전파하지 않는다.

클릭은 공격 요청을 저장하고 update에서 공격에 진입한다. 진입한 update에는 시간을 진행하지 않아 첫 프레임을 보인다. 공격 동안 이동·방향 변경을 막되 키 변경은 유지한다. 완료 update는 이동 시간을 중복 사용하지 않고 다음 이동 클립을 선택하며 다음 update부터 이동한다. 창 경계는 기존 idle/run 폭을 유지하고 공격 여백은 화면 끝에서 일부 잘릴 수 있다(검·투명 여백 때문에 이동 가능 폭을 줄이지 않음).

## Project Structure & Interfaces

- game/mode.py: GameplayMode.on_event → level.player.control.
- game/scene.py: GameplayLevel(mode=GameplayMode), 명시적 player, 기존 CharacterScene 진입점 유지.
- game/character.py: A/D, 공격 요청·상태 머신, 단발 로더·반전 출력.
- assets/warden/attack.png·animations.json·README.md: 원본 시트·시간·root(96,120)·출처 해시.
- requirements.txt, README.md, tests/unit/test_character.py, tests/integration/test_character_scene.py, tests/smoke/character_smoke.py: 호출부와 검증·실행 안내.
- engine/game_framework/공개 exports·기존 fixtures: 수정 불필요.

## Documentation Impact (mandatory)

feature/basic-gameplay에서 현재 checkout 재사용. 주 에이전트만 쓰기, 감사는 gpt-6.1-sol/high 읽기 전용 위임(여러 계층 경계 검토).

| 요구사항 | 기준 docs | 변경 시점·내용 | 검증 |
|---|---|---|---|
| FR-001/002/003 | architecture, systems, progress | 첫 증분: 감사·모드·A/D·진행 기록 후 커밋 | 이동·모드 입력 표적 검사 |
| FR-004/005/006 | art-direction, assets README, architecture, systems | 두 번째 증분: 공격 연결·상태·출처 | 상태/SDL/PNG 검사 |
| FR-DOC | game-design, README, tests README, progress | 최종: 실행 안내·현 상태·verification 동기화 후 커밋 | 링크·공백·converge |

constitution/workflow/tooling은 정책·도구 환경 변화가 없어 수정하지 않는다. 완료된 009/010은 과거 검증 근거로 보존한다.

## Verification & Risks

첫 증분은 기존 이동 검사와 구체 모드 단일 전달을 확인한다. 두 번째는 공격 중 재클릭·키 해제/반대키/양키·포커스·종료 재공격·첫 프레임과 잘못된 loop를 검사한다. 실제 창 smoke는 양 방향 공격·종료 복귀를 관찰 가능한 PNG로 캡처한다. 좌측 공격은 반전 임시 표현이며 해부학적 손 표현·기존 공격 프레임의 형태 흔들림은 최종 아트 품질 승인이 아니다. 별도 좌측 원화 제작은 제외한다.
