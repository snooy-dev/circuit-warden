# Circuit Warden 작업 규칙

## 시작과 권한

1. `docs/README.md`, `docs/progress.md`, `.specify/memory/constitution.md`를 읽는다.
2. 해당 작업의 현재 docs와 활성 `specs/<feature>/`만 추가로 읽는다.
3. 현재는 도구·문서 체계 구성 단계다. 사용자가 구현 시작을 명시적으로 지시하기 전에는 게임 코드, 원형, 실행 진입점, 게임 에셋을 만들지 않는다. 이후 명시적 지시를 받으면 `docs/progress.md`에 범위와 근거를 기록한다.
4. 사용자는 기획·게임 설계·범위를 결정한다. Codex는 질문, 문서화, 기술 제안, 작업 분할, 구현, 테스트·디버깅을 담당한다.

## 단일 워크플로우

- Spec Kit만 개발 진행 체계로 사용한다. BMad, OpenSpec, GSD, Superpowers의 별도 계획·실행 흐름을 섞지 않는다.
- 문서는 한국어로 작성한다. Spec Kit이 인식하는 제목·요구사항 ID·작업 체크박스는 템플릿 형식을 유지한다.
- `specify → clarify(필요 시) → plan → tasks → analyze → implement → docs 갱신 → converge`를 따른다.
- 설계에 영향을 주는 미정 사항은 구현 전에 해결한다. 이미 승인된 범위의 통상적인 코드 수정과 테스트마다 재승인을 요구하지 않는다.
- 구현 보류 상태에서 implement나 전체 workflow run을 실행하지 않는다.
- 새 Git 브랜치가 필요하면 `codex/` 접두사를 사용한다. 기능 폴더를 만들기 위해 브랜치를 임의로 바꿀 필요는 없다. 사용자 변경을 보존하고 자동 커밋하지 않는다.

## 문서와 완료 조건

- `docs/`는 현재 유효한 기준, `specs/`는 진행 중인 변경의 명세·계획·작업·최신 검증 결과다. 과거 변경 경위는 Git 로그·diff로 확인한다.
- game-design은 의도와 범위, systems는 시스템별 규칙을 소유한다. 같은 수치는 한 문서에서만 정의하고 나머지는 참조한다.
- PPTX는 제안 자료다. 제안·가정·미정·확정·대체·폐기를 구분하고 추론을 승인된 요구로 승격하지 않는다.
- 확정 설계와 구현 상태도 구분한다. 승인됐지만 미구현인 규칙을 구현 완료라고 표시하지 않는다.
- 결정 직후 해당 docs의 현재 내용을 수정하고 유효한 선택 이유만 짧게 남긴다. 별도 결정 연표·변경일지·세션 로그를 누적하지 않는다. 계획에는 문서 영향을, tasks에는 docs 갱신·검증 작업을 반드시 넣는다.
- 완료 전 docs·명세·코드·테스트의 대응을 확인한다. 기능별 `verification.md`에 실제 명령·결과·미실행·문서 갱신 또는 영향 없음의 이유를 남긴다.
- 실패·미실행·필수 미완료 작업이 남으면 완료로 보고하지 않는다. 버그에 맞춰 명세를 바꿔 정당화하지 않는다.
- 새 대화를 위한 목표·활성 작업·미결 사항은 progress에 갱신한다. 작업 목록 전체를 중복 복사하지 않는다.
- docs와 verification은 이전 내용을 갱신하며 실행 로그를 계속 덧붙이지 않는다. 폐기된 규칙·해결된 질문은 제거하고 현재 설계의 이유와 남은 문제를 보존한다.
- 완료한 specs는 현재 기준을 docs에 반영하고 검증 결과가 Git 커밋에 보존된 것을 확인한 뒤, 다른 문서에서 참조하지 않으면 후속 정리 변경에서 제거할 수 있다. 미커밋 근거를 먼저 삭제하지 않는다. 자동 커밋하지 않는다.
- 커밋을 요청받으면 관련 코드·docs·명세 변경을 함께 묶고 메시지에 변경 이유·검증을 적는다. 새 대화에서 과거 맥락이 필요하면 `git log -- <path>`와 `git show <commit>:<path>`를 조회한다.

## 기술·도구 경계

- 게임은 Python + Pico2D. 게임 환경은 `.venv/`, 의존성은 `requirements.txt`다. 다른 엔진으로 바꾸지 않는다.
- 도구 환경은 `.local-tools/python/`. PowerShell에서 `. ./scripts/use-project-tools.ps1`로 현재 세션을 준비한다. 게임 실행·테스트에는 `.venv/Scripts/python.exe`를 명시한다.
- 스킬은 `.agents/skills/`, 원본·실행 도구는 `.local-tools/`. 두 경로는 `.git/info/exclude`로만 제외한다. docs·specs·정책·템플릿은 숨기지 않는다.
- Agent Sprite Forge는 generate2dsprite, generate2dmap, generate2dmedia, video2dsprite, codeart2d의 묶음이다. 필요한 스킬만 호출하고 codeart2d는 명시적으로 선택한 경우에만 쓴다.
- pixelfx는 `.local-tools/pixelfx/`에서 실행한다. 또 다른 checkout을 만들지 않는다. 준비 스크립트가 PIXELFX_DIR을 설정한다.
- 설치는 생성 요청이 아니다. 현재는 외부 생성 호출·비용 지출·게임 에셋 제작을 하지 않는다. 이후 아트 작업은 승인된 기능과 아트 가이드에 연결한다.
- 계정·키를 docs나 Git에 기록하지 않는다. 도구 설정으로 게임 의존성이나 전역 환경을 바꾸지 않는다.
