# Data Model

- GameplayLevel: images, player(Character), mode(GameplayMode). on_open마다 새 플레이어 생성.
- GameplayMode: level에 종속, on_event는 player.control로 단일 전달.
- Character: x/facing/pressed/view_bounds, attack_requested, Machine(state=idle|run|attack), SpritePlayer. 이동·공격 상태는 객체별이다.
- Clip: 기존 SpriteClip. loop는 정확한 bool, durations는 기존 양수 유한 초 검증, 공격 7개 프레임과 root 보존.
- 전이: move idle→run, stop run→idle, attack idle/run→attack, finish attack→idle. 완료 시 현재 입력/경계로 run 선택 가능. 공격 중 입력은 키 상태만 바꾸고 요청은 무시한다.
