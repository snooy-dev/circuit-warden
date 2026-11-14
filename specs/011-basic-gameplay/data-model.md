# Data Model

- GameplayLevel: images, player(Character), mode(GameplayMode). on_open마다 새 플레이어 생성.
- GameplayMode: level에 종속, on_event는 player.control로 단일 전달.
- Character: x/facing/pressed/view_bounds, attack_requested, Machine(state=idle|run|attack|dash|jump), SpritePlayer. 이동·공격 상태는 객체별이다.
- Clip: 기존 SpriteClip. loop는 정확한 bool, durations는 기존 양수 유한 초 검증, 공격 7개 프레임과 root 보존.
- 전이: move idle→run, stop run→idle, attack idle/run→attack, finish attack→idle. 완료 시 현재 입력/경계로 run 선택 가능. 공격 중 입력은 키 상태만 바꾸고 요청은 무시한다.

- SpriteEffect: 공격 시점 position/facing/scale 불변, 독립 SpritePlayer(sword_trail), 700ms 종료 시 level에서 제거. 여러 공격의 효과가 공존할 수 있다.

- Character 점프: y(발 기준 월드 좌표), velocity_y(수직 속도), jump_requested(갱신 전 요청). grounded는 y=GROUND_Y와 velocity_y=0. Space는 pressed set에 포함하고 좌우 방향 계산에는 영향 없음. 점프 state=jump의 jump_phase(start/rise/fall/land), jump_elapsed(시작/착지 시간)를 사용한다. 공중 대시는 rise/fall에서만 가능하고 종료 후 jump로 돌아간다. 공격 진입은 지상 idle/run에서만 가능.

- Character 대시: dash_requested(미시작 요청), dash_remaining(현재 단계의 남은 초), dash_phase(준비/이동/복귀 클립 종류), dash_facing(복귀 연결 방향), air_dash_used(착지 전 공중 사용). dash 전이 idle/run→dash, end_dash 전이 dash→idle. 방향 고정·기존 중력 유지, 착지 시 air_dash_used 해제. 종료 갱신은 기존 입력/경계에 따라 idle/run을 선택하고 동일 Run 재생을 유지한다. 일반 이동·재생 시간을 중복 적용하지 않는다.

- 대시 SpriteEffect: 이동 시작의 월드 x/y에 고정, 좌우 전용 dash_fx 클립·367ms·뒤쪽 레이어·독립 소멸. 베기에도 동일 클래스를 사용한다.

- 공중 체공: dash_phase=dash인 동안 y/velocity_y를 그대로 보존한다. 다른 단계와 완료 후에는 기존 수직 적분으로 이어간다.
