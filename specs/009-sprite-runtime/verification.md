# Verification: 009 스프라이트 실행 기능

**상태**: P1/P2 이미지·표시·재생 구현·자동 검증 완료. 실 시트 출력 검사 통과, 사용자 직접 확인 대기.
**진행 근거**: 2026-11-11 사용자 계획 구현·중간 커밋 지시. 임시 검사는 미추적, 사용자 직접 확인 전 제거 금지.
**브랜치**: feature/engine, d7d68308 기반. 아래 기존 P1/P2 증거는 출처 브랜치 feature/sprite-runtime의 기록이며 최신 통합 검사는 마지막 절을 따른다.

## 실제 검사

| 명령·검사 | 결과 |
|---|---|
| setup-tasks.ps1 -Json / check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks | 성공, 009 문서·작업 목록 확인 |
| analyze: spec/plan/tasks/헌법 대응 | FR 11개 전체 작업 연결, 사용자 조건·수명·순서 모순 없음. 구현 차단 항목 없음 |
| 명세 품질 체크리스트 | 미완료 항목 0개 |
| 게임 Python -B <임시 폴더>/preview.py --project <현재 작업트리> --smoke | 종료 0, 실제 PNG 로딩/공유·월드/UI·pause/step/switch/flip/단발/resize/reenter/cleanup·원본 해시 8단계 PASS |
| 실제 SDL 출력 smoke-0/4/6.png 열기 | idle·Run의 자르기·투명 배경·기준점·확대·반투명과 1100×720/900×600 화면 배치 관찰 |
| 독립 리뷰 수정 재확인 | 앞서 재현한 3개 입력 모두 수정됨을 검토자가 재실행 확인 |
| pathlib/re 문서 검사·SHA256·git diff --check·추적 파일 검사 | 로컬 링크 19개 통과, 남은 작업 T013/T014/T016만 존재. 원본 4개 해시 불변, 임시 자료 저장소 밖, main/engine/의존성 차이 없음 |
| 게임 Python -B -m unittest discover -s tests -p test_sprites.py -v (구현 전) | 예상 실패: sprites 모듈 없음 |
| 같은 신규 검사 (구현 후) | 제한 환경의 Temp 접근 실패 후 확장 실행 5개 통과 |
| D:/GitHub/circuit-warden/.venv/Scripts/python.exe -B -m unittest discover -s tests -v | **100개 통과**. 기존 85개 + 신규 15개 |

P1은 94개 통과 후 ffc4a13으로 커밋했다. P2 검사 4개는 구현 전 ImportError를 확인했다. 독립 리뷰(gpt-6.1-sol/medium)의 큰 dt 위상 소실·짧은 프레임 건너뜀·닫힌 캐시 반환 3건을 수정하고 회귀 검사를 추가했다. 전체 100개 통과 후 검사 배치 정리에 해당하는 스프라이트 검사 11개도 통과했다. 확장 hooks 파일은 없어 전후 hook 없음.

## 요구사항별 증거

- FR-001/002: source 영역 검증, pivot 월드/UI bounds, 반전 기준점, 실제 SDL 소프트웨어 렌더러의 식별 색상 픽셀로 행 선택·수평 반전·비영점 viewport 검사. clip Python 예외 후 alpha/blend 복원, 무효 출력 생략 확인.
- FR-005/006: 실제 경로 별칭의 1회 로딩, 누락 파일 경로 오류, 실패 캐시 없음, renderer 없음/다른 세션 사용 거부.
- FR-007/010: 정리 실패에도 객체→UI→이미지 순서, 부분 로딩 실패 정리, 반복 exit/close, 닫힌 참조 거부. 실제 Pico2D Image에서 traceback 보유·detach·None 소멸자 호출이 유효 texture를 재해제하지 않음을 확인. 기존 전체 이미지/장면/엔진 호출 검사 통과.
- FR-003/004: 가변 시간·분할 갱신·반복/단발·독립 개체·같은/다른 clip 전환과 재시작, 큰 유한 dt·짧은 프레임 회귀 검사 통과.
- FR-008: 실 idle/Run 원본을 읽기 전용으로 사용하고 SHA256 불변 확인. assets/기본 실행/커밋에 포함하지 않았다. FR-009: 미추적 임시 하네스와 설정·출력 PNG를 유지하며 사용자 확인/그 이후 정리는 미완료.
- FR-DOC: architecture/progress/README와 명세·계획·계약·데이터 모델을 P1/P2 완료·사용자 확인 미완료로 맞췄다.

## 실제 출력·보존 상태

임시 폴더는 C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c602-4806-7d43-aaed-3468b12931a0/sprite-preview다. [실행법과 키](quickstart.md)를 따른다. preview.py/sources.json/launch.ps1/created-files.txt와 출력 PNG는 모두 저장소 밖 미추적이다. 원본은 D:/GitHub/circuit-warden/art/warden/provisional-approved의 idle-unarmed-v7/unarmed와 run-v4/run_right이며 수정·복사하지 않았다. SHA256은 임시 sources.json에 기록하고 smoke 종료 시 원본 4개 파일의 일치를 확인했다.

