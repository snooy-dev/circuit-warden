# Implementation Plan: 기본 게임플레이

**Date**: 2026-11-11 | **Spec**: [spec.md](spec.md) | **Status**: Ready

## Summary

engine/game_framework를 그대로 사용하고 game에 구체 GameplayMode와 idle/run/attack 상태 전이를 연결한다. 공격 정책은 [기본 조작](../../docs/systems/basic-gameplay.md)을 따른다.

## Technical Context

- **Language/Dependencies**: Python 3.14 + Pico2D 1.5.1, transitions 0.9.3 추가(게임 .venv 설치 확인).
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
- requirements.txt, README.md, docs/README.md, tests/unit/test_character.py, tests/integration/test_character_scene.py, tests/smoke/character_smoke.py: 호출부와 검증·실행 안내.
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

## 후속 증분: 720p·공격/베기 연결

기존 브랜치 fetch·origin/main merge 결과 Already up to date, 작업 트리 깨끗함. 새 공격은 attack-sword-v6/bundle-outlined/sheet.png, 효과는 provisional-approved/sword-trail-electric-v4/trail-sheet.png를 바이트 보존 복사한다. pixelfx MIT 고지는 licenses/pixelfx-LICENSE.txt 한 곳에 보관한다. 게임·자산 README에 별도 제작 도구 사용 문구를 추가하지 않는다. 사용자 지시에 따라 에셋별 라이선스 파일을 만들지 않는다.

game/scene.py의 DEFAULT_SIZE만 (1280,720), Engine(*DEFAULT_SIZE)로 전달해 범용 엔진의 기본값과 view_height=600을 분리한다. F6 대체 크기는 기존 (1024,720)을 유지한다. 호출부 tests/smoke/character_smoke.py와 통합 검사의 window_size를 맞춘다.

game/effects.py에 단발 SwordTrail(GameObject)을 추가한다. 공격 시작에 level.spawn, 좌표·방향·배율 고정, 기존 SpritePlayer로 700ms 뒤 destroy. 레벨 스냅샷 규칙으로 생성 프레임은 update 없이 0초에서 보인다. 바닥(-2)→효과(-1)→캐릭터(0) 순서로 그려 원본 behind character를 유지한다. Character는 독립 검사에서도 쓰이므로 level이 있을 때만 효과를 spawn한다. 재공격마다 독립 객체를 사용해 남은 잔상을 자르지 않는다.

호출부/검사: load_clips와 animations.json에 sword_trail 단발 추가, 기존 단위 fixture는 레벨 없이 이동 검사를 유지한다. 통합 검사 하나에서 효과의 첫 프레임·방향 고정·이동 후 잔존·재공격 공존·소멸·장면 종료를 검증한다. 기존 SDL smoke에서 해상도·양 방향 합성과 잔여 효과를 확인한다. 전체 엔진 회귀는 필요 없다. docs/art-direction·architecture·systems·progress, README·assets 출처·검증을 갱신해 한 증분으로 커밋한다.

## 표시 배율 조정

DISPLAY_SCALE만 1로 변경한다. 기존 캐릭터 출력·이동 경계·SwordTrail 생성이 공통 값을 재사용하므로 새 옵션은 없다. tests/unit/test_character.py의 2배 기대값과 좁은 창 입력을 1배로 조정한다. 경계·출력 검사 2개 및 기존 실제 창 smoke로 발 기준점·베기 정렬을 확인하고 architecture·progress·verification을 맞춘다. 루트 README는 수정하지 않는다.

## 점프 증분

기존 feature/basic-gameplay 동기화 결과 Already up to date. game/character.py에 y·수직 속도·미시작 점프 요청을 추가한다. grounded는 바닥 위치와 수직 속도 0으로 판정한다. Space 유지 상태는 기존 pressed set으로 KEYDOWN 중복을 막는다. 제자리·공중 A/D는 기존 idle/run Machine 전이를 재사용하며 별도 jump 애니메이션 상태나 물리 엔진은 만들지 않는다.

