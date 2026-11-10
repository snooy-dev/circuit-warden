# 검증 상태: 게임프레임워크

**현재 실행 근거**: 2026-11-10 사용자가 각 계획을 새 채팅에서 구현하고 독립 계획을 별도 워크트리에서 병렬 진행하도록 지시했다. 이전 검토 대기는 해제됐다. P1/P2부터 착수하고 P3는 P1/P2, P4는 P3, P5는 P1~P4의 검증된 커밋에 의존한다. 상세 기술 선택은 제안 기본값으로 구현하며 별도 사용자 확정으로 과장하지 않는다.

**상태**: 분리 계획 검토 대기 / 모든 구현 보류. 완료 보고 아님.
**근거**: 2026-11-10 사용자가 이번에는 계획을 읽고 승인 여부·수정사항을 제시한다고 지시했다.

## 계획별 상태

| 계획 | 상태 | 실제 실행 근거 / 다음 검토 |
|---|---|---|
| P1 객체·규칙 | 미승인·미구현 | 다음 검토 대상. core 자동 검사는 아직 없음 |
| P2 창·출력 | 미승인·미구현 | 기존 001 검사 성공은 가변 출력/전체화면 성공 근거가 아님 |
| P3 월드 렌더링 | 미승인·미구현 | 합성 컨테이너 실험은 실제 렌더 구현 성공 근거가 아님 |
| P4 Canvas UI | 미승인·미구현 | UI 트리/배율/패스 실행 검증 없음 |
| P5 통합 | 미승인·미구현 | P1~P4 선행. 통합 검사/전체 완료 판정 없음 |

## 실제 확인
| 작업·명령 | 결과 | 범위 |
|---|---|---|
| 원본 폴더의 .venv/Scripts/python.exe -m unittest discover -s tests -v | 기존 16개 통과 | 엔진 출발 상태만 확인 |
| git log/branch와 main..feature/engine 비교 | main에 엔진 없음. d2a0a8c는 엔진 5bfca50과 최신 정책을 포함 | 새 feature/game-framework 기반 선택 |
| 관리 워크트리 생성, git switch -c feature/game-framework | 별도 작업 폴더·브랜치 생성 | 원본 미커밋 변경 보존 |
| resolve-template.ps1 spec-template -Json, setup-plan.ps1 -Json, setup-tasks.ps1 -Json, check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks | 성공 | 프로젝트 템플릿과 필수 문서 확인 |
| 원본 게임 Python -m unittest discover -s tests -p test_game_framework.py -v (새 작업 폴더) | ModuleNotFoundError: game_framework, 예상 미구현 실패 | 기능 구현 성공 증거 아님 |
| 계획·명세·작업 대조 | FR 10개, SC 3개에 작업 대응. 구조·파이프라인은 검토안이며 저장 범위·세부 API·업데이트 결과 판정은 최종 검토 대상 | 사용자 상세 승인과 구분 |

## 보류 시점과 문서 영향
게임프레임워크 런타임 코드는 작성하지 않았다. 작성한 테스트 초안은 drafts/test_game_framework.py.txt로 옮겨 기존 자동 검사에 영향을 주지 않게 보존했다. 구현·새 테스트 통과·실제 창·converge·증분 커밋은 수행하지 않았다. 사용자 직접 확인도 없다.

spec/plan/tasks와 research·data-model·contracts·quickstart·checklist, docs/architecture·progress·game-design을 레벨 소유·씬 참조·규칙 분리·입력/업데이트/렌더링·이미지별 뎁스·월드/UI 분리 제안에 맞췄다. 계획 검토/구현 보류를 유지한다. README·workflow의 기존 엔진 실행 안내는 변경하지 않았다. systems·art-direction 및 원본 폴더의 미커밋 작업은 변경하지 않았다.

## 명칭 조사 범위

공식 Unity Scene/GameObject/uGUI Canvas/2D 정렬, GameMaker Room/Object/UI Layers, Godot Scene/CanvasItem/CanvasLayer 및 Unreal GameMode 문서를 웹으로 확인하고 research.md에 출처·해석·후보를 구분했다. 일부 빠른 시작 UI URL은 조회 실패하여 GameMaker 월간 UI Layers 본문과 Runtime 문서를 확인했다. 외부 엔진 설치·실행은 하지 않았다. Python 자료 구조의 독립 비교는 아래와 같이 수행했다. Renderer는 사용자 지정 이름이다. Canvas·UIElement는 이후 구체 자료 구조 제안에 포함한 미승인 후보이며 LevelScene 이름은 유지한다.

## 자료 구조 검토용 실험

게임 Python으로 `C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c37d-0ed1-7d02-9951-6a21f240d309/framework-container-comparison.py`를 실행했다. 종료 0, 전체 순서·잔존 항목·제거/신규 항목의 같은 단계 갱신 방지 assert 통과. 준비 3회·측정 31회, GC 측정 구간 중지, 준비/검사 시간 제외. 최종 수치는 research.md와 같은 폴더의 JSON에 보존한다. 컨테이너 단품과 합성 단계 비교이며 실제 게임 콜백·UI 레이아웃·그리기·GPU·전체 게임 프레임 검증이 아니다. 프레임워크 구현·implement·전체 workflow는 실행하지 않았다.

