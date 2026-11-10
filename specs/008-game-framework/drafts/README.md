# 비활성 테스트 참고자료

[test_game_framework.py.txt](test_game_framework.py.txt)는 GameMode가 객체를 소유하던 초안의 보존 자료다. 현재 레벨 소유·렌더링 씬·게임모드 분리 계획과 맞지 않는다. 실행하거나 현재 수용 기준으로 사용하지 않는다. 승인 후 tests/test_game_framework.py는 새 명세에 맞게 작성한다.

[test_world_rendering.py.txt](test_world_rendering.py.txt)는 P3 선행 커밋 대기 중 준비한 현재 월드 계약의 검사 초안이다. 구문 검사만 통과했으며 P3 구현 성공 근거가 아니다. P2 검증 커밋 통합 후 실제 API와 대조해 `tests/`로 옮기고 실행한다.
