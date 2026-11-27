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
- [x] T010 첫 레벨 공통 픽셀 격자 출력 (`game/scene.py`)
- [x] T011 실제 SDL 픽셀·창 전환·입력 검증 및 기준 갱신 (`verification.md`, `docs/`)
- [x] T012 전원선 에셋과 등장 전류 시작점 배치 (`assets/levels/power-supply/`)
- [x] T013 첫 로드·R·빠른 입력에 등장 연출 연결 (`game/scene.py`, `game/character.py`)
- [x] T014 실제 SDL과 맵 검사, 기준 및 검증 결과 갱신 (`tests/smoke/power_supply_smoke.py`, `docs/`)
- [x] T015 바닥 접점 에셋과 등장 시작점 교체, SDL·맵 검사 및 설계 동기화 (`assets/levels/power-supply/`, `verification.md`, `docs/`)
- [x] T016 케이스 벽면 전원 인렛과 내부 단자 스폰 연결, SDL·맵 검사 및 설계 동기화 (`assets/levels/power-supply/`, `verification.md`, `docs/`)
- [x] T017 실제 C14의 삽입구와 얕은 돌출 비율을 반영하고 벽면 스폰 연결 검사 (`assets/levels/power-supply/`, `verification.md`, `docs/`)
- [x] T018 상단 케이블 낙뢰로 등장 연출 교체, 인렛 제거, SDL 등장·입력 및 맵 검사 (`assets/levels/power-supply/`, `verification.md`, `docs/`)
- [x] T019 갈라진 번개와 바닥 충격의 등장 전용 시트 제작·통합·SDL 확인 (`scripts/bake-effects/`, `assets/levels/power-supply/`, `game/scene.py`, `verification.md`, `docs/`)
- [x] T020 시작 케이블의 피복 손상과 구리 심선 제작, 낙뢰 접점 정합 및 SDL 확인 (`assets/levels/power-supply/`, `verification.md`, `docs/`)
- [x] T021 낙뢰 타격의 카메라 흔들림과 정상 복귀 구현·SDL 확인 (`game/scene.py`, `verification.md`, `docs/`)

## 레벨 동선 재설계

- [x] T022 [US1] 전원 구역의 연습·방열판·상하 경로·출력 동선과 구조물의 표시 및 충돌을 맞춘다 (`assets/levels/power-supply/map.json`, FR-008~FR-010)
- [x] T023 [US1] 훈련장 공중 발판 아래의 보행 높이를 확보한다 (`game/training_map.py`, FR-009)
- [x] T024 [US1] 양방향 착지와 하부 보행, 중앙 틈 낙하와 경로 합류를 검증하고 현재 기준을 갱신한다 (`tests/smoke/power_supply_smoke.py`, `docs/`, `verification.md`, FR-008~FR-010)

## 전망대와 전력 변환부 재제작

- [x] T025 [US1] 안전한 연습 발판과 정비 전망대, 두 경로, 낙하·복귀, 출력의 충돌·시야·전하 배치를 실제 입력으로 확인한다 (`assets/levels/power-supply/map.json`, `tests/smoke/power_supply_smoke.py`, FR-011~FR-012)
- [x] T026 [US1] 새 원경과 정비 구조물 및 방전 단서를 제작하고 화면에서 착지면·위험의 가독성을 확인한다 (`assets/levels/power-supply/`, `game/power_supply_map.py`, FR-013)
- [x] T027 [US1] 맵·경로·기본 진입·재시작을 검사하고 기준 문서와 증거를 갱신한다 (`docs/`, `specs/021-power-supply-level/verification.md`, FR-011~FR-013)

## 정비 샤프트와 순환 동선

- [x] T028 [US1] 출시판 지도 및 방 연결 데이터를 대조하고 2층 순환 동선을 배치한다 (`assets/levels/power-supply/map.json`, FR-014~FR-015)
- [x] T029 [US1] 첫 레벨의 수직 카메라와 기존 소재를 사용한 방별 구조물을 적용한다 (`game/scene.py`, `game/power_supply_map.py`, `assets/levels/power-supply/`, FR-016)
- [x] T030 [US1] 중앙 출력 경로·배기 순환·전하·방전·오프닝을 확인하고 기준 문서와 실행 증거를 갱신한다 (`tests/smoke/power_supply_smoke.py`, `docs/`, `verification.md`, FR-014~FR-016)

## 배전망 복구와 상층 귀환

- [x] T031 [US1] 인게임 레퍼런스의 구도·위험 배치를 대조하고 3층 구역과 두 순환 경로를 제작한다 (`assets/levels/power-supply/map.json`, FR-017~FR-019)
- [x] T032 [US1] 릴레이, 교량, 차단기, 셔터와 장치 상태를 연결하고 구조 면과 소품을 정돈한다 (`game/power_supply_map.py`, `game/scene.py`, `game/character.py`, FR-017~FR-019)
- [x] T033 [US1] 전원 복구와 귀환을 실제 기본 창에서 확인하고 기준 문서와 실행 증거를 갱신한다 (`tests/smoke/power_supply_smoke.py`, `docs/`, `verification.md`, FR-017~FR-019)

