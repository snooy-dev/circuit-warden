# Verification: 감사 1~5 수정

날짜: 2026-11-15. 상태: 수정·검증 완료. 사용자 요청 범위는 [spec.md](spec.md), 실행 작업은 [tasks.md](tasks.md)를 따른다.

## FR-001 / FR-005: 예약 공격·단일 행동 판정

- 변경 전 새 단위/통합 검사에서 공격 시간이70ms/79.6ms 앞서는 실패를 각각 확인했다.
- 변경 후 `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_character tests.unit.test_input_buffer tests.unit.test_charge_teleport tests.integration.test_character_scene tests.integration.test_dash_animation tests.integration.test_jump_animation tests.integration.test_charge_scene`: 62개 통과(캐릭터 증분 당시).
- 예약 만료와 대시 종료 경계,80ms 갱신에서 공격·베기 모두0초/첫 프레임과 다음50ms 동기화,100ms 허용/0.1ms 초과 만료, 착지 연결·공중 대시·전하 취소를 확인했다.
- game/character.py의 세 요청 플래그와 중복 허용 조건을 제거했다. tests/unit/test_charge_teleport.py의 내부 플래그 확인은 순간이동 직후 실제 상승 클립 확인으로 바꿨다.
- 표적 검사는 SDL 소프트웨어 렌더러다. 아래 최종 통합에서 실제 창도 관찰했으며 사람의 조작감 확인으로 표시하지 않는다.

## FR-002: 표시 변경과 대기 클릭

- 기준 HEAD의 engine/display.py·loop.py를 메모리에 로드해 새 회귀를 실행하면 분리된 묶음에서 전하 x140 순간이동 대신 x0 공격으로 실패했다.
- `.\.venv\Scripts\python.exe -B -m unittest -v tests.unit.test_engine tests.integration.test_resize_input`: 수정 후27개 통과.
- F6+클릭 같은/다음 묶음, 전체화면·실제 마지막 창 크기 복귀, 무효 출력, 종료 우선, 입력 중 새 요청의 다음 프레임 보존을 확인했다. 실제 자산·SDL 소프트웨어 텍스처를 사용하고 창/이벤트 큐는 모의했다.

## FR-004: 예외 보관 중 참조 해제

- 새 약한 참조 회귀2개는 수정 전 월드 update/event와 UI update에서3건 실패했다. 내부 순회 finally에서 snapshot을 비운 후 통과했다.
- `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_game_framework.FrameworkTests.test_saved_dispatch_error_releases_unrelated_objects_after_close tests.unit.test_game_framework.CanvasTests.test_saved_update_error_releases_unrelated_nodes_after_close tests.unit.test_game_framework.FrameworkTests.test_mutation_in_mode_or_object_waits_for_next_dispatch tests.unit.test_game_framework.FrameworkTests.test_close_in_dispatch_stops_later_calls_and_cannot_reopen tests.unit.test_game_framework.CanvasTests.test_whole_dfs_snapshot_and_membership_check_even_when_hidden -q`: 5개 통과.
- 예외 traceback은 보존하면서 무관한 객체/노드가 close·GC 뒤 해제되는 것을 확인했다. 정상 순회 중 생성/제거·닫기 계약을 유지한다.

## FR-003 / SC-002 / SC-003: 모양 유지·성능

- 게임 .venv에 NumPy2.5.4를 설치하고 requirements.txt에 고정했다. 외부 네트워크가 제한된 첫 설치는 DNS 오류로 실패했고 허용된 재실행으로 설치했다. 도구·전역 환경은 변경하지 않았다.
- `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_charge_teleport tests.unit.test_teleport_link tests.integration.test_charge_scene`: 18개 통과.
- 기준은 `a5f47a841aa2b0665438f936f8d8524b4a85d949`의 합성 코드다. 실제 SDL로 읽은154개 PNG 프레임과 72프레임×9값×3 bob의1,944 RGBA 합성을 고정 SHA로 비교했다. 부동소수 경계 인접값·난수·안정 상태도 포함한다. 전류 자체와 PNG는 수정하지 않았다.
- `.\.venv\Scripts\python.exe -X utf8 -B tests/performance/charge_benchmark.py --baseline a5f47a841aa2b0665438f936f8d8524b4a85d949`: 전후 텍스처 업로드847개 SHA `8b64c2c8df9cd52c42c5de06b5e83555464007d6170d6a4c189c47e7d070ecdd` 일치.
- 1280×720 SDL 소프트웨어 renderer, 전하5개, 고정1/60초×180프레임, 클릭14회 중 순간이동12회. 별도 동일성/워밍업 실행 후 전후 순서를 바꿔5쌍(각900프레임) 측정했다. GC는 기본 설정이다.

