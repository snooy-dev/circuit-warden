# Verification: 기본 적 전투

## Status

2026-11-15: 원화 기반 hibit 적 1종의 양방향 전투 구현·선택한 검증 완료. 사용자 직접 조작감과 최종 미술 판단은 미확인이다.

## 체력바 제거 후속 검증

사용자 요청으로 워든과 적의 체력바 그리기·미사용 함수를 제거했다. 내부 체력·피해·처치·재시작은 유지했다.

- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m tests.smoke.basic_enemy_smoke --output-dir art/enemies/verification-no-health-bars`: PASS. 실제 SDL 공방·회피·사망·R·처치·정리를 확인했고 초기 캡처를 열어 양쪽 체력바가 없음을 관찰했다.
- `rg`로 미사용 체력바 함수·호출이 남지 않았음을 확인하고 `git diff --check`를 통과했다.
- 명세 FR-001·계획·T016·시스템·구조를 대조했으며 converge에 남은 작업은 없다. 아래 자동 검사64개 결과는 체력바 제거 이전 결과다. 이번에는 출력만 삭제했으므로 자동·전체 회귀를 재실행하지 않고 SDL 검사로 확인했다.

## 환경과 명령

작업트리: `C:/Users/Developer/.codex/worktrees/basic-enemy/circuit-warden`, 브랜치 `feature/basic-enemy`. 최신 origin/main을 fetch한 6568aa7에서 분리했다. 게임 Python은 기존 체크아웃의 `.venv`를 재사용하며 의존성을 변경하지 않았다.

- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy tests.integration.test_character_scene tests.integration.test_dash_animation tests.integration.test_jump_animation tests.unit.test_character tests.unit.test_input_buffer -q`: **64개 통과**. 전투 유닛16개, 실제 자산 전투 통합3개와 현재 입력·점프·대시·캐릭터 장면 검사를 포함한다.
- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m tests.smoke.basic_enemy_smoke --output-dir art/enemies/verification-final`: **PASS**. 실제 SDL 이벤트로 접근·예고·돌진·회복, 점프 회피, 5회 피격·사망 정지, R, 움직이는 적 3회 처치, 좌측 공격, 창 크기 변경과 자원 해제를 확인했다. 반격 검사에서는 초기 위치·방향을 시험 설정하며 적 AI는 계속 동작한다. 별도 좌측 공격 사례는 적을 회복 상태에 고정한다.
- 최종 캡처의 초기 크기·접지·피격 표시·재시작을 열어 확인했다. 앞선 캡처에서 예고 압축·공중 회피·사망 표시도 관찰했다. 화면 자료는 로컬 `art/enemies/verification-final/`에 보관한다.
- hibit `finish_frames.py --strict`: 128×96, 보이는 높이55, 16색 팔레트·사용15색, 팔레트 밖0, 이진 알파, 경고0. 첫 96×72 시도는 canvas-fit으로 출력 없이 중단하고 캔버스를 확대해 통과했다. 단일 프레임이므로 프레임 간 깜박임은 검사 대상이 아니다.
- `git diff --check`: 통과. 변경 문서의 신규 로컬 링크와 코드·요구사항 대응을 확인했다.

## 판정 결함 수정

프레임 끝의 적 위치로 검을 판정하던 구현은 0.10초 갱신에서도 활성 중 이탈한 적을 놓치고 활성 종료 후 진입한 적을 잘못 맞혔다. 보호 중에만 스친 돌진도 갱신 끝에 보호가 만료되면 피해를 줬다. 이를 재현한 뒤 검 활성 시간, 적의 단계별 경로, 실제 최초 접촉 시각을 교차하도록 수정했다. 워든이 먼저 접촉한 뒤 이동한 경우와 선입력 분할에서 첫 활성 구간이 덮이는 경우도 회귀로 고정했다. 활성 시작0.10초 포함·종료0.20초 제외를 확인했다.

## 요구사항 대응

| 요구사항 | 현재 근거 |
|---|---|
| FR-001 | 실제 PNG 좌우 출력·높이·피벗·장면 수명 및 SDL |
| FR-002, SC-001 | 양방향·활성 경계·움직이는 적 접촉·중복 피해·3회 처치 |
| FR-003 | 접근·방향 고정·돌진·회복·수직 회피 유닛 및 SDL |
| FR-004 | 최초 접촉 시 보호·만료·체력 하한·사망 정지·대시 중 피격 |
| FR-005 | 사망/처치/공격 중 R, 유지키·효과 제거·텍스처 재사용 |
| FR-006, SC-003 | 기존 입력·점프·대시·선입력 회귀, 잔상 비피해 |
| SC-002 | 최종 SDL smoke와 캡처 관찰 |
| SC-DOC | 시스템 규칙·기술 구조·아트·검사 안내·진행 상태 동기화 |

Spec Kit converge는 요구사항6개·성공 기준4개·수용 사례6개·작업16개와 기술 선택을 대조했고 남은 필수 구현이나 검증 누락을 발견하지 않았다. 첫 표시·검 타격 증분은 f5e518b로 보존했다.

## 한계와 미실행

- 사용자 직접 조작감·전투 밸런스·최종 미술 품질은 미확인이다. 적은 단일 자세의 변형이며 관절 보행 시트가 없다.
- 워든의 한 갱신 안 경로는 시작과 끝 사이의 선형 근사다. 적 경로는 단계별 선형 구간이다. 같은 갱신의 치명 검이 돌진보다 우선하는 현재 규칙을 유지한다.
- 패링·전하·전체 맵/승패·다수 적·전체 회귀는 범위 밖이다. 공통 엔진을 수정하지 않아 전체 회귀는 선택하지 않았다.
- 기존 체크아웃의 미커밋 점프·전하 변경은 건드리거나 포함하지 않았다. 과거 art/warden 후보 링크 일부는 원본 체크아웃에만 파일이 있으며 이번 자산과 새 링크는 작업트리에 존재한다.
