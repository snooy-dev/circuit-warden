# Verification: 기본 적 전투

## Status

2026-11-15: 원화 기반 hibit 적 1종의 양방향 전투 구현·선택한 검증 완료. 사용자 직접 조작감과 최종 미술 판단은 미확인이다.

## 최신 main 통합 검증 — 2026-11-16

사용자 요청으로 `origin/main` 9f1d72c를 `feature/basic-enemy`에 merge했다. 시작 시 워크트리는 깨끗했으며 원본 D:/GitHub/circuit-warden은 수정하지 않았다. 충돌8파일은 입력 action 반환/시간 offset, 전투·전하 배치, 두 기능의 현재 문서를 함께 유지해 해결했다. 적 PNG·이동600ms·체력바 제거와 최신 전하·워든 PNG를 보존한다.

- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest discover -s tests -p 'test_*.py' -q`: **194개 통과**. 최초 표적 실행은 전하 없는 장면을 가정한 테스트 fixture에서19개 오류가 났으며 전하 아트 mock·클릭 좌표·유지 객체 기대값을 갱신했다. 런타임 검증을 우회하지 않았다.
- 새 결합 회귀3개는 순간이동의 공격 취소와 체력/보호 보존, 전투 판정 후 예약 이동과 사망 예약 취소, R의 효과/예약/제외 상태 정리와 아트 재사용을 검사한다.
- 후속 읽기 전용 리뷰에서 사망 중 전류 고정과 R 이후 전하 활성 상태 갱신 경계를 확인했다. 사망 시 전류 제거·후처리 활성 재계산을 보완하고 `... -B -m unittest tests.integration.test_basic_enemy tests.integration.test_charge_scene -q`: **24개 통과**. 짧은20ms 치명 프레임에도 전류가 남지 않음을 포함한다. 전체194개 결과는 이 작은 보완 전이며 관련24개로 재검증했다.
- `... -B -m tests.smoke.basic_enemy_smoke --output-dir art/enemies/verification-main-merge`: **PASS**. 실제 SDL 공방·점프 회피·사망·R·처치·양방향·resize·해제를 확인했다. 접근 중간 캡처를 열어 전하5개와 적의 동시 표시·접지를 확인했다.
- `... -B tests/smoke/charge_smoke.py --output-dir "$env:TEMP/circuit-warden-enemy-merge-charge"`: **PASS**, 순간이동13회·예약3회·취소·연속 선택·resize/fullscreen·정리. 명령 세션별 임시 경로가 달라 후속 세션에서는 이 캡처를 열지 않았으며 통과한 자동 SDL 실행 결과만 근거로 삼는다.
- SDL 두 검사는 사망 전류/활성 상태 보완 전 실행이다. 해당 보완은 실제 PNG 기반 통합24개로 확인했고 창 검사는 반복하지 않았다. 사용자 직접 조작감·밸런스는 미확인이다.
- FR-008·계획·T020~021과 현재 시스템/구조/게임 설계/진행 상태를 대조했다. 충돌 표시와 diff 공백을 검사하고 두 부모 이력을 보존한다. push·PR·main 브랜치 변경은 하지 않는다.

## 이동 모션 속도 후속 조정

사용자의 다리 움직임이 빠르다는 지적에 따라 이동8프레임의 프레임당 시간을50→75ms, 한 주기를400→600ms로 조정했다. 이동 속도100·공격 설정·PNG는 유지했다.

- 게임 Python의 `-B -` 인라인 SDL 검사: 실제 클립8×75ms, 50ms에서 첫 프레임 유지·75ms에서 다음 프레임·600ms에서 반복과 같은 시간의60월드 단위 이동을 확인했다. 실제 창 출력·캡처·자원 해제 PASS. 캡처는 `art/enemies/verification-slower-walk/character-slower-walk.png`다.
- HEAD와 JSON을 비교해 이동 프레임 시간 외 설정이 같고 PNG SHA256이 기존 값과 같음을 확인했다. 전체 전투 회귀는 시간 설정만 변경해 재실행하지 않았다. 사용자 체감 확인은 남아 있다.
- 아트 기준·진행 상태·기존 계획의 현재 주기를600ms로 맞췄다.

## 이동·공격 클립 통합 후속 검증

FR-007의 사용자 요청과 리깅 우선·어색하면 이미지 포즈 전환이라는 답변에 따라 로컬 generate2dsprite의 출력 클립을 게임에 적용했다. 영상 경로는 없었으며 내장 ImageGen의 키포즈와 원본 리깅의 작은 중간 포즈2장을 사용했다. 기존 행동·피해 시간은 유지하고 전투 단계의 소비 시간만 SpritePlayer에 전달한다. 기존 스프라이트의 전체 크기 변형은 제거했다.

- `git fetch origin` 뒤 `git merge --no-commit origin/main`: Already up to date. 사용자 원본 체크아웃은 수정하지 않았다.
- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy -q`: **20개 통과**. 긴 dt의 회복 재생 시간·정확한 전환 경계의 첫 프레임·R 초기화·PNG 좌우 렌더·리소스 수명과 기존 전투 판정을 확인했다.
- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest tests.integration.test_character_scene.CharacterSceneTests.test_real_asset_draw_and_fresh_scene_lifetime tests.integration.test_character_scene.CharacterSceneTests.test_invalid_asset_on_enter_releases_already_loaded_texture -q`: **2개 통과**. 선택적 자산 root를 추가한 기존 로더의 워든 기본 호출과 실패 정리를 확인했다.
- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m tests.smoke.basic_enemy_smoke --output-dir art/enemies/verification-motion-final`: **PASS**. 실제 SDL 이동 중간·예고 최대·돌진·회복, 점프 회피·피격·사망·R·양방향 타격·처치·리사이즈·텍스처 해제를 확인했다. 예고/돌진 캡처를 열어 접지·포즈·체력바 미표시를 관찰했다.
- 원본 idle 픽셀 보존·공통160×112 셀·피벗(80,100)·팔레트 밖0·이진 알파·잘림0을 검사했다. 로컬 `build_animation_clips.py --strict` 경고0, `export_engine.py --target aseprite-json --padding 0 --extrude 0` 왕복 검사 PASS. 최종 이동 중간톤3색을 기존 팔레트의 어두운 단계로 맞추고 알파·금속색 보존 및 게임의16개 재생 위치/시간이 최종 Forge 출력과 같은지 확인했다. 색 보정 후 실제 SDL 이동 캡처(`art/enemies/verification-motion-palette/character-enemy-walk-palette.png`)도 확인했다. 코드·모양·시간이 같아 앞선 전투 검사 결과를 재사용했다. 상세 원본 QA 경고와 후처리 근거는 `assets/enemies/metal_dust_motion.json`에 보존했다. 이동 원본의 pixel-reduction 2.882<4 경고는 실제 해상도 한계로 남기고 게임 크기에서 확인했다.
- `git diff --check`와 새 로컬 링크·최종 시트 SHA-256을 확인했다.
- 시스템·아트 기준·구조·progress·검사 안내 및 FR-007·plan·T018~019를 대조했다. 새 범용 엔진 기능이나 전투 규칙은 추가하지 않았다. 전체 회귀는 재실행하지 않았다. 생성 포즈의 작은 질감 변화와 돌진1포즈 유지, 사용자 직접 품질 평가는 남는다.

