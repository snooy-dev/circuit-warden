# 검증 상태: 게임프레임워크

2026-11-10 사용자가 P1~P5 구현과 독립 계획의 별도 워크트리 병렬 작업을 지시했다. P2 담당 작업트리의 결과이며 전체 프레임워크 완료 보고가 아니다.

## 계획별 상태

| 계획 | 상태 | 근거 / 다음 작업 |
|---|---|---|
| P1 객체·규칙 | 독립 채팅 담당 | 이 작업트리에서는 미구현 |
| P2 창·출력 | 구현·자동/실제 SDL 검사 통과 / 로컬 커밋 인계 준비 | 아래 결과 참조 |
| P3 월드 렌더링 | 선행 결과 대기 | P1/P2 검증 커밋 통합 필요 |
| P4 Canvas UI | 선행 결과 대기 | P3 검증 커밋 필요 |
| P5 통합 | 선행 결과 대기 | P1~P4 후 전체 판정 |

## P2 자동 검증

- 기준 커밋: `1940dd423daf423a84637b9ccec7d23eb92d722f`, 브랜치: `feature/display-management`.
- 명령: `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe -m unittest discover -s tests -v`
- 결과: **27개 통과**, 기존 16개 회귀 포함. 모의 SDL로 window/output/viewport, 2배 DPI 좌표·휠 제외, 최소화/0 크기 update·종료 유지, 프레임 중 크기 변경 표시 생략, 리셋 이벤트/누적 세대, 전환 지연·실패 정리·창 크기 복귀를 검사했다. 실제 ctypes SDL_Event를 채워 창/마우스/키 반복 필터/두 종류 리셋 전달과 출력 조회 오류도 검사했다.
- 실제 SDL 명령: `& D:/GitHub/circuit-warden/.venv/Scripts/python.exe tests/display_smoke.py C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c41a-3137-7f90-9330-4a9370e0b7ce`
- 결과: 종료 0, `PASS: resize/fullscreen/restore/minimize/mouse/render`. 640×480 → 960×540 → 1536×864 보더리스 → 960×540 복귀를 실제 window/output 조회와 assert로 확인했다. 최소화 상태 output_valid=False, draw 수 불변, 복구 후 SDL_WarpMouseInWindow에서 실제 이동 이벤트를 받아 출력 좌표 일치까지 확인했다. SDL_RenderReadPixels/IMG_SavePNG로 저장한 p2-stage-1/2/3/6.png를 직접 열어 도형·출력 경계·마우스 표시를 관찰했다. 자원 생성/이미지 복구는 P3 범위다.
- 자동 UI 도구로 main.py의 기본 창·도형을 관찰했다. F6 자동 키 입력 뒤 크기 변화는 확인하지 못했고 원인을 단정하지 않는다. 이후 실제 SDL 검사는 위 별도 스크립트에서 앱 내부 API로 수행했다. 사용자 직접 확인은 받지 않았다.
- 실제 window/output 비율은 1:1이었다. 모의 2배 DPI는 자동 검사로 통과했으나 실물 DPI 배율 변경·다른 모니터 이동·직접 키 조작/테두리 드래그는 미확인이다. 이 한계를 실물 검증 성공으로 표시하지 않는다.
- 정적 검증: `git diff --check` 통과, 변경된 Markdown 13개의 로컬 파일 링크 대상 존재 검사 통과. 최종 자동 검사 27개와 실제 SDL 검사도 재실행하여 모두 통과했다.

## 인계 상태

- 브랜치 `feature/display-management`, 기준 SHA `1940dd423daf423a84637b9ccec7d23eb92d722f`.
- 최신 사용자 작업 규칙이 이전 AGENTS 지시를 대체하며 검증된 증분의 코드·docs·명세·검증 근거를 로컬 커밋하도록 명시했다. 이전 커밋 차단 상태는 해소 근거가 생겼으며 현재 변경을 커밋하고 실제 SHA로 갱신한다.
- 2026-11-10 최신 인계: 독립 P1/P2만 별도 브랜치·워크트리에서 병렬 진행한다. P2 브랜치는 feature/display-management다. P3는 P1/P2 검증 커밋을 C:/Users/Developer/.codex/worktrees/cbb2/circuit-warden의 feature/world-rendering에 통합한다. 이후 P4와 P5는 별도 브랜치를 만들지 않고 같은 워크트리/브랜치를 P3 → P4 → P5 순서로 재사용한다. 선행 종료 전에 다음 쓰기를 시작하지 않으며 기존 브랜치·워크트리는 보존한다.
- PR 생성·게시·병합은 수행하지 않는다. P3는 커밋된 코드·계약·검증 결과를 확인한 뒤 통합한다.

## 문서와 범위 대조

P2 계획·T006/T007·FR-006/010의 출력 기반을 engine.py/main.py 및 tests에 대응했다. architecture/progress/README/quickstart와 공통 명세·계획·계약의 오래된 전체 보류 표현을 해당 범위에서 수정했다. 상세 기술 선택은 구현 기본값이며 사용자 설계 확정과 구분한다. systems/art-direction/game-design의 게임 정책·아트는 바뀌지 않아 수정하지 않았다. Pico2D 설치본, 의존성, 외부 에셋·서비스, 원본 저장소의 미커밋 파일과 다른 워크트리는 수정하지 않았다.

P3는 viewport/output_valid와 reset_generation을 사용하고 이미지 자원 복구를 구현해야 한다. 원래 조사 근거는 research.md에 보존하며 이전 실험·설계 검토를 P2 실행 증거로 사용하지 않는다.
