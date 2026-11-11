# Verification: 캐릭터 표시와 좌우 이동

상태: 명세·계획·분석 완료, 구현 진행 중. 엔진 PR #2와 feature/character-movement 분기 완료.

## Analyze

FR-001/006→T003/004, FR-002~005→T005~007, FR-DOC/SC-DOC→T002/008/009. 7개 요구 모두 작업과 연결되며 명세·계획·작업 간 차단 충돌은 없다. 임시 수치와 게임 규칙 미정을 구분했다. 확장 hooks 파일 없음. 미확인: 실제 게임 조작·화면·사용자 직접 확인.

## P1 에셋 배치

표준 pathlib/struct/hashlib/json으로 원본과 복사 PNG 3개의 SHA-256 일치, PNG IHDR 크기·셀 개수·프레임 시간·기준점을 확인했다. idle 1024×624=48셀·2000ms, Run 좌/우 각 1024×208=16셀·480ms이며 셀은 모두 128×104다. 게임 이름에 버전이 없고 출처·해시를 assets/warden/README.md에 보존했다. 메타데이터의 제작용 previewSpeed·이벤트는 가져오지 않았다. .gitattributes는 PNG binary이며 LFS/의존성 추가 없음.

architecture·art-direction·progress·docs/README에 검사 범위/게임 복사본과 구현 중 상태를 반영했다. 실제 게임 코드 검증은 다음 증분이며 P1을 게임 동작 완료로 표시하지 않는다.
