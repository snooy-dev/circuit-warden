# Implementation Plan: 게임오브젝트 충돌

1. `game_framework/collision.py`에 불변 콜라이더, 양측 응답, AABB 스윕을 둔다. `Level`은 기존 객체 소유 목록에서 콜라이더를 조회한다.
2. 워든과 바닥은 Block, 워든과 적 및 검과 적은 Overlap으로 연결한다. 워든의 화면 경계와 적의 AI 상태, 피해 시간과 순서를 보존한다. 순간이동은 도착 좌표의 블로킹 오버랩을 검사한다.
3. 초기 접촉과 이동 방향, 큰 갱신의 터널링, 객체 제거, 전투 시간 경계, 대시·착지·도착지 거부를 테스트한다. 실제 SDL 창에서 게임 조작 시나리오를 확인한다.
4. 현재 계약은 `docs/architecture.md`, 진행 근거와 결과는 `docs/progress.md`와 `verification.md`에 기록한다.
