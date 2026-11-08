# 문서 기반 개발 흐름

## 현재 범위

기본 실행 기반의 명세·계획은 사용자 승인을 받았으며 구현·검증을 완료했다. 이미 수행한 단계를 전체 workflow로 중복 실행하지 않는다. 현재 상태는 [진행 상태](progress.md)를 따른다.

## 진행 순서

1. 기획 대화의 결정·미정을 즉시 docs에 기록한다. PPTX는 원본 근거로 남긴다.
2. `$speckit-specify`와 필요한 `$speckit-clarify`로 기준 docs·승인 상태·문서 영향을 포함한 명세를 작성한다.
3. `$speckit-plan`으로 기술 선택·문서 갱신·검증을 계획한다.
   - 명세·계획의 링크와 핵심 제안을 사용자에게 먼저 제시하고 검토·진행 확인을 받는다. 포함 범위 선택만으로 상세 명세·계획을 승인 처리하지 않는다.
4. `$speckit-tasks`로 실제 작업을 만든다. docs 갱신·verification 작성·진행 기록은 필수다.
5. `$speckit-analyze`로 모순·누락을 점검하고 중요한 미정을 해결한다.
6. 명세·계획 검토를 마치고 구현 진행을 확인한 범위만 `$speckit-implement`로 수행한다. 이후 승인된 범위의 통상 수정·테스트는 매번 재승인을 요구하지 않는다.
7. docs를 실제 결과에 맞춰 갱신하고 기능별 verification.md를 작성한다.
8. `$speckit-converge`가 남긴 작업이 있으면 같은 흐름에서 구현·검증·문서 갱신을 반복한다.

Codex가 순서를 안내한다. 직접 스킬을 호출해도 AGENTS·constitution·프로젝트 템플릿 규칙이 적용된다.

## 기록과 완료

- docs는 현재 승인 설계와 구현 상태, specs는 진행 중인 변경의 작업 문서다. 변경 경위는 Git 로그·diff로 확인하며 별도 연표를 누적하지 않는다.
- verification에는 요구사항별 실제 명령·결과·미실행/실패·문서 갱신·남은 문제를 기록한다.
- 문서 영향이 없으면 이유를 적는다. 날짜 변경만으로 갱신을 대신하지 않는다.
- 자동 테스트·Pico2D 실제 창/입력·사람의 플레이 판단은 서로 대체되지 않는다.
- progress와 verification은 현재 상태·최신 유효 결과로 갱신한다. 폐기된 규칙과 해결된 질문을 지운다. 현재 선택 이유와 미해결 위험은 남긴다.
- 완료 specs는 docs 반영·검증 결과의 커밋 보존·참조 없음이 확인되면 후속 정리 변경에서 제거할 수 있다. 미커밋 근거를 먼저 삭제하지 않는다. 커밋은 요청받았을 때 수행한다.

## 설정 위치

- .specify/memory/constitution.md: 공통 원칙.
- .specify/templates/overrides/: spec/plan/tasks/checklist 템플릿. 기본 파일은 직접 수정하지 않는다.
- .specify/workflows/overlays/speckit/circuit-warden-docs.yml: 공식 speckit 흐름에 docs 작성·갱신, analyze, converge를 포함.
- AGENTS.md: 읽기 순서·구현 보류·역할·도구 경로.

CLI 단계 실행 완료가 게임 완성 보증은 아니다. converge가 남긴 작업·미실행 테스트·문서 불일치가 있으면 완료가 아니다. 스킬과 CLI 흐름을 동시에 중복 실행하지 않는다.
