# Verification: 감사 1~5 수정

날짜: 2026-11-15. 상태: 진행 중. 사용자 요청 범위는 [spec.md](spec.md), 실행 작업은 [tasks.md](tasks.md)를 따른다.

## FR-001 / FR-005: 예약 공격·단일 행동 판정

- 변경 전 새 단위/통합 검사에서 공격 시간이70ms/79.6ms 앞서는 실패를 각각 확인했다.
- 변경 후 `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_character tests.unit.test_input_buffer tests.unit.test_charge_teleport tests.integration.test_character_scene tests.integration.test_dash_animation tests.integration.test_jump_animation tests.integration.test_charge_scene`: 62개 통과(캐릭터 증분 당시).
- 예약 만료와 대시 종료 경계,80ms 갱신에서 공격·베기 모두0초/첫 프레임과 다음50ms 동기화,100ms 허용/0.1ms 초과 만료, 착지 연결·공중 대시·전하 취소를 확인했다.
- game/character.py의 세 요청 플래그와 중복 허용 조건을 제거했다. tests/unit/test_charge_teleport.py의 내부 플래그 확인은 순간이동 직후 실제 상승 클립 확인으로 바꿨다.
- SDL 소프트웨어 렌더러 통합 검사다. 실제 창 관찰은 최종 통합에서 수행할 예정이며 사람의 조작감 확인으로 표시하지 않는다.

## FR-002: 표시 변경과 대기 클릭

- 기준 HEAD의 engine/display.py·loop.py를 메모리에 로드해 새 회귀를 실행하면 분리된 묶음에서 전하 x140 순간이동 대신 x0 공격으로 실패했다.
- `.\.venv\Scripts\python.exe -B -m unittest -v tests.unit.test_engine tests.integration.test_resize_input`: 수정 후27개 통과.
- F6+클릭 같은/다음 묶음, 전체화면·실제 마지막 창 크기 복귀, 무효 출력, 종료 우선, 입력 중 새 요청의 다음 프레임 보존을 확인했다. 실제 자산·SDL 소프트웨어 텍스처를 사용하고 창/이벤트 큐는 모의했다.

## FR-004: 예외 보관 중 참조 해제

- 새 약한 참조 회귀2개는 수정 전 월드 update/event와 UI update에서3건 실패했다. 내부 순회 finally에서 snapshot을 비운 후 통과했다.
- `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_game_framework.FrameworkTests.test_saved_dispatch_error_releases_unrelated_objects_after_close tests.unit.test_game_framework.CanvasTests.test_saved_update_error_releases_unrelated_nodes_after_close tests.unit.test_game_framework.FrameworkTests.test_mutation_in_mode_or_object_waits_for_next_dispatch tests.unit.test_game_framework.FrameworkTests.test_close_in_dispatch_stops_later_calls_and_cannot_reopen tests.unit.test_game_framework.CanvasTests.test_whole_dfs_snapshot_and_membership_check_even_when_hidden -q`: 5개 통과.
- 예외 traceback은 보존하면서 무관한 객체/노드가 close·GC 뒤 해제되는 것을 확인했다. 정상 순회 중 생성/제거·닫기 계약을 유지한다.

## Documentation / Git

- docs/architecture.md의 공격 진입·단일 판정을 갱신하고011 데이터 모델의 요청 플래그 표현을 현재 구조에 맞췄다. 게임 규칙·PNG·아트 기준·루트 README는 변경하지 않는다.
- feature/audit-fixes 생성 전 fetch 성공, 최신 origin/main은 이미 포함되어 merge가 Already up to date였다. 기존 점프 PNG8개와 tmp는 보존하고 커밋에서 제외한다.
- 다음 필수 작업: 전하 출력/성능 증분, 실제 SDL·전체 통합·converge.