별도 실행의 첫 Start-Process는 호출 종료 후 지속 여부를 확보하지 못해 사용자 실행 유지 근거로 쓰지 않았다. 이후 장기 실행 세션 28413으로 preview를 열었고 열린 창 목록에서 ‘스프라이트 임시 확인 — 실 시트 미반영’을 확인했다. Python 창의 컴퓨터 사용 캡처는 접근 허용이 없어 수행하지 못했고, 프로그램이 실제 SDL 렌더러에서 저장한 출력 PNG를 관찰한 결과와 구분한다. 현재 창을 닫아도 launch.ps1로 다시 실행할 수 있다.

자동 입력은 SDL 이벤트 주입이다. 물리 키 조작과 사용자 직접 확인은 미실행이다. 임시 자료를 제거하지 않았다. 소프트웨어 SDL 검사에서는 native source 픽셀과 알파 상태·traceback 잔존/None 소멸자를 확인했고, 실제 창에서는 두 PNG 시트의 출력·재생·크기 변경·재진입을 관찰했다.

## Converge 대조와 남은 작업

spec/plan/tasks와 sprites.py, game_framework.py, 관련 테스트 및 실제 출력 증거를 대조했다. FR 11개, SC 5개, 계획 결정 10개, 헌법 원칙 5개를 기준으로 추가로 구현할 코드 누락은 발견하지 못했다. FR-009/SC-004 및 전체 완료 조건은 사용자 확인과 임시 정리 때문에 **부분 충족**이다. 이미 T013(사용자 결과)·T014(확인 후 정리)·T016(최종 문서/커밋)에 남아 있으므로 중복 작업을 추가하지 않았다. T015는 이 현재 대응 점검을 완료했다는 의미이며 기능 전체 Converged 판정은 아니다.

사용자 확인 전 대기를 유지한다. 결과를 받은 후 T013/T014를 수행하고 최종 converge·문서·커밋으로 마무리한다. 원본 art·영구 assets·기본 main·의존성은 변경하지 않았다. clip 내부 SDL 실패 반환은 Pico2D 한계로 관측할 수 없다. 장치 리셋 자동 복구·실물 DPI·대규모 성능은 범위 밖이다.

game-design/systems/workflow/tooling은 정책·환경 변화가 없어 수정하지 않았다. architecture의 예전 리소스 관리자 제외 문장은 장면 간 공유 관리자를 제외하는 것으로 현재 구현과 맞췄다. game_framework.py의 기존 리셋 shortcut 주석도 현재 범위에 맞게 정리했으며 실행 동작 변화는 없어 자동 검사를 반복하지 않았다.

## Engine Package Integration (2026-11-11)

- 진행 근거: 게임 전에 엔진 보완 → engine/main PR → feature/character-movement 작업을 진행하라는 사용자 지시와 중단 후 계속 지시. main 병합은 수행하지 않는다.
- FR-011: 게임 API는 game_framework/sprites.py·drawing.py·level_scene.py, native 출력은 engine/rendering/drawing.py에 배치했다. engine → game_framework 역의존성은 없다. 루트 sprites.py는 기존 임시 실행기 호환이며 전체 이미지 호출을 보존한다.
- SC-005 자동 검사: 통합 사본에서 게임 Python `-B -m unittest discover -s tests -v`로 전체 회귀 검사를 수행한다. **106개 통과**. 처음 검사에서 sandbox 기본 Temp 접근 제한으로 이미지 테스트 6개가 실패했으나, 실제로 임시 파일이 필요 없는 모의 로더 테스트를 기존 읽기 전용 파일로 변경해 환경 재지정 없이 동일 명령이 통과했다.
- 실제 검사 명령: 게임 Python `-B .local-tools/work/engine-sprite-integration/preview/preview.py --project .local-tools/work/engine-sprite-integration/engine --smoke` (실행에서는 두 경로를 절대 경로로 전달).
- 결과: 종료 0. 실제 PNG 로딩/캐시·월드/UI·일시정지/한 프레임/클립 전환·반전·단발·1100×720↔900×600 크기 변경·재진입·모든 이미지 닫기·원본 해시 불변 8단계 PASS. smoke-4/6.png에서 클리핑·반전·투명 배경·기준점·기본/확대 표시를 관찰했다. SDL 이벤트 주입과 렌더러 PNG 관찰이며 실제 물리 키 입력·사용자 확인으로 기록하지 않는다.
- docs: architecture·progress·README·docs/README 및 009 계획·실행 안내를 패키지 구조에 맞췄다. main 최신 커밋의 art-direction을 그대로 보존해 공격 v5 잠정 승인 상태를 되돌리지 않는다. game-design/systems/requirements는 정책·의존성 변화가 없어 변경하지 않는다.
- 범위 대조: FR-001~011/FR-DOC와 현재 코드·검사·문서를 확인했다. 기존 사용자 확인·임시 정리 T013/T014/T016은 남으며 Draft PR에 그대로 명시한다. 새 게임 에셋·이동은 이 엔진 변경에 포함하지 않는다. 예전 임시 폴더는 수정·삭제하지 않았다.
