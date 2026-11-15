# Verification: 전하 순간이동

상태: 2026-11-15 요청 범위 구현·표적/실제 SDL 검증 완료. 사용자 직접 조작감은 미확인이다.

## 자동 검사

게임 .venv에서 최종 코드로 다음 26개 통과:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_charge_teleport tests.unit.test_teleport_link tests.integration.test_charge_scene tests.unit.test_input_buffer tests.integration.test_character_scene.CharacterSceneTests.test_sword_trails_keep_attack_position_and_expire_independently tests.integration.test_jump_animation.JumpAnimationTests.test_real_assets_and_start_air_land_locks tests.integration.test_dash_animation
```

| 요구사항 | 실제 근거 |
|---|---|
| FR-001 | 거리 안/밖/경계·48/144Hz 전환 일치·0초 반전 연속·PNG154프레임·파동 양끝 투명·premultiplied 색/알파 |
| FR-002,005 | 공격 대비 전하 선택 우선·중첩 가까운 대상·재사용·비활성 공격 전달·동일 위치 클릭의 선입력 제거/효과 중복 방지 |
| FR-003,004 | 공격·점프 준비/상승/낙하/착지·대시 준비/이동/복귀 취소·선입력 제거·낙하/착지·공중 대시 이력·도착 거절 |
| FR-006 | 승인 JS RGBA5개 SHA 기준·종료 빈 프레임·양 끝점 실제 SDL 백색 출력·역방향 독립100ms 수명·50ms 첫 갱신에서도 첫 섬광 보존 |
| FR-007 | viewport/DPI 배율 선택·무효 출력·텍스처 부분 초기화 실패/종료 해제·공유 아트 weakref 해제·캐시16개 제한 |
| FR-008 | 도착점 기준 즉시 활성화·낙하 중 기준점 고정·진행 중 위치 불변·마지막 유효 전하 예약·99/100ms 경계에서1회 실행·포커스/출력/대상 무효 취소·draw가 없어도 예약 효과100ms 수명 |
| 기존 행동 | 마지막 선입력·만료·공중 공격/대시 제한·포커스 상실·점프 단계·대시 효과·공격 잔광 |

최종 검토에서 찾은 장면 종료 후 CPU 아트 참조 잔류와 첫 갱신이 전류 첫 섬광을 건너뛰는 문제를 수정하고 해당 회귀 검사를 통과했다. 예약 실행으로 갱신 후 생성된 효과는0초 초기화해 다음 출력이 생략돼도 생성 후 시간이 버려지지 않게 했다. 0초 전환 갱신은 승인 참조와 같은 조기 반환을 사용한다.

## 아트 동일성·비용 검사

- 승인 link.js·Pixelfx의 샘플을 Node에서 생성하고 Python 포트와 대조했다. 서브에이전트의 일회성 비교에서 승인 PNG6종×13프레임(내보내기의 RGB 사전 곱 보정)78개와 직접 RGBA13경로×12샘플156개가 모두 바이트 일치했다. 상시 실행 근거는 test_teleport_link의 저장된 기준 SHA다.
- 전하 보간 최적화는 `git show 11f0345:game/charge.py`를 별도 모듈로 읽고 최종 ChargeArt.frame과72위상×5진행도360출력을 비교해 바이트 일치를 확인했다. 게임 Python의 일회성 표준입력 검사이며 파일·원본을 수정하지 않았다.
- 같은 보간 계산의 단독 평균은5.75→2.06ms로 줄었으며, 이후 픽셀 캐시를 지연 생성/16개 제한으로 바꿨다. 72위상을 순회한 ChargeArt의 tracemalloc 보유량은13.37MiB였다. 종료 weakref 해제는 위26개 검사에 포함한다.
- 전류300월드 단위4방향×12프레임의 교대 측정에서 래스터 중앙값11.7~11.8→8.1ms, 최적화 전후260샘플 출력 일치를 확인했다. 이 단독 수치는 전체 프레임 성능 보장이 아니다.

## 실제 SDL 창·화면 관찰

```powershell
.\.venv\Scripts\python.exe tests/smoke/charge_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/15/01a1dd61-8318-7af1-aa48-7798d2de5e0f
```

SDL 이벤트 큐 클릭으로 순간이동10회, 공격/점프 준비/대시 취소, 선입력3회를 포함한 연속 전하 이동, 가로/세로/대각/역방향 전류, F6/F11 후 선택, Escape 종료·자원 해제 통과. 최종 출력은 `teleports=10, buffered=3, max draw=22.0ms, median draw=6.8ms`였다. 진행 중 다음 전하 클릭이 즉시 이동하지 않고 예약으로 이어지는 구간을 포함한다. 현재 전류는 겹치지 않지만 CPU 래스터 처리로60fps 유지를 보장하지 않는다.

위 폴더의 character-charge-ready.png, character-charge-chain-1.png, character-charge-horizontal.png, character-charge-vertical.png 및100ms 압축 후 character-charge-first-3.png를 직접 열어 활성/비활성 색 구분·몸 중심 도착 후 낙하·고정 연결·1px 중심 전류와 잔광을 관찰했다. 창/전체화면 캡처도 smoke가 생성했다. 자동 입력/화면 관찰이며 사용자 직접 조작은 아니다.

## 문서·Git·미확인

origin/main6568aa7에서 feature/charge-teleport를 생성했고 마무리 fetch에서도 origin/main은 동일했다. 첫 증분은11f0345이며 연결·수명·성능 보완을 두 번째 증분으로 커밋한다. 사용자 점프 PNG8개와 기존 tmp는 변경/커밋하지 않았다. 검사는 현 작업트리의 사용자 PNG를 읽지만 이번 코드는 그 수정에 의존하지 않는다.

시스템/기본 조작/기술 구조/아트/게임 설계/progress/tests 안내를 실제 구현과 대조했다. 루트 README·엔진·의존성·공용 프레임워크는 범위 밖이라 변경하지 않았다. git diff --check와 관련 문서 로컬 링크 검사를 통과했다. 전체 회귀는 공용 엔진 변경이 없어 선택하지 않았다.

Converge에서 FR8개·수용 시나리오6개·SC4개·계획 선택5개·작업16개와 헌법5원칙을 대조했고 남은 필수 작업은 없다. 미구현·명세 모순·범위 초과 발견0건이며 새 Convergence 작업은 추가하지 않았다.

활성 거리300·배치·100ms 진행 시간·무소모 재사용·낙하 조작감과 최종 미술 품질은 사용자 플레이 전이다. CPU 래스터의 프레임 비용은 남아 있다. 피해·적·공중 공격·무적·장애물 처리는 이번 범위에서 제외했다. PR은 생성/게시하지 않았다.