## 전원 복구와 귀환 지름길

- [x] T034 [US1] 하층과 서쪽 귀환 동선을 블록아웃하고 단일 전원 상태를 실제 SDL 입력으로 검증한다 (`map.json`, `game/`, `tests/smoke/power_supply_smoke.py`, FR-020~FR-021)
- [x] T035 [US1] 장치 원화를 가공·배치하고 점프·전하 귀환, 출력, 재시작과 실제 화면을 확인한다 (`assets/levels/power-supply/`, `docs/`, `verification.md`, FR-020~FR-022)

## 변압실의 두 경로

- [x] T036 [US1] 상부 우회와 하부 전투 블록아웃에 버스바와 단일 복구 상태를 연결한다 (`map.json`, `game/`, FR-023~FR-024)
- [x] T037 [US1] 방별 원경과 지형·위험의 hi-bit 에셋을 가공하고 실제 배율에서 배치한다 (`assets/levels/power-supply/`, FR-025)
- [x] T038 [US1] SDL에서 두 경로의 서로 다른 결과, 피해와 차단, 귀환·출력을 확인하고 현재 문서를 갱신한다 (`tests/smoke/power_supply_smoke.py`, `docs/`, `verification.md`, FR-023~FR-025)

## 상하 회로와 중앙 접속부

- [x] T039 [US1] 접속부·하강 갤러리·하층과 배선탑의 블록아웃 및 덮개·복구 상태를 구현한다 (`map.json`, `game/`, FR-026~FR-028)
- [x] T040 [US1] 방별 hi-bit 원경과 표면을 새 층계와 방 연결에 배치한다 (`assets/levels/power-supply/`, FR-029)
- [x] T041 [US1] 실제 SDL에서 초회 동선과 선택 지름길, 복구·출력·초기화의 결과를 확인하고 검증·기준을 갱신한다 (`tests/smoke/power_supply_smoke.py`, `docs/`, `verification.md`, FR-026~FR-029)

## 서로 연결된 여덟 공간

- [x] T042 [US1] 하층·배전탑·상층의 충돌과 출입구를 배치하고 방 경계 카메라와 적 없는 파워 맵을 구현한다 (`map.json`, `game/`, FR-030~FR-032)
- [x] T043 [US1] 새 방의 환경·지형을 가공하고 2×2 게임 픽셀 격자에 배치한다 (`assets/levels/power-supply/`, FR-033)
- [x] T044 [US1] 실제 게임 입력과 화면에서 양방향 방 전환, 모든 방의 연결, 복구·출력·초기화를 확인하고 문서를 갱신한다 (`tests/`, `docs/`, `verification.md`, FR-030~FR-033)

## 복구 전 상하 탐색

- [x] T045 [US1] 전원 상태별 연결도를 정하고, 중앙 갈림길과 상하 합류 및 선택 순환을 블록아웃한다 (`map.json`, FR-034~FR-036)
- [x] T046 [US1] 산화·먼지 자산을 생성하여 hi-bit로 가공하고 확정된 이동면과 표지에 적용한다 (`assets/levels/power-supply/`, FR-037)
- [x] T047 [US1] 실제 SDL에서 상층 우선과 하층 우선의 완주, 복구 전 상하 전환, 닫힌 출력과 복구 상태·초기화를 검사한다. 후속 변경에서는 사용자 요청에 따라 추가 플레이 실행을 생략하고 수직 연결의 배치와 충돌을 확인한다 (`tests/smoke/power_supply_smoke.py`, `verification.md`, FR-034~FR-036)
- [x] T048 [US1] 판금·기판의 이어지는 면과 샤프트 지지를 구성하고, 최하층 부하 시험실과 양쪽 접근로를 배치한다. 설계·기술·아트 기준과 진행 상태를 동기화한다 (`map.json`, `docs/`, `verification.md`, FR-038~FR-039)

## 수직으로 엮은 설비와 다음 맵의 관문

- [x] T049 [US1] 상태별 방 접속도를 만들고 수직 냉각 경로, 전하 경로, 조용한 중앙과 상부 관문을 블록아웃한다 (`map.json`, FR-040~FR-043)
- [x] T050 [US1] 새 개구부와 이동면에 원경·받침·전경 및 마모 재질을 합성한다 (`assets/levels/power-supply/`, FR-044)
- [x] T051 [US1] 오프스크린 입력으로 양쪽 경로·복구·보스 구역 통과·출력을 확인하고 최종 화면과 문서를 맞춘다 (`tests/smoke/power_supply_smoke.py`, `docs/`, `verification.md`, FR-045)
