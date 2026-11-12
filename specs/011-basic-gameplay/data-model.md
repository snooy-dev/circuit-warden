# Data Model

- GameplayLevel: images, player(Character), mode(GameplayMode). on_open마다 새 플레이어 생성.
- GameplayMode: level에 종속, on_event는 player.control로 단일 전달.
- Character: x/facing/pressed/view_bounds, attack_requested, Machine(state=idle|run|attack|dash), SpritePlayer. 이동·공격 상태는 객체별이다.
- Clip: 기존 SpriteClip. loop는 정확한 bool, durations는 기존 양수 유한 초 검증, 공격 7개 프레임과 root 보존.
- 전이: move idle→run, stop run→idle, attack idle/run→attack, finish attack→idle. 완료 시 현재 입력/경계로 run 선택 가능. 공격 중 입력은 키 상태만 바꾸고 요청은 무시한다.

- SwordTrail: 공격 시점 position/facing/scale 불변, 독립 SpritePlayer(sword_trail), 700ms 종료 시 level에서 제거. 여러 공격의 효과가 공존할 수 있다.

- Character 점프: y(발 기준 월드 좌표), velocity_y(수직 속도), jump_requested(갱신 전 요청). grounded는 y=GROUND_Y와 velocity_y=0. Space는 pressed set에 포함하고 좌우 방향 계산에는 영향 없음. 공중에서도 state는 idle/run/dash, attack 진입은 지상에서만 가능.

- Character 대시: dash_requested(미시작 요청), dash_remaining(남은 초), air_dash_used(착지 전 공중 사용). dash 전이 idle/run→dash, end_dash 전이 dash→idle. 방향 고정·기존 중력 유지, 착지 시 air_dash_used 해제. 종료 갱신은 일반 이동 시간을 중복 적용하지 않는다.
