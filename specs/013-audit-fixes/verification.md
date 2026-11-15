# Verification: 감사 1~5 수정

날짜: 2026-11-15. 상태: 진행 중. 사용자 요청 범위는 [spec.md](spec.md), 실행 작업은 [tasks.md](tasks.md)를 따른다.

## FR-001 / FR-005: 예약 공격·단일 행동 판정

- 변경 전 새 단위/통합 검사에서 공격 시간이70ms/79.6ms 앞서는 실패를 각각 확인했다.
- 변경 후 `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_character tests.unit.test_input_buffer tests.unit.test_charge_teleport tests.integration.test_character_scene tests.integration.test_dash_animation tests.integration.test_jump_animation tests.integration.test_charge_scene`: 62개 통과(캐릭터 증분 당시).
- 예약 만료와 대시 종료 경계,80ms 갱신에서 공격·베기 모두0초/첫 프레임과 다음50ms 동기화,100ms 허용/0.1ms 초과 만료, 착지 연결·공중 대시·전하 취소를 확인했다.
- game/character.py의 세 요청 플래그와 중복 허용 조건을 제거했다. tests/unit/test_charge_teleport.py의 내부 플래그 확인은 순간이동 직후 실제 상승 클립 확인으로 바꿨다.
- SDL 소프트웨어 렌더러 통합 검사다. 실제 창 관찰은 최종 통합에서 수행할 예정이며 사람의 조작감 확인으로 표시하지 않는다.

## Documentation / Git

- docs/architecture.md의 공격 진입·단일 판정을 갱신하고011 데이터 모델의 요청 플래그 표현을 현재 구조에 맞췄다. 게임 규칙·PNG·아트 기준·루트 README는 변경하지 않는다.
- feature/audit-fixes 생성 전 fetch 성공, 최신 origin/main은 이미 포함되어 merge가 Already up to date였다. 기존 점프 PNG8개와 tmp는 보존하고 커밋에서 제외한다.
- 다음 필수 작업: 표시 전환·예외 참조 정리 증분, 전하 출력/성능, 실제 SDL·전체 통합·converge.