idle 알파를 도구 Python/Pillow로 측정: 첫 프레임 (24,11,78,93), 프레임 높이 81~83, 전체 y 범위 10~93. BODY_HEIGHT=83, JUMP_HEIGHT=BODY_HEIGHT*DISPLAY_SCALE*2, 상승 시간 0.4초로 초기 속도·중력을 유도한다. 일정 가속도 식 y += v*dt - g*dt²/2, v -= g*dt를 사용하고 바닥을 넘으면 clamp한다. 부동소수점 착지 오차만 작은 허용 오차로 처리한다. 런타임 Pillow 의존성 없음.

입력 처리에서 공중 클릭/점프·공격 중 점프를 버린다. update 시작에서 유효한 점프를 먼저 소비해 같은 프레임 공격을 차단하고, 그 후 수평 이동·재생은 기존 경로를 사용한다. Character._draw의 y를 실제 좌표로 바꾼다. SwordTrail은 지상 공격만 가능하므로 기존 바닥 위치를 유지한다. game/scene.py 창 제목·실행 안내에 Space를 반영한다.

호출부·검사: tests/unit/test_character.py에 정점/분할 dt/착지, 공중 A/D/클립, 반복 키/공격/포커스 경계를 검사한다. tests/smoke/character_smoke.py의 기존 시나리오 뒤에 제자리·달리기 점프를 추가한다. docs/systems/basic-gameplay·game-design·architecture·progress와 011 검증을 갱신한다. engine/game_framework/자산/루트 README는 영향 없어 수정하지 않는다. 선택한 표적 검사와 실제 창 확인 후 하나의 플레이 가능한 증분으로 커밋한다.

## 측면 idle 교체

좌우 48프레임의 RGBA가 정확한 수평 반전이므로 기존 idle.png와 반전 경로를 재사용한다. 오른쪽 원본을 복사하고 animations.json pivot x만 58→64, 실제 자산 통합 검사의 pivot 기대값을 수정한다. 좌측 원본 anchor=63은 픽셀 인덱스 반전 기준이며 런타임은 연속 좌표 pivot=64를 반전한다. 별도 좌측 시트/로더/상태를 추가하지 않는다. 새 알파 높이도 81~83px라 점프 상수는 유지한다. 출처·현재 아트/진행/구조 문서 갱신, 표적 PNG 검사와 기존 SDL smoke의 좌우 idle·복귀를 확인한다. 루트 README는 변경하지 않는다.

## 대시

현재 변환은 screen=world×viewport_height/600이며 기본 시야 1066.67×600이다. DISPLAY_SCALE=1에서 알파 범위 최대 키83·폭62 월드 단위(망토 포함), 셀128×104는 여백 포함이다. DASH_DISTANCE=BODY_HEIGHT*2, DASH_SECONDS=.2로 정의하여 화면 픽셀과 분리한다.

Character Machine에 dash와 종료 전이를 추가한다. 요청·잔여 시간·공중 소비 여부만 보관하고 기존 수직 적분 뒤 수평 대시를 처리한다. min(dt, 잔여 시간)만 이동해 초과 dt가 거리를 늘리지 않으며 기존 셀 경계로 clamp한다. 마지막 갱신에서는 일반 이동을 더하지 않고 다음 갱신부터 유지 키를 반영한다. Run 출력은 전용 좌우 클립이므로 dash에서 재반전하지 않는다. 지상 대시는 공중 횟수를 소비하지 않으며 착지가 회복한다.

영향: game/character.py, game/scene.py 안내, tests/unit/test_character.py와 기존 SDL smoke, docs/architecture·systems/basic-gameplay·game-design·progress, 011 문서. 엔진·자산·공개 API·루트 README는 그대로다. 표적 검사로 거리/분할/출력 독립성과 입력 경계·공중 회복을 확인하고 SDL에서 좌우 지상/공중 Run을 캡처한다.
