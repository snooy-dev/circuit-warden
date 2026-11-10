# 검증 상태: 게임프레임워크

**현재 실행 근거**: 2026-11-10 사용자가 P1~P5의 새 채팅 구현과 독립 계획의 별도 워크트리 병렬 작업을 지시했다. 이전 구현 보류는 해제됐다. 상세 기술 선택과 사용자 게임 정책 확정은 구분한다.

**상태**: P1 구현·자동 검증 완료. 전체 프레임워크 완료 아님.
**P1 브랜치**: `feature/framework-p1`
**기준 커밋**: `1940dd423daf423a84637b9ccec7d23eb92d722f`
**P1 구현 커밋**: 이 문서와 코드·검사를 포함하는 커밋. 정확한 SHA는 후속 인계 갱신에서 기록한다.

## 계획별 상태

| 계획 | 이 작업트리의 상태 | 실제 근거 / 다음 단계 |
|---|---|---|
| P1 객체·규칙 | 구현·자동 검증 완료 | 새 core 검사 16개 + 기존 16개 통과. FR-001~004의 월드 소유·규칙·전달 수명 담당 범위 충족 |
| P2 창·출력 | 별도 워크트리 담당 / 여기서 미검증 | P1과 독립. 기존 001 검사는 가변 출력 성공 근거가 아님 |
| P3 월드 렌더링 | 선행 검증 커밋 대기 | P1/P2 통합 후 구현 |
| P4 Canvas UI | 선행 결과 대기 | P3 후 구현 |
| P5 통합 | 선행 결과 대기 | P1~P4 후 SC-001/002/DOC 전체 판정 |

## 실제 명령과 결과

전용 작업트리 `C:/Users/Developer/.codex/worktrees/0ff6/circuit-warden`에서 실행했다.

| 명령 | 결과 |
|---|---|
| `git status --short`, `git cat-file -t 1940dd423daf423a84637b9ccec7d23eb92d722f` | 시작 시 깨끗한 작업트리·기준 commit 확인 |
| `git switch -c feature/framework-p1 1940dd423daf423a84637b9ccec7d23eb92d722f` | 전용 브랜치 생성. 최초 제한된 Git 관리 경로 쓰기는 거부됐고 승인된 확장 실행으로 성공 |
| `$env:SPECIFY_FEATURE_DIRECTORY=(Resolve-Path specs/008-game-framework).Path; ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` | 성공. 최초 SPECIFY_FEATURE만 지정한 시도는 디렉터리 미해결로 실패했고 명시 디렉터리로 해결 |
| `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest discover -s tests -v` | 32개 통과: P1 16개, 기존 엔진·데모 16개 |
| `git diff --check` | 통과 |
| 게임 Python 표준입력 pathlib/re 검사: 변경 Markdown의 로컬 링크 대상·줄 끝 공백 | 11개 문서 통과 |

## 요구사항·검사 대응과 인계 API

- FR-001/002: Level별 GameMode 격리, 초기 배치→모드 시작, 등록순 dict·ID 조회·증가 ID, 단일 소유·재등록 금지, 동일성 기반 제거와 반복 제거, 재열기 시 새 배치.
- FR-003: 이벤트/update 시작 스냅샷, 모드→등록순 객체, 모드/객체의 생성·자기/다른 객체 제거, 다음 전달 참여, 교차 재진입 거부, 오류 후 가드 복구.
- FR-004 담당 범위: 실패한 spawn 소유 해제·한 번 정리, 실패 객체 재사용 거부, 초기 배치/모드 시작 실패의 전체 정리, 복수 오류 보존, 닫는 중 등록/재열기 거부, 닫기 중 일부 오류에도 전체 정리 시도, 전달 종료/실패 후 제거 객체 참조 해제.
- `Level(mode=None)`, `Level.on_open()`, `open()/close()`, `spawn(obj)`, `get(id)`, 읽기 전용 `objects/mode`를 제공한다. `objects`는 등록순 tuple이며 순회 자체의 소유 변경은 하지 않는다.
- `GameObject.level/id`, `on_spawn/on_destroy/handle_event/update`, `destroy()`와 `GameMode.level`, `on_start/on_event/on_update/on_end`를 제공한다. 위치·게임 상태는 구체 객체가 가진다.
- 모드는 Level 생성 때 연결되며 다른 Level에서 공유·재사용하지 않는다. 닫힌 Level의 입력/update는 무시한다. `on_open` 뒤 `on_start`, 열기 실패에도 `on_end`를 시도한다. 단일 오류는 그대로, 복수 오류는 BaseExceptionGroup으로 전달한다.
- P5 공동 스냅샷 API는 아직 없다. 현재 `Level.update()`가 내부 스냅샷을 취득한다. P5가 Canvas 결합 시 담당 계약을 확장한다.

## 문서 갱신·analyze·converge

P1 계획·T003~T005·spec/plan/data-model/contracts/quickstart와 docs/architecture·progress·README를 실제 API·검증 상태에 맞췄다. 공통 문서의 이전 구현 보류 문장을 최신 지시로 정리하되 다른 계획의 구현 완료를 주장하지 않았다. architecture는 목표 설계와 P1 구현을 구분하며 이전 링크 앵커를 보존했다.

analyze에서 P1은 렌더/Canvas/SDL 없이 FR-001~004의 담당 범위를 구현할 수 있음을 확인했다. 구체 승패·업데이트 후 판정은 제외다. 테스트 초안은 예전 GameMode 소유 모델이므로 복사하지 않고 현재 Level 계약으로 새 검사를 작성했다. 독립 읽기 전용 Luna/high 검토에서 재현 가능한 P1 결함은 없었으며 core 16개를 별도로 통과했다. 지적된 모드 시작 중 닫기 검사 공백을 보완하고 전체 32개를 다시 통과했다. converge에서 P1 요구사항·실제 API·검사·문서 대응과 제외 범위를 대조했고 P1 필수 미완료는 없다. 기존 engine.py/main.py/requirements.txt와 원본 작업 폴더는 변경하지 않았다. systems·game-design·art-direction은 게임 규칙·아트를 변경하지 않아 영향 없다. 외부 서비스·생성·새 의존성·PR 없음.

## 미실행·한계

P1은 창 없는 core 계획이므로 새 실제 창·UI 자동 조작·사용자 직접 확인은 수행하지 않았다. P2~P5의 실제 출력·렌더·Canvas·복합 장면 검증을 대체하지 않는다. 실제 게임 규모·성능 예산은 미정이며 새 성능 주장을 하지 않는다. 오류 traceback이나 외부 변수가 잡고 있는 참조의 즉시 메모리 해제는 보장하지 않는다.

## 다음 단계

P3 담당은 P1 구현 커밋과 별도 P2 검증 커밋을 통합한 뒤 월드 렌더링을 진행한다. 이 문서의 P2~P5 상태는 이 작업트리에서 확인한 범위이며 다른 워크트리의 최신 결과는 해당 검증 커밋에서 가져온다.
