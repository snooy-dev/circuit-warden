# Data Model

- GameplayLevel: images, player(Character), mode(GameplayMode). on_open마다 새 플레이어 생성.
- GameplayMode: level에 종속, on_event는 player.control로 단일 전달.
- Character: x/facing/pressed/view_bounds, buffered_action/buffer_remaining, Machine(state=idle|run|attack|dash|jump), SpritePlayer. 이동·공격 상태는 객체별이다.
- Clip: 기존 SpriteClip. loop는 정확한 bool, durations는 기존 양수 유한 초 검증. 지상17표시프레임/340ms·공중18표시프레임/300ms와 각 원본의 표시 순서·root를 보존. 지상 frameIndices는 뒤쪽 효과→몸체→앞쪽 효과를 합성한 프레임을 순서대로 가리킨다.
- 전이: move idle→run, stop run→idle, attack idle/run→attack, finish 지상 attack→idle, 공중 attack→jump. 완료 시 현재 입력/경계로 run 선택 가능. 공격 중 새 행동은 buffered_action에 마지막1개만 저장하고 buffer_remaining100ms 안에 가능하면 소비한다. 포커스 상실·만료·무효 출력에서 지운다.

- Character 점프: y(발 기준 월드 좌표), velocity_y(수직 속도). 허용된 점프 예약은 지역값으로 갱신에 직접 전달한다. grounded는 y=GROUND_Y와 velocity_y=0. Space는 pressed set에 포함하고 좌우 방향 계산에는 영향 없음. 점프 state=jump의 jump_phase(start/rise/fall/land), jump_elapsed(시작/착지 시간)를 사용한다. 공중 대시는 rise/fall에서만 가능하고 종료 후 jump로 돌아간다. 공격 진입은 지상 idle/run 또는 jump의 rise/fall에서 가능. 공중 공격은 수직 상태를 보존하고 공격 완료 시 jump로 복귀하며, 바닥 접촉이 먼저면 남은 공격을 취소하고 land로 전환.

- Character 대시: dash_remaining(현재 단계의 남은 초), dash_phase(준비/이동/복귀 클립 종류), dash_facing(복귀 연결 방향), air_dash_used(착지 전 공중 사용). dash 전이 idle/run→dash, end_dash 전이 dash→idle. 방향 고정·기존 중력 유지, 착지 시 air_dash_used 해제. 종료 갱신은 기존 입력/경계에 따라 idle/run을 선택하고 동일 Run 재생을 유지한다. 일반 이동·재생 시간을 중복 적용하지 않는다.

- 대시 SpriteEffect: 이동 시작의 월드 x/y에 고정, 좌우 전용 dash_fx 클립·367ms·뒤쪽 레이어·독립 소멸.

- 공중 체공: dash_phase=dash인 동안 y/velocity_y를 그대로 보존한다. 다른 단계와 완료 후에는 기존 수직 적분으로 이어간다.

- 착지 연결: land60~90ms에서 유효 buffered_action=jump면 start/jump_elapsed=.04로 전환하고 예약을 지운다. airborne 속도는 남은 시작80ms 종료 때 설정한다.
