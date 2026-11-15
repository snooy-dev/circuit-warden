# Verification: 전하 순간이동

상태: 2026-11-15 요청 범위 구현·표적/실제 SDL 검증 완료. 사용자 요청으로 전하 표시보다 넓게 클릭 반경을24→48로 확대했다. 새 클릭 판정과 상승 관성의 조작감은 사용자 재확인 전이다.

## 자동 검사

게임 .venv에서 클릭 판정 변경에 대응하는 기존3개를 조정해 통과했다. 전하 중심에서44월드 단위 떨어진 표시 밖 클릭·50월드 단위의 판정 밖 공격·두 판정 중 가까운 대상·viewport/DPI·넓어진 영역에서 마지막 유효 선입력을 확인했다.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.integration.test_charge_scene.ChargeSceneTests.test_selection_priority_overlap_reuse_and_inactive_fallback tests.integration.test_charge_scene.ChargeSceneTests.test_resize_dpi_and_invalid_output_use_current_coordinates tests.integration.test_charge_scene.ChargeSceneTests.test_destination_activation_and_last_valid_buffer
```

7ce6f52의 상승 관성 표적7개와 ebbc810의 기반26개 중 이번 변경과 무관한 검사 결과는 재사용한다. 런타임 변경은 game/charge.py의 CLICK_RADIUS 한 값뿐이며 기존 선택/선입력 호출부·좌표 변환·자산은 유지한다.

| 요구사항 | 실제 근거 |
|---|---|
| FR-001 | 거리 안/밖/경계·48/144Hz 전환 일치·0초 반전 연속·PNG154프레임·파동 양끝 투명·premultiplied 색/알파 |
| FR-002,005 | 표시 밖 선택·판정 밖 공격·공격 대비 전하 선택 우선·확대된 판정 중첩에서 가까운 대상·재사용·비활성 공격 전달·동일 위치 클릭의 선입력 제거/효과 중복 방지 |
| FR-003,004 | 공격·점프 준비/상승/낙하/착지·대시 준비/이동/복귀 취소·선입력 제거·작은 상승/낙하/착지·공중 대시 이력·도착 거절 |
| FR-006 | 승인 JS RGBA5개 SHA 기준·종료 빈 프레임·양 끝점 실제 SDL 백색 출력·역방향 독립100ms 수명·50ms 첫 갱신에서도 첫 섬광 보존 |
| FR-007 | viewport/DPI 배율 선택·무효 출력·텍스처 부분 초기화 실패/종료 해제·공유 아트 weakref 해제·캐시16개 제한 |
| FR-008 | 도착점 기준 즉시 활성화·공중 이동 중 기준점 고정·진행 중 위치 불변·마지막 유효 전하 예약·99/100ms 경계에서1회 실행·포커스/출력/대상 무효 취소·draw가 없어도 예약 효과100ms 수명 |
| 기존 행동 | 마지막 선입력·만료·공중 공격/대시 제한·포커스 상실·점프 단계·대시 효과·공격 잔광 |

최종 검토에서 찾은 장면 종료 후 CPU 아트 참조 잔류와 첫 갱신이 전류 첫 섬광을 건너뛰는 문제를 수정하고 해당 회귀 검사를 통과했다. 예약 실행으로 갱신 후 생성된 효과는0초 초기화해 다음 출력이 생략돼도 생성 후 시간이 버려지지 않게 했다. 0초 전환 갱신은 승인 참조와 같은 조기 반환을 사용한다.

## 아트 동일성·비용 검사

- 승인 link.js·Pixelfx의 샘플을 Node에서 생성하고 Python 포트와 대조했다. 서브에이전트의 일회성 비교에서 승인 PNG6종×13프레임(내보내기의 RGB 사전 곱 보정)78개와 직접 RGBA13경로×12샘플156개가 모두 바이트 일치했다. 상시 실행 근거는 test_teleport_link의 저장된 기준 SHA다.
- 전하 보간 최적화는 `git show 11f0345:game/charge.py`를 별도 모듈로 읽고 최종 ChargeArt.frame과72위상×5진행도360출력을 비교해 바이트 일치를 확인했다. 게임 Python의 일회성 표준입력 검사이며 파일·원본을 수정하지 않았다.
- 같은 보간 계산의 단독 평균은5.75→2.06ms로 줄었으며, 이후 픽셀 캐시를 지연 생성/16개 제한으로 바꿨다. 72위상을 순회한 ChargeArt의 tracemalloc 보유량은13.37MiB였다. 종료 weakref 해제는 기반26개 검사에 포함하며 관련 자원 코드는 변경하지 않았다.
- 전류300월드 단위4방향×12프레임의 교대 측정에서 래스터 중앙값11.7~11.8→8.1ms, 최적화 전후260샘플 출력 일치를 확인했다. 이 단독 수치는 전체 프레임 성능 보장이 아니다.

## 실제 SDL 창·화면 관찰

```powershell
.\.venv\Scripts\python.exe tests/smoke/charge_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/15/01a1dd61-8318-7af1-aa48-7798d2de5e0f
```

SDL 이벤트 큐 클릭으로 순간이동10회, 공격/점프 준비/대시 취소, 선입력2회를 포함한 연속 전하 이동, 가로/세로/대각/역방향 전류, F6/F11 후 선택, Escape 종료·자원 해제 통과. 중심에서50단위 클릭은 공격,44단위 클릭은 순간이동/선입력으로 처리됐으며 창 크기 변경·전체화면에서도44단위 클릭으로 이동했다. 최종 출력은 `teleports=10, buffered=2, max draw=24.7ms, median draw=7.5ms`였다. 현재 전류는 겹치지 않지만 CPU 래스터 처리로60fps 유지를 보장하지 않는다.

위 폴더의 character-charge-attack-cancel.png를 직접 열어 표시 밖 클릭 이후 전하에 도착하고 전류가 표시된 화면을 관찰했다. smoke는 약60ms의 양의 수직 속도와 약250ms의 도착 높이 위 낙하도 검사한다. 자동 입력·화면 관찰이며 사용자 직접 플레이 평가는 아니다.

## 문서·Git·미확인

origin/main6568aa7에서 feature/charge-teleport를 생성했고 이번 재개에서도 fetch 후 같은 origin/main과 merge --no-commit의 Already up to date를 확인했다. 기반 증분은11f0345·ebbc810·7ce6f52이며 클릭 판정 확대는 별도 증분으로 커밋한다. 사용자 점프 PNG8개와 기존 tmp는 변경/커밋하지 않았다. 검사는 현 작업트리의 사용자 PNG를 읽지만 이번 코드는 그 수정에 의존하지 않는다.

시스템/progress/spec/plan/tasks를 실제 구현과 맞췄다. 기본 조작·기술 구조·아트·게임 설계·검사 명령은 유지되므로 해당 기준 문서의 변경 영향은 없다. 루트 README·엔진·의존성·공용 프레임워크는 변경하지 않았다. git diff --check와 관련 문서 로컬 링크 검사를 통과했다. 전체 회귀는 공용 엔진 변경이 없어 선택하지 않았으며 단순 값 변경용 새 테스트는 만들지 않았다.

Analyze에서 FR-002의 확대 판정과 기존 선택/선입력/좌표 변환의 충돌이 없음을 확인했다. Converge에서 변경된 FR-002·FR-007·FR-008·T020~T021과 코드/검증/docs를 대조했고 전체21개 작업 중 남은 필수 작업은 없다. 새 Convergence 작업은 추가하지 않았다.

활성 거리300·클릭 반경48·배치·100ms 진행 시간·무소모 재사용·상승 관성 조작감과 최종 미술 품질은 사용자 재확인 전이다. 넓어진 영역에서 공격 대신 전하를 선택하는 빈도는 직접 플레이로 판단해야 한다. CPU 래스터의 프레임 비용은 남아 있다. 피해·적·공중 공격·무적·장애물 처리는 이번 범위에서 제외했다. PR은 생성/게시하지 않았다.
