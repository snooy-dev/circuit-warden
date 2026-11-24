# Implementation Plan: 오프닝 스토리 컷신

**Spec**: [명세](spec.md)

## Reference

- 《Another World》의 사건 중심 연출과 Éric Chahi가 《Heart of Darkness》의 카메라 전환을 설명한 사례를 참고했다. 워든의 낙뢰와 조작 인계가 한 사건으로 이어지도록 한다. [GDC 포스트모템](https://www.gdcvault.com/play/1014630/classic-game-postmortem-out-of) · [Chahi 인터뷰](https://nintendoworldreport.com/interview/47746/interview-with-eric-chahi-on-another-world-for-nintendo-switch).
- 《INSIDE》의 게임 화면이 움직임과 환경으로 상황을 전달하는 방식에서 전원 구역의 팬과 빛을 활용하는 방향을 가져왔다. [Playdead의 공식 영상 자료](https://playdead.com/press/).

## Storyboard

| 시간 | 화면 | 서사 기능 |
|---|---|---|
| 0.0~0.95초 | 어둠에서 상단 케이블과 흡기 팬이 드러난다. 팬이 돌기 시작하고 카메라가 물러난다. | 오래 멈춘 장치가 전원을 받는다. |
| 0.95~1.72초 | 구리 쪽에서 작은 스파크가 튄다. 팬과 조명이 가라앉고 카메라가 바닥을 프레임에 넣는다. | 기동이 실패하고 방전 지점이 드러난다. |
| 1.72~2.20초 | 같은 케이블에서 낙뢰가 바닥까지 이어진다. 타격 때 짧게 흔들린 뒤 워든이 모습을 드러낸다. | 고장 난 전원 구역에 워든이 도착한다. |
| 2.20~2.85초 | 전하가 드러나고 화면의 검은 띠가 걷힌다. 카메라가 게임 구도에 도착하면 조작을 넘긴다. | 워든을 움직여 전원 구역을 탐색한다. |

서사 제안은 전원이 들어왔으나 출력까지 닿지 못한 회로에 워든이 도착하는 이야기다. 출력 단자에 도달하는 기존 첫 목표와 연결할 수 있다. 워든의 기원, 고장 원인, 전원 인가 주체는 미정이다.

## Technical Context

`New Game → CharacterScene(power_supply=True, story_intro=True)`로 진입한다. `PowerOpening`이 같은 레벨 안에서 팬, 스파크, 기존 낙뢰 및 카메라 큐를 재생한다. 연출 중 전투 시뮬레이션과 입력을 보류한다. 자동 종료와 Skip은 같은 레벨의 일반 카메라와 게임플레이를 사용한다. 컷신과 플레이는 현재 공통 픽셀 격자를 거치며 Skip UI는 출력 해상도에서 그린다. R과 훈련장은 기존 경로를 사용한다.

## Constitution Check

사용자 후속 피드백은 전원 구역 내 실시간 연출 제작의 근거다. 세부 서사는 제안 상태다. 조명과 타이밍의 수치는 시안이다. 새 이미지·오디오 및 전투 규칙 변경은 이번 범위 밖이다.
