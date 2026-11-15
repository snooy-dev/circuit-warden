# Verification: 전하 순간이동

상태: 2026-11-15 기본 전하 선택·취소·낙하 증분 검증. FR-006 전류 연결은 다음 증분이다.

## 자동 검사

게임 .venv에서 다음 명령으로 19개 통과:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_charge_teleport tests.integration.test_charge_scene tests.unit.test_input_buffer tests.integration.test_character_scene.CharacterSceneTests.test_sword_trails_keep_attack_position_and_expire_independently tests.integration.test_jump_animation.JumpAnimationTests.test_real_assets_and_start_air_land_locks tests.integration.test_dash_animation
```

| 요구사항 | 실제 근거 |
|---|---|
| FR-001 | 거리 안/밖/경계·48/144Hz 전환 일치·0초 반전 연속·PNG 154프레임·파동 양끝 투명·premultiplied 색/알파 |
| FR-002,005 | 공격 대비 전하 선택 우선·중첩 가까운 대상·재사용·비활성 공격 전달 |
| FR-003,004 | 공격·점프 준비/상승/낙하/착지·대시 준비/이동/복귀 취소·선입력 제거·낙하/착지·공중 대시 이력·도착 거절 |
| FR-007 | viewport/DPI 배율 선택·무효 출력·텍스처 부분 초기화 실패/종료 해제 |
| 기존 행동 | 마지막 선입력·만료·공중 공격/대시 제한·포커스 상실·점프 단계·대시 효과·공격 잔광 |

첫 실행에서 dt=0의 반전 값에 미세 오차를 발견해 참조 제어기와 동일한 0초 조기 반환으로 수정했다. 위 결과는 수정 후 결과다.

## 실제 SDL 창·화면 관찰

```powershell
.\.venv\Scripts\python.exe tests/smoke/charge_smoke.py --output-dir C:/Users/Developer/.codex/visualizations/2026/11/15/01a1dd61-8318-7af1-aa48-7798d2de5e0f
```

SDL 이벤트 큐를 통한 클릭으로 순간이동8회, 공격/점프 준비/대시 취소, 연속 전하 이동, F6/F11 후 선택, Escape 종료·자원 해제 통과. character-charge-ready.png·character-charge-chain-4.png를 직접 열어 활성/비활성 색 구분·도착 후 낙하를 관찰했다. 사용자 직접 조작은 아니다. 1회 실행 최대 draw 29.8ms(초기 업로드 포함)이며 전류 통합 후 비용을 다시 확인한다.

## 문서·Git·미확인

origin/main 6568aa7에서 feature/charge-teleport를 생성했다. 사용자 점프 PNG8개와 tmp는 변경/커밋하지 않는다. 테스트는 현 작업트리의 사용자 PNG를 읽지만 이번 코드는 해당 PNG 수정에 의존하지 않는다.

시스템/기본 조작/기술 구조/아트/게임 설계/progress에 사용자 입력 결정과 구현 상태를 반영했다. 루트 README·엔진·의존성·공통 프레임워크는 범위 밖이라 변경하지 않았다. git diff --check 통과. 전체 회귀는 공용 엔진 변경이 없어 선택하지 않았다.

FR-006·최종 연결 화면·converge는 남아 있다. 활성 거리·배치·무소모 재사용·낙하 조작감과 최종 미술 품질은 사용자 플레이 전이다.
