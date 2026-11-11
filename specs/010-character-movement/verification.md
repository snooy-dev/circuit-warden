# Verification: 캐릭터 표시와 좌우 이동

상태: 표시·이동 구현 및 자동/실제 SDL 검증 완료. 사용자 직접 조작·플레이 품질은 미확인. 엔진 PR #2와 feature/character-movement 분기 완료.

## Analyze

FR-001/006→T003/004, FR-002~005→T005~007, FR-DOC/SC-DOC→T002/008/009. 7개 요구 모두 작업과 연결되며 명세·계획·작업 간 차단 충돌은 없다. 임시 수치와 게임 규칙 미정을 구분했다. 확장 hooks 파일 없음. 최종 미확인: 사용자 직접 조작·플레이 품질. 실제 SDL 자동 입력·화면 관찰은 아래에 기록한다.

## P1 에셋 배치

표준 pathlib/struct/hashlib/json으로 원본과 복사 PNG 3개의 SHA-256 일치, PNG IHDR 크기·셀 개수·프레임 시간·기준점을 확인했다. idle 1024×624=48셀·2000ms, Run 좌/우 각 1024×208=16셀·480ms이며 셀은 모두 128×104다. 게임 이름에 버전이 없고 출처·해시를 assets/warden/README.md에 보존했다. 메타데이터의 제작용 previewSpeed·이벤트는 가져오지 않았다. .gitattributes는 PNG binary이며 LFS/의존성 추가 없음.

architecture·art-direction·progress·docs/README에 검사 범위/게임 복사본과 구현 중 상태를 반영했다. 실제 게임 코드 검증은 다음 증분이며 P1을 게임 동작 완료로 표시하지 않는다.

## P2 표시·이동 검증

| 명령·검사 | 실제 결과 |
|---|---|
| 구현 전 새 캐릭터 검사 실행 | 예상 실패 2개: game 모듈 없음 |
| 게임 Python -B -m unittest discover -s tests -v (게임 사본 cwd) | 전체 **116개 통과** (기존 106 + 신규 10) |
| runpy로 main·demos.check 진입점 검사, Engine.run 대역 | 각 장면으로 진입하는 호출 확인 |
| 게임 Python -B tests/smoke/character_smoke.py --output-dir 프로젝트 밖 기존 폴더 (실행 시 절대 경로) | 실제 창 검사 종료 0. idle/우Run/반대입력/좌Run/해제/포커스상실/resize/fullscreen/Escape/cleanup PASS |
| character-run-right.png·character-idle-left.png 관찰 | 바닥선의 발 기준점, 전용 Run, 반전 idle, 투명 배경·시트 자르기 관찰 |
| 실제 main.py를 루트 main 작업 폴더에서 절대 경로로 실행 | 게임 창과 idle 출력 확인, art 경로 없이 실행됨 |
| 데스크톱 창 캡처 | 실제 캐릭터 창을 관찰했으나 다른 창이 일부 가림. 이후 전경 활성화는 `foreground window did not report a process id`로 실패해 데스크톱 키 입력 검증 근거로 쓰지 않음 |

smoke의 첫 호출은 출력 폴더가 없어 사전 인자 검사로 종료 2였다. 폴더를 만든 뒤 동일 검사로 통과했으며 런타임 결함이 아니다. 자동 SDL 이벤트와 실제 물리 키 입력·사용자 확인은 서로 다르다. 위 PNG는 실제 SDL 렌더러에서 읽은 출력이며 게임 에셋을 합성한 목업이 아니다.

## 요구사항·문서 대조

- FR-001/006·SC-001: 에셋 증분 baaeb2c. 원본/복사 해시 일치 및 PNG binary 속성의 diff/merge/text unset 확인. 이름·규격·시간·출처 보존.
- FR-002: main 게임 진입, demos.check 별도 진입, __file__ 기준 경로. 실제 PNG 로딩/출력과 장면 재생성 시 새 이미지·실패 후 이미 로딩한 texture 해제를 확인했다.
- FR-003·SC-002: 같은 방향 별칭·반복 입력·상쇄·일부 해제·마지막 방향·분할 dt의 이동량을 검사했다.
- FR-004: 48/16/16프레임, 원본 시간과 pivot·행 우선 영역·전용 좌우 Run·왼쪽 idle 반전·같은 클립 시간 유지·전환 첫 프레임을 검사했다.
- FR-005: 포커스 상실·최소화 유지 키 제거, 경계 clamp, 창 축소·너무 좁은 화면의 중앙 배치를 검사했다. 실제 SDL focus-loss 주입도 통과했다.
- 최종 리뷰에서 boolean pivot이 숫자처럼 나눗셈되는 잘못된 설정 수용을 재현했다. 숫자 타입 검사를 추가하고 회귀 검사에서 설정 파일/클립 오류 문맥과 이미 로딩한 이미지 정리를 확인했다. 전체 116개 통과. 유효 에셋 경로의 동작은 그대로다.
- FR-DOC·SC-DOC: README·docs/README·architecture·art-direction·progress·010 문서를 현재 출력/조작 상태로 갱신한다. game-design/systems는 게임 정책 확정이 없어, tooling/requirements는 환경 변경이 없어 수정하지 않는다.

## Converge와 한계

기능 요구 7개·성공 기준 4개·두 사용자 흐름·계획의 경계/수명/파일 담당·헌법 원칙을 코드와 테스트에 대조했다. 코드의 미구현 차단 항목은 없다. T004 에셋 커밋을 먼저 보존했고 게임 증분에 코드·검사·문서를 함께 담는다. 009의 이전 사용자 직접 확인과 임시 자료 정리 T013/T014/T016은 이번 010 결과로 완료 처리하지 않는다. main/원본 art/원본 main의 미커밋 정책·도구 변경을 보존한다.

최종 게임 이동 속도·미술 품질·사용자 직접 조작은 확정하지 않았다. 좁은 창에서 프레임 전체가 물리적으로 들어가지 않으면 기준점을 중앙에 둔다. 장치 리셋 자동 복구·실물 고DPI/모니터 이동·대량 객체 성능은 범위 밖이다. 게임 PR 생성/병합과 main 병합은 수행하지 않는다.

최종 주 에이전트 검사: 전체 116개 통과, 변경 문서 링크 누락 0개·공백 오류 0개, git diff --no-index --check 오류 출력 없음(변경 존재 종료 1), 원본/복사 PNG 3개 해시 불변. 원본 main 작업 폴더의 변경은 건드리지 않았다.