| 측정 | 변경 전 p95 | 변경 후 p95 | 최대 전→후 | 16.67ms 초과 전→후 |
|---|---|---|---|---|
| 픽셀 CPU | 22.175ms | 8.957ms(-59.6%) | 29.382→12.482ms | 302→0/900프레임 |
| update+draw+software present | 24.339ms | 10.838ms(-55.5%) | 31.228→14.992ms | 348→0/900프레임 |

p95는 실행별95백분위의 중앙값이다. 이벤트 펌프·실제 창/GPU/VSync·프레임 대기는 제외했다. SC-003의30% 개선과 이 측정의16.67ms 목표를 충족하며 다른 장비의 FPS 보장은 아니다.

## 통합·실제 SDL

- `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -q`: 161개 통과. 공통 엔진 입력 순서와 게임 상태 통합 때문에 한 번 선택했다.
- `.\.venv\Scripts\python.exe -B tests/smoke/charge_smoke.py --output-dir <세션 출력>`: 실제 SDL 순간이동10회·선입력2회·행동 취소·가로/세로/대각·F6/F11·Esc·자원 해제 통과. 캡처 보존 실행은 max draw9.8ms, median1.1ms였다.
- `.\.venv\Scripts\python.exe -B tests/smoke/audit_smoke.py --output-dir <세션 출력>`: 실제 SDL 큐에서 F6 다음 묶음 클릭이 x140 전하에 도착하고1280→1024 창 전환을 확인했다. 예약 공격 재현에는 장면 dt만 고정하며80ms 뒤 캐릭터/베기 모두0초·첫 프레임, 다음50ms 동기화·Esc·자원 해제를 통과했다.
- 세션 출력: `C:/Users/Developer/.codex/visualizations/2026/11/15/01a1dde8-74e5-7132-8171-12f342fb4cc4/audit-013`. character-charge-first-1.png·character-charge-horizontal.png·character-audit-buffered-attack-first.png를 직접 열어 전류 연결·공격 시작 자세를 확인했다. 사용자 손 조작 검사가 아니다.

## Documentation / Git

- docs/architecture.md의 공격 진입·단일 판정을 갱신하고011 데이터 모델의 요청 플래그 표현을 현재 구조에 맞췄다. 게임 규칙·PNG·아트 기준·루트 README는 변경하지 않는다.
- feature/audit-fixes 생성 전 fetch 성공, 최신 origin/main은 이미 포함되어 merge가 Already up to date였다. 기존 점프 PNG8개와 tmp는 보존하고 커밋에서 제외한다.
- docs/architecture.md에 표시 순서·내부 참조 해제·배열/바이트 캐시 구분을 반영했다. docs/tooling.md는 게임 NumPy 설치를, tests/README.md는 재현·성능 명령을 설명한다. 기본 조작·전하 시스템·아트 기준은 규칙·모양이 같아 변경하지 않았다.
- 별도 읽기 전용 검토에서 새 실행 결함은 없었고 픽셀 배열 캐시와 완성 bytes 캐시의 문서 표현을 수정했다. 변경 관련 Markdown23개 로컬 링크·git diff --check·기존 점프 PNG8개 SHA-256 보존을 확인했다. pip check도 No broken requirements found였다.
- 최종 converge 대조에서 FR6개·SC4개·수용 시나리오6개·작업16개에 대응하는 구현/근거와 문서가 일치했다. 새 계층·아트·게임 규칙 추가 없이 요청5건을 처리했고 추가 구현 작업은 없었다.
- PR/push·사용자 직접 조작감·다른 GPU/장치의 성능 검사는 수행하지 않았다. 요청된 로컬 수정·검증 외 필수 작업은 없다.
