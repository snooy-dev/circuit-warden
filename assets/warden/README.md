# 워든 게임 자산

사용자 지시로 잠정 승인 측면 idle 망토 바람 v2·Run v4·전기 베기 v4와 이번에 게임 사용으로 선택한 공격 v6 아웃라인 있음 시트를 변경 없이 복사했다. 런타임 파일명에는 버전을 붙이지 않는다. 원본은 art에 보존하며 최종 아트 품질 승인을 뜻하지 않는다.

| 게임 파일 | 원본 | SHA-256 |
|---|---|---|
| idle.png | art/warden/provisional-approved/idle-side-wind-v2/idle_right/sheet.png | 6cd0b5133576e6f73cb492a0f36e114c160371c33115bda0272d877f7735d506 |
| run_left.png | art/warden/provisional-approved/run-v4/run_left/sheet.png | 618ef3377b2682ee6d15ab4052a208f041562adcaed406a0361977ca7460940e |
| run_right.png | art/warden/provisional-approved/run-v4/run_right/sheet.png | c29d16562b7df8a8ec927b031ef1589bdf6252467afb648f1537af60977fc3aa |
| attack.png | art/warden/attack-sword-v6/bundle-outlined/sheet.png | e7a9a24a46feff5d20ffb20f032b57b9bbd67754c0263e8f5fb162458b7891e6 |
| sword_trail.png | art/warden/provisional-approved/sword-trail-electric-v4/trail-sheet.png | 379ebfc70867974cdb0afdf4b37bb5c5a5f5ccd931479d04857f887f1d48dc30 |

프레임은 좌상단부터 행 우선이다. animations.json의 기준점은 셀 좌상단 픽셀, 시간은 밀리초다. 제작용 이벤트·previewSpeed는 게임 규칙으로 가져오지 않았다.

공격은 이번 기본 조작 구현 요청으로 연결했다. 192×192·7열·7프레임·각 50ms, 기준점 (96,120), 단발이다. 왼쪽 공격은 런타임 수평 반전이다. 원본의 자세·전류·픽셀은 변경하지 않았다.

베기는 192×192·14열·14프레임·각 50ms, 기준점 (96,120)이다. 원본대로 캐릭터 뒤에서 재생한다. 공격 종료 뒤에도 시작 위치·방향을 유지하며 700ms에 소멸한다. 공격 v5와 무외곽선 v6 원본은 art와 이전 Git 커밋에 보존한다.

idle은 오른쪽 시트 48프레임·2초·기준점 (64,92)을 사용하고 왼쪽은 런타임에서 수평 반전한다. 원본 좌측 48프레임이 우측의 정확한 픽셀 반전임을 확인했다.
