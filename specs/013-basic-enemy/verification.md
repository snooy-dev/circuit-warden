# Verification: 기본 적 전투

## Status

US1 적 표시·검 타격·처치 증분을 검사했다. 돌진·워든 피격·R은 다음 증분이며 전체 전투 완료가 아니다.

## 명령과 결과

작업트리: `C:/Users/Developer/.codex/worktrees/basic-enemy/circuit-warden`. 게임 Python은 기존 체크아웃의 `.venv`를 재사용하며 외부 의존성은 변경하지 않았다.

- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest tests.unit.test_basic_enemy tests.integration.test_character_scene tests.unit.test_character tests.unit.test_input_buffer -q`: 39개 통과. 검 판정 양방향·활성 경계·스윙 중복·거리·높이·긴 갱신 및 현재 이동·점프·대시·선입력을 확인했다.
- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest tests.integration.test_basic_enemy -v`: 2개 통과. 실제 PNG 좌우 출력·독립 이미지 수명·양방향 3회 처치를 확인했다.
- `D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m tests.smoke.basic_enemy_smoke --output-dir art/enemies/verification-us1`: PASS. 실제 SDL 이벤트로 검 공격·HP·처치·정리를 실행했다. 캡처의 초기 크기·접지·피격 표시를 직접 열어 관찰했다.
- hibit `finish_frames.py --strict`: 128×96·보이는 높이55·16색 팔레트·사용15색·팔레트 밖0·이진 알파·경고0. 첫 96×72 캔버스 시도는 canvas-fit으로 출력 없이 중단했고 128×96으로 확대해 통과했다. 단일 프레임이므로 프레임 간 깜박임 검사는 적용하지 않았다.

## 요구사항 대응

| 요구사항 | 현재 근거 |
|---|---|
| FR-001, FR-002, SC-001 | 실제 자산 통합2개·전투 유닛4개·SDL |
| FR-003~005, SC-002 | US2 미구현·미실행 |
| FR-006, SC-003 | 현행 입력·캐릭터·장면 표적 검사 |
| SC-DOC | 아트·구조·시스템·진행 상태를 현재 증분에 반영 |

## 한계

사용자 직접 조작감과 최종 미술 품질은 미확인이다. 적은 단일 자세이며 관절 보행 시트가 없다. 별도 작업트리의 미커밋 점프·전하 변경은 포함하지 않는다. 전체 회귀는 공통 엔진을 수정하지 않아 선택하지 않았다. 기존 art/warden 후보 링크 일부는 로컬 원본 체크아웃에서만 유효하다.
