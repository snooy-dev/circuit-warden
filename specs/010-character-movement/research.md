# Research: 캐릭터 이동 검사

- Decision: 기존 엔진 PR #2를 기반으로 game 패키지에 정책을 둔다. Rationale: 키 유지/이동은 게임 정책이고 009에 표시·재생이 있다. Alternatives: 새 엔진/중복 스프라이트 구현 제외.
- Decision: 좌우 Run 전용 시트와 idle 반전을 사용한다. Rationale: 사용자가 지정한 아트·기준점 보존. Alternatives: Run을 임의 재생성하거나 별도 방향 아트를 만들지 않는다.
- Decision: 3개 소형 PNG는 일반 Git 바이너리로 관리한다. Rationale: 새 LFS 도구와 별도 전송 없이 복원 가능. Alternatives: art 전체나 제작용 중간 파일 복사 제외.
- 입력은 engine/events.py가 KEYUP·창 포커스 이벤트를 이미 보존한다. 새로운 기반 기능 누락은 발견하지 않았다.
