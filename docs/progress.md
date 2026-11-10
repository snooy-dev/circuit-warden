# 진행 상태

갱신일: 2026-11-11

## 현재 단계

- **엔진/게임 API 책임 경계 정리 완료**: 2026-11-11 사용자 승인 범위로 game_framework 공개 조작 API와 engine 내부 실행을 분리했다. 기존 기능·공개 import·실행 명령을 유지하고 demos 및 tests/unit·integration·smoke를 분류했다.
- 작업 폴더: C:/Users/Developer/.codex/worktrees/game-framework/circuit-warden, feature/game-framework. 다른 작업트리·미커밋 변경은 건드리지 않았다.
- 전체 자동 90개 통과. 지연 수집·수명 가드·실패 정리·정렬 및 engine→game_framework 의존 금지를 확인했다. 실제 SDL 통합 smoke와 초기/크기 변경 PNG 관찰 결과는 [검증](../specs/008-game-framework/verification.md)을 따른다. 실물 DPI·물리 키·사용자 직접 확인은 이번에 수행하지 않았다.
- 현재 구조는 [기술 구조](architecture.md#코드-폴더-구조), 요구사항 FR-012/013·SC-004와 Phase 8은 008에 반영했다. 게임 정책·아트 통합·PR은 이번 범위 밖이다.

## 확정 사항

- Python + Pico2D, Spec Kit 단일 흐름과 docs 갱신 필수.
- 개발 요청 범위 안에서 명세·계획을 제시하고 별도 승인 대기 없이 구현한다. 최소 실행 가능한 틀부터 확장하며 검증·문서 갱신·커밋을 증분마다 반복한다. PR 생성·게시·병합은 승인 대상으로 둔다.
- 기능별 `feature/<기능명>` 브랜치를 사용하며 동시 작업에는 워크트리를 권장한다. 서브에이전트는 난도·지시 구체성에 따라 모델과 추론 수준을 선택한다. 상세 기준은 [워크플로우](workflow.md)를 따른다.
- 게임 .venv와 도구 .local-tools/python 환경 분리. 로컬 스킬·도구는 .git/info/exclude로 제외한다.
- 기술 계약과 검증 기본값은 [architecture](architecture.md)가 소유한다.

## 미결 사항

- 이번 기본 실행 기반의 필수 미완료 작업은 없다.
- 게임 의도·규칙·제작 범위, 아트 스타일·규격은 별도 미정이다.
- 자동 UI 도구의 키 입력은 반응을 확인하지 못했다. 실제 사용자 키 조작은 정상이며 도구 자체의 원인은 조사하지 않았다.

## 다음 작업

이번 구조 정리의 필수 잔여 작업은 없다. 후속 개발은 feature/game-framework의 현재 패키지를 기준으로 진행한다. 실행 방법은 [quickstart](../specs/008-game-framework/quickstart.md)를 따른다. 게임 규칙·아트·성능 예산은 미정이며 PR 생성·게시·병합은 별도 승인 대상이다.

## 개발 방식 조정

2026-11-10 사용자가 기능별 feature 브랜치, 동시 작업의 워크트리 권장, 작은 단위의 지속 개발·커밋, PR 외 승인 절차 제거, OpenAI 권장에 따른 서브에이전트 모델/추론 수준 선택을 요청했다. 이 지시가 이전의 별도 구현 승인·요청 시에만 커밋 규칙을 대체한다. AGENTS·constitution 2.0.0·workflow·프로젝트 템플릿과 overlay에 반영했다. 이번 정책 작업 브랜치는 `feature/incremental-workflow`이며 기존 미커밋 작업을 보존한다. 최신 검증과 한계는 [개발 방식 검증](workflow-verification.md)을 참조한다.
