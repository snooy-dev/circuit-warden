# Tasks: 첫 레벨 전원 구역

## Phase 1: Setup

- [x] T001 기획 원본·아트·카메라 기준과 범위 문서화 (`spec.md`, `plan.md`)

## Phase 2: Foundational

- [x] T002 이동 가능한 충돌·시작점·종점 배치 (`assets/levels/power-supply/map.json`)

## Phase 3: User Story 1

- [x] T003 [US1] 원경·구조·소품 생성 및 배치 (`assets/levels/power-supply/`)
- [x] T004 [US1] 레벨 로드, 전투 배치, 도착·재시작 통합 (`game/scene.py`)
- [x] T005 [US1] 맵·웹 도달 검사와 Tiled 내보내기 (`art/levels/power-supply/`)

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T006 실제 창·게임 경로 검증 및 기준 갱신 (`verification.md`, `docs/`)

## 후속 증분

- [x] T007 먼지 원경·솜털·팬 회전자 생성 및 hi-bit 가공 (`art/levels/power-supply/dust-revision/`)
- [x] T008 먼지 배치와 흡기 팬 회전 통합 (`assets/levels/power-supply/map.json`, `game/power_supply_map.py`)
- [x] T009 맵·실제 SDL 검증 및 기준 갱신 (`verification.md`, `docs/`)
