# Verification: 점진적 개발과 모델 선택 정책

기준일: 2026-11-10. 범위: 사용자 요청에 따른 개발 방식·Git·서브에이전트 운영 정책 변경. 새 게임 기능·아트 제작·통합을 수행한 작업이 아니다.

## 요구사항과 반영

| 요구사항 | 반영 위치·결과 |
|---|---|
| 독립 기능 개발만 feature 브랜치 사용·소규모 작업은 현재 브랜치 사용 | AGENTS·workflow·constitution 2.1.0·plan/checklist 템플릿·overlay에 일치시킴. 기존 브랜치는 유지 |
| 기본 틀부터 확장하며 작은 단위로 검증·커밋 | workflow·plan/tasks 템플릿·overlay. 관련 코드·문서·검증을 증분마다 함께 관리 |
| PR 외 승인 요청 없이 계속 개발 | AGENTS·constitution·workflow·spec/plan/tasks/checklist 템플릿·overlay. 요청 범위와 실제 사용자 승인을 구분하며 Ready 사용 가능 |
| 난도·지시 구체성에 따른 모델과 추론 수준 선택 | workflow의 작업별 시작값·상향 기준·현재 호출 제약. AGENTS에서 참조 |
| 기존 변경 보존 | 기존 미커밋 문서·스크립트·아트 specs를 유지. 작업 중 progress의 아트 상태 갱신을 감지해 다시 읽고 정책 문단만 수정 |

constitution은 기존 승인·커밋 원칙의 비호환 변경으로 1.0.0에서 2.0.0으로 올렸다. 서브에이전트의 읽기 전용 정책 검토에는 `gpt-6-luna` / `medium` / `fork_turns="none"`을 사용했고 결과를 수신했다. 관련 파일·충돌 지점이 명확한 문서 점검이므로 이 설정을 선택했다. 별도의 모델 간 성능 비교 실험은 하지 않았다.

## 공식 자료와 적용 범위

- [OpenAI Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): 모델·추론 수준 선택, 독립 읽기 작업의 위임과 병렬 쓰기 충돌에 대한 안내를 확인했다.
- [OpenAI Model selection](https://developers.openai.com/api/docs/guides/model-selection): 품질·시간·비용을 함께 고려하고 수용 기준으로 결과를 확인하는 원칙을 적용했다.

프로젝트 모델표는 이 원칙과 현재 도구 계약에 따른 시작값이며 OpenAI의 고정 배정표가 아니다. 전역 Codex 설정은 변경하지 않았다.

## 실제 검사

- `.specify/scripts/powershell/resolve-template.ps1 constitution-template -Json`: 성공. 기존 원칙과 제목 구조를 유지해 개정했다. `.specify/extensions.yml`은 없어 실행할 hook이 없었다.
- `git switch -c feature/incremental-workflow`: 최초 파일 권한 제한 이후 권한 검토를 거친 재시도 성공. 기존 변경을 유지했다.
- `git diff --check`: 종료 코드 0. LF→CRLF 안내만 있으며 공백 오류 없음.
- PowerShell `[IO.File]::ReadAllText`·`[regex]::Matches`·`Test-Path -LiteralPath`: 변경 문서/템플릿/overlay 11개, 상대 링크 대상 31개 확인. 충돌 마커·대체 문자·줄 끝 공백 없음.
- `resolve-template.ps1 <name> -Json`: spec·plan·tasks·checklist 4개 프로젝트 템플릿 해석 성공.
- `.local-tools/python/Scripts/python.exe -c "...yaml.safe_load..."`: overlay YAML 파싱, `extends == speckit`, 단계 6개 및 고유 ID 6개 확인 성공. 처음에는 도구 Python 경로를 잘못 지정해 실행하지 못했으며 실제 `Scripts/python.exe` 위치를 확인해 재실행했다. 게임 환경에는 PyYAML이 없어 설치하지 않고 기존 도구 환경을 사용했다.
- `rg -n '승인을 받|확인을 받|자동 커밋하지|커밋은 요청|구현 시작 지시 전|without approval'`로 현재 정책 검사 및 서브에이전트 재검토: 일반 승인 대기·자동 커밋 금지 제거 확인. 과거 승인 사실·PR 승인·사용자 승인 허위 표시 금지 문장은 유지. overlay의 `approved intent` 잔여 표현은 요청 의도·명시적 사용자 결정으로 수정.

## 미실행과 한계

- 문서·템플릿 정책만 수정하여 게임 자동 테스트·실제 창·아트 검사를 실행하지 않았다.
- 전체 Spec Kit workflow, 새 게임 구현, 워크트리 생성·병렬 쓰기·PR 작업은 실행하지 않았다.
- 기존 변경과 정책 변경을 HEAD 기준으로 분리했다. 기존 문서·아트·스크립트 변경은 작업 폴더에 보존한다. 푸시는 하지 않는다.
- 지침과 템플릿의 일치는 검사하지만 미래 세션의 행동이나 모델 성능을 보증하지 않는다. 아트 기능의 개별 검토·사용 상태는 해당 기능 문서가 소유한다.

## 분리 커밋 검증

HEAD를 기준으로 정책 변경만 10개 파일의 Git index에 구성했다. 커밋 대상의 상대 링크 7개가 index에 존재하며 YAML 파싱과 `git diff --cached --check`를 통과했다. 준비 시점 파일 해시와 비교하여 동시 수정된 specs/007-warden-sprint-hibit 파일을 제외한 기존 파일의 내용이 동일함을 확인했다. 해당 기능의 동시 변경은 덮어쓰거나 커밋하지 않았다. 이전 문서 정리·아트·도구 변경은 커밋에서 제외했다.

## 소규모 작업의 브랜치 예외 검증

2026-11-10 최신 사용자 지시에 따라 단순 문서·지침 갱신과 색상 점검·명암 복원 같은 소규모 보정은 현재 브랜치에서 처리하도록 수정했다. constitution 2.1.0은 이 예외를 추가한다. 새 브랜치 생성이나 기존 브랜치 삭제·병합은 수행하지 않았다.

- `git diff --check`: 종료 코드 0, 공백 오류 없음.
- Python `re.findall`·`Path.exists`: 변경 대상 8개 파일의 상대 링크 대상 36개 존재 확인.
- `rg -n`으로 AGENTS·constitution·workflow·progress·plan/checklist 템플릿·overlay의 브랜치 기준 일치 확인.
- 문서·정책만 수정했으므로 게임 테스트·실제 창 검사는 실행하지 않았다. 기존 미커밋 변경은 이번 커밋에서 제외한다.
