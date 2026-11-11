# 워든 게임 자산

사용자 지시로 잠정 승인 idle v7·Run v4·공격 v5 시트를 변경 없이 복사했다. 런타임 파일명에는 버전을 붙이지 않는다. 원본은 art에 보존하며 최종 아트 품질 승인을 뜻하지 않는다.

| 게임 파일 | 원본 | SHA-256 |
|---|---|---|
| idle.png | art/warden/provisional-approved/idle-unarmed-v7/unarmed/sheet.png | 232fbad18ced07f1e3f9045cdc61612ac82b38cfc5b85b5070c7d0f8869b3979 |
| run_left.png | art/warden/provisional-approved/run-v4/run_left/sheet.png | 618ef3377b2682ee6d15ab4052a208f041562adcaed406a0361977ca7460940e |
| run_right.png | art/warden/provisional-approved/run-v4/run_right/sheet.png | c29d16562b7df8a8ec927b031ef1589bdf6252467afb648f1537af60977fc3aa |
| attack.png | art/warden/provisional-approved/attack-v5/sheet.png | 96ef8186c62a36c0d888eb43e22b2c58b320fcf82638844fc4619e4cba249405 |

프레임은 좌상단부터 행 우선이다. animations.json의 기준점은 셀 좌상단 픽셀, 시간은 밀리초다. 제작용 이벤트·previewSpeed는 게임 규칙으로 가져오지 않았다.

공격은 이번 기본 조작 구현 요청으로 연결했다. 192×192·7열·7프레임·각 50ms, 기준점 (96,120), 단발이다. 왼쪽 공격은 런타임 수평 반전이다. 원본의 자세·전류·픽셀은 변경하지 않았다.
