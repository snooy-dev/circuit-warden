# Implementation Plan: [FEATURE]

**Date**: [DATE] | **Spec**: [link] | **Status**: Draft / Ready / Approved

## Summary

[확정 의도를 구현하는 최소 접근. 규칙은 spec/docs를 참조.]

## Technical Context

- **Language/Dependencies**: Python + Pico2D; 현재 requirements.txt 확인.
- **Runtime**: 게임 .venv/, 도구 .local-tools/python/.
- **Platform/Performance**: [확정 목표 또는 미정. 임의 수치 확정 금지.]
- **Testing**: [Python 자동 테스트와 실제 Pico2D 검사의 범위·명령.]

## Constitution Check

- [ ] 사용자 결정·기술적 가정·요청 범위·명시적 보류를 구분했으며 PR 외 별도 승인 대기를 두지 않았다.
- [ ] 기준 docs를 읽었고 모순·미정을 해결했다.
- [ ] 문서 영향·갱신·실행 검증을 계획했다.
- [ ] 웹 서버/DB/다른 엔진 등 불필요한 구조를 도입하지 않는다.

## Decisions & Alternatives

[필요한 기술 선택·이유·기각 대안. 현재 유효한 결정은 docs/architecture.md에 반영. 과거 결정 연표는 추가하지 않는다.]

## Project Structure & Interfaces

[이번 변경이 실제로 건드릴 파일·호출부·데이터·테스트·에셋. 기존 구조 먼저 확인.]

## Documentation Impact (mandatory)

최소 실행 가능한 틀 → 기본 동작 → 확장별 결과·검증·문서 갱신·커밋 지점을 계획한다. `feature/<기능명>` 브랜치와 동시 작업의 워크트리·파일 담당, 필요한 서브에이전트 모델/추론 수준·이유를 명시한다.

| 요구사항/결정 | 기준 docs | 바뀌는 내용 | 갱신 시점 | 검증 방법 |
|---|---|---|---|---|
| [FR/SC/결정] | [경로·항목] | [변경 또는 영향 없음의 이유] | [설계/구현 후] | [증거] |

docs/progress.md에 현재 목표·활성 작업·미결 사항을 갱신한다. verification.md에는 실제 검증 결과와 문서 대응 검토를 남긴다.

## Verification & Risks

[자동 테스트·Pico2D 실행·에셋 검사·사람의 플레이 판단을 구분. 미실행을 통과로 쓰지 않는다.]
