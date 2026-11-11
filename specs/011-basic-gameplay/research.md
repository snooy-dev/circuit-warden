# Research: 기반 감사와 기술 선택

## 입력·모드

Decision: game에 GameplayMode를 추가하고 입력을 한 번 전달한다.
Rationale: engine/events.py가 키 repeat 필터·마우스 버튼·창 이벤트를 보존한다. engine/loop.py는 입력→update→draw, 최소화 중에도 update한다. game_framework/world.py는 mode.on_event 후 모든 객체.handle_event를 호출하며 반환값으로 소비하지 않는다. game/scene.py의 objects[-1] 대신 명시적 player 참조가 필요하다.
Alternatives considered: 범용 InputManager·입력 소비 API 추가는 현재 한 플레이어에 불필요.

## 재생·상태

Decision: SpritePlayer 재사용, 게임 로더 bool loop 전달, transitions.Machine 명시 전이.
Rationale: game_framework/sprites.py는 반복·단발·finished·restart를 이미 지원한다. 기존 game/character.py는 loop=False를 거부하고 매 update idle/run으로 덮어쓴다. 50ms 프레임 진입 직후 update(.1)는 첫 렌더 전에 세 번째 프레임을 선택하므로 진입 update는 0초 유지한다.
Alternatives considered: if문 상태도 충분하나 사용자 권고에 따라 transitions를 game에만 도입한다.
Source: [공식 transitions README](https://github.com/pytransitions/transitions/blob/master/README.md), Context7로 auto_transitions=False와 명시 전이 API 확인.

## 자산

Decision: attack-v5/sheet.png 원본 1344×192, 7열·각 50ms·root=(96,120)를 복사한다.
Rationale: 잠정 승인된 공격 사용이 이번 요청 범위다. 셀 크기가 다르므로 SDL 출력에서 실제 몸 크기·접지를 확인한다. 원본 수정/재생성 없음.
Alternatives considered: 좌측 새 시트 생성은 요청 밖이므로 반전 사용. 공격 여백을 기존 이동 경계에 합치면 이동 범위가 줄어들어 기존 경계를 유지한다.