공식 Cocos RenderCommand, Godot drawing commands, Unreal PrimitiveComponent/SceneProxy, Python 3.14 list/dict/sort/heap 문서로 명칭·연산 근거를 확인했다. 일부 문서 접근이 실패한 경우 검색에 반환된 공식 문서 본문과 접근 가능한 공식 API 문서를 사용했다. 서브에이전트의 읽기 전용 검토에서 단계 스냅샷 시점과 정렬 캐시 동률 문제를 확인하고 계약에 반영했다.

## 화면 밖·반투명 조사

로컬 Pico2D의 Image.draw/opacify·도형 함수를 rg와 Get-Content로 읽어 SDL 호출/공유 상태 변경을 확인했다. 최초 wildcard 경로 조회는 Windows 경로 오류로 실패했고 rg --files로 실제 경로를 찾아 읽었다. 공식 Unity bounds, SDL2 blend/alpha modulation/texture blend 문서도 확인했다. FR-008/009, 보기 원점·범위·불투명도 계약과 수용 검사를 관련 docs·spec·plan·data-model·contracts·tasks·quickstart·research에 반영했다. 새 요구는 고려 대상으로 반영했으며 상세 제안의 사용자 승인·구현 재개로 기록하지 않았다. 창/픽셀 합성/성능·신규 게임 테스트는 미실행이다.

## 독립 좌표·가변 출력 검토

engine.py의 고정 창 크기와 Pico2D open_canvas/resize_canvas/get_events/y 변환을 읽었다. SDL2의 창 크기·renderer 출력 픽셀·전체화면 공식 문서를 확인했다. 월드/Canvas 논리 좌표·양방향 변환·UI 루트 anchor·Engine 출력 상태/필요 이벤트 보존을 FR-010 및 관련 계획/계약에 반영했다. 기존 1:1 이동 제안은 대체했다. 읽기 전용 수식 검토에서 y 방향과 0 크기의 렌더/입력 제외 조건을 확인했다. 실제 코드·의존성·창 상태 변경은 없으며 해상도/DPI/전체화면/리셋·좌표 왕복 테스트는 미실행이다.

## 문서 검증

엔진 내부 자료 구조는 Cocos2d-x v4 소스, Unity uGUI main 소스, Unreal 5.5 ULevel 공식 API에서 확인했다. Defold는 읽기 전용 서브에이전트가 공식 GitHub 연결로 개발 커밋 9066bb952b42ddfd2cd6a68c48352b0937dab4e3의 선언·사용 코드를 대조했다. 주 에이전트의 Defold raw URL 재조회는 cache miss로 실패하여 해당 독립 조사 근거를 통합했다. 공식 엔진 조사와 Python dict 삽입 순서·sort 안정성을 근거로 Level=dict, Canvas=roots/children 목록 트리, Renderer=월드 전역/UI 형제 정렬 구체안을 작성했다. architecture·research·spec·plan·data-model·contracts·tasks·quickstart·progress·game-design을 대조·갱신했다. UI 계층·하위 트리 수명/표시·로컬 뎁스와 전체 UI 스냅샷은 새 기술 제안이며 사용자 승인으로 표시하지 않았다. 엔진 설치·실행·새 성능 측정은 하지 않았다.

분리 계획을 포함한 관련 Markdown 19개를 대상으로 Python pathlib/re 정적 검사(로컬 링크 대상·줄 끝 공백, 미구현 런타임 파일 부재 확인)와 git diff --check를 통과했다. 역할·프레임 순서·보류 상태를 문서 간 대조했다. 현재 변경은 문서만이며 물리·별도 simulate 단계는 범위에 없다. 신규 기능 테스트·실제 창 검사는 구현 보류로 실행하지 않는다.

읽기 전용 설계 검토에서 동일 인스턴스 재등록·전체 UI DFS 스냅샷 시점·종료 중 등록·부모 숨김·UI 로컬 정렬 제약을 확인해 계약에 반영했다. 위 검토는 실행 테스트가 아니다. 추가 수용 검사는 tasks/quickstart에 계획했으며 기존 합성 컨테이너 실험을 UI 트리 성능 증거로 사용하지 않는다.

## 계획 분리 검증

plan.md를 다섯 하위 계획의 안내·요구사항 대응으로 바꾸고 plans/01-core.md~05-integration.md를 작성했다. 각 문서에 범위·제외·선행/인계 계약·변경 파일·검증·완료·docs 영향을 명시하고 tasks.md를 같은 순서로 재구성했다. 공통 spec/research/data-model/contracts는 보존했다. `.specify/feature.json`과 브랜치·코드·원본 작업 폴더는 변경하지 않았다. 읽기 전용 분할 검토에서는 의존순환·책임 누락이 없음을 확인했으며 이는 구현 검증이 아니다. 문서 검사에서 하위 계획 5개·필수 섹션·구현 보류, 작업 ID T001~T022의 유일성·미실행 구현 작업 20개, 활성 기능 포인터와 런타임 파일 부재를 확인했다. 문서 검사 결과는 위 문서 검증에 따른다.

## 다음 단계
분리 구성과 우선 P1의 사용자 승인 여부·수정사항을 받은 뒤 해당 계획과 상태를 갱신한다. 한 계획의 승인을 전체 승인으로 확대하지 않는다. 승인 전 implement나 전체 workflow를 실행하지 않는다. 보존된 옛 테스트 초안은 새 계획의 검증 증거가 아니며 승인 후 다시 작성해야 한다.
