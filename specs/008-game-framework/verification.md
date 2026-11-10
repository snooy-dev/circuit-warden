# 검증 상태: 게임프레임워크 — P4 전용 작업트리

**실행 근거**: 2026-11-10 사용자가 P1~P5 새 채팅 구현·별도 워크트리·검증 증분 커밋을 지시했다. 이전 구현 보류는 해제됐으며 PR 생성·게시·병합은 범위 밖이다.

**상태**: P4 준비 검증 / 재개된 P3의 완료와 공유 작업트리 인계 대기. Canvas 구현·전체 기능 완료 보고가 아니다.
**준비 브랜치**: `feature/canvas-ui` (기존 커밋 보존). 실제 구현 브랜치는 `feature/world-rendering`이다.
**기준 커밋**: `1940dd423daf423a84637b9ccec7d23eb92d722f`
**P4 준비 커밋**: `affd3ace2ab46c313b256ef6f79173c8939c9646` — UI 계획·진행 상태·검증/차단 근거만 포함. P4 구현 완료 커밋은 없다.
**준비 작업트리**: `C:/Users/Developer/.codex/worktrees/fc2d/circuit-warden`
**실제 구현 작업트리**: `C:/Users/Developer/.codex/worktrees/cbb2/circuit-warden` — P3 종료·검증 완료 후 P4, 이어 P5가 순차 재사용하며 동시 쓰기를 하지 않는다.

## 선행 상태와 통합 조건

| 계획 | 확인한 상태 | 근거 |
|---|---|---|
| P1 | 별도 브랜치 구현·자동 검증 완료 보고 / 이 작업트리 미통합 | P1 구현 `d3c4ed06f2efa199c41a15f525b161d9e894f7b3`; P3 브랜치의 verification에 기존 16개+core 16개 성공 기록 |
| P2 | 별도 채팅에서 검사 통과 보고 / 검증 커밋 없음 | P3 최종 응답: 자동 승인 검토가 옛 커밋 금지 규칙을 근거로 P2 커밋을 두 번 거부해 사용자 응답 대기 |
| P3 | 재개되어 진행 중 / 최신 완료 커밋 대기 | 채팅 `01a1c41a-a29f-77a0-905b-a7e7ea69059f`, 브랜치 `feature/framework-p3`; `11306be4980f1add78494c990b5c889f3c519b61`은 P1 통합만 포함 |
| P4 | UI 계약·검사 준비만 수행, T014~T017 미완료 | P3 종료 후 공유 작업트리에서 진행 |
| P5 | 이 작업트리에서 미검증 | P1~P4 완료 후 담당 채팅 진행 |

최신 사용자 지시는 독립 P1/P2만 별도 브랜치/워크트리로 병렬 실행하고 P3→P4→P5는 공유 경로·브랜치를 순차 사용하도록 바꿨다. `wait_threads`에서 P3 재개를 확인했고 공유 경로는 읽기 권한 확장 실행으로 브랜치·상태만 확인했다. P3 수정 파일은 건드리지 않았다. P3 종료·검증 커밋·깨끗한 작업트리 확인 후 P4를 진행한다. 현재 준비 커밋 전체 병합은 하지 않고 필요한 내용만 검토한다. 기존 준비 워크트리/브랜치 삭제·아카이브, 다른 채팅 메시지·새 채팅 생성은 하지 않는다.

## 실제 명령과 결과

| 명령 | 결과·한계 |
|---|---|
| `git status --short`, `git branch --show-current` | 시작 시 변경 없는 detached 작업트리 확인 |
| `git show --no-patch --oneline 1940dd423daf423a84637b9ccec7d23eb92d722f` | 엔진·계획 기준 커밋 확인 |
| `git switch -c feature/framework-p4 1940dd423daf423a84637b9ccec7d23eb92d722f` | 최초 Git 관리 경로 쓰기 권한으로 실패, 확장 실행은 승인되어 전용 브랜치 생성 성공 |
| `$env:SPECIFY_FEATURE_DIRECTORY='specs/008-game-framework'; $env:SPECIFY_FEATURE_NO_PERSIST='1'; ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` | 성공. 앞선 SPECIFY_FEATURE만 지정한 호출은 디렉터리 미해결로 실패했고 명시 디렉터리로 해결. 활성 포인터는 쓰지 않음 |
| `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest discover -s tests -v` | 기존 엔진·데모 16개 통과. P4 검증은 아님 |
| `git log -3 --oneline feature/framework-p3`, `git show feature/framework-p3:specs/008-game-framework/verification.md` | 선행 브랜치가 P1 통합까지임을 직접 확인 |
| `git diff --check` | 통과 |
| 게임 Python 표준입력 pathlib/re 문서 검사 | 변경 Markdown 3개의 로컬 링크·줄 끝 공백, T014~T017 미체크와 런타임 파일 부재 확인 통과 |

## analyze·문서 영향·미실행

공통 spec/plan/tasks와 P4 계획, architecture, data-model/contracts/research/quickstart를 읽었다. requirements 체크리스트 11개는 모두 체크되어 있으며 수정하지 않았다. 확장 hooks 설정 파일은 없었다. T014~T017이 FR-004/006~010의 UI 수명·형제 정렬·좌표·알파에 대응하고 P5 공동 스냅샷과 별개임을 확인했다.

P4 계획에서 브랜치·최신 구현 허가·기술 기본값을 정리했다. Canvas는 명시적 reference_size를 받고 기준 크기를 최종 게임 해상도로 고정하지 않는다. 루트 anchor와 균등 배율은 기존 계약을 따르며 자동 레이아웃·입력 분배·reparent는 추가하지 않는다. progress에 정확한 선행 차단·재개 조건을 기록했다. 런타임 계약을 구현하지 않았으므로 architecture/data-model/contracts를 구현 완료로 바꾸지 않았다. 게임 설계·아트·systems는 영향 없다.

Canvas 자동 테스트·실제 UI 창·부모 이동/숨김/삭제·화면비/반투명 검사는 P3 인계 전이라 전부 미실행이다. P4 implement와 완료 converge는 수행하지 않았으며 T014~T017 체크박스를 남겼다. 미완료 P4를 정당화하도록 요구사항을 낮추지 않았다. 게임 코드·의존성·에셋·원본 작업 폴더는 변경하지 않았다.