## 크기·디테일 보정 자산 통합 후속 검증

사용자의 적 크기·원화 디테일 보정 및 워든과 같은 픽셀 크기 요청에 따라 새 hibit 자산을 연결했다. 로더의 셀·피벗과 몸통 판정을 맞췄으며 공격 경계·돌진 접촉 시각·공중 회피 검사의 배치를 새 판정 크기에 맞게 이동했다. 전투 규칙 코드는 판정 크기 외에 변경하지 않았다.

- `git fetch origin` 후 `git log --oneline HEAD..origin/main`은 비어 있었고 `git merge --no-commit origin/main`은 Already up to date였다.
- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy -q`: **19개 통과**. 활성 구간·접촉 경계·점프 높이·실제 PNG 양방향 출력·수명을 확인했다.
- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m tests.smoke.basic_enemy_smoke --output-dir art/enemies/verification-detail-v2`: **PASS**. 실제 SDL의 점프 회피·피격·사망·R·양방향 타격·처치·창 크기 변경을 확인했다. 초기 캡처에서 워든과 적의 크기·접지·체력바 미표시를 관찰했다.
- 자산 크기128×104·알파 범위(6,14,121,92)·16색·팔레트 밖0·이진 알파·메타데이터/해시 일치를 확인했다. `git diff --check`와 새 로컬 참조 경로를 확인했다. 원본1px=1월드 단위이며 예고·돌진의 기존 자세 변형은 유지한다.
- `docs/art-direction.md`, `docs/systems/basic-enemy.md`, `docs/progress.md`와 FR-001·계획·T017을 동기화했다. 엔진 구조·입력·API는 바뀌지 않아 architecture·검사 안내 수정은 필요 없다. 전체 회귀는 재실행하지 않았으며 단일 자세·사용자 직접 미술 평가 미확인은 남는다.

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
| FR-007 | 모션 시간 경계·긴 dt·R·공유 로더 및 실제 이동/공격 PNG·SDL |
| SC-002 | 최종 SDL smoke와 캡처 관찰 |
| SC-DOC | 시스템 규칙·기술 구조·아트·검사 안내·진행 상태 동기화 |

Spec Kit converge는 후속 요구사항 FR-007·작업 T018~019까지 코드·자산·docs·선택한 검증과 대조했고 남은 필수 구현이나 검증 누락을 발견하지 않았다. 첫 표시·검 타격 증분은 f5e518b로 보존했다.

## 한계와 미실행

- 사용자 직접 조작감·전투 밸런스·최종 미술 품질은 미확인이다. 이동 포즈에는 작은 질감 변화가 있고 공격은 적은 키포즈로 구성된다. 돌진은 전용1포즈를 유지하면서 게임 위치가 이동한다.
- 워든의 한 갱신 안 경로는 시작과 끝 사이의 선형 근사다. 적 경로는 단계별 선형 구간이다. 같은 갱신의 치명 검이 돌진보다 우선하는 현재 규칙을 유지한다.
- 패링·전하·전체 맵/승패·다수 적·전체 회귀는 범위 밖이다. 공통 엔진을 수정하지 않아 전체 회귀는 선택하지 않았다.
- 기존 체크아웃의 미커밋 점프·전하 변경은 건드리거나 포함하지 않았다. 과거 art/warden 후보 링크 일부는 원본 체크아웃에만 파일이 있으며 이번 자산과 새 링크는 작업트리에 존재한다.
