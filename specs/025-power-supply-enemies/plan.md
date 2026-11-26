# Implementation Plan: 전원 구역 몬스터

**Date** 2026-11-26 | **Spec** [spec.md](spec.md) | **Status** Ready

## Summary

먼저 기존 금속 먼지를 여러 위치에 연결해 공유 전투와 재시작을 검증한다. 이어 팬의 고정 고도 왕복과 콘덴서의 제자리 방전을 기존 예고·공격·회복에 연결한다.

## Technical Context

- **Language/Dependencies** Python + Pico2D. 게임은 `.venv`, 원화 가공은 도구 Python과 내장 ImageGen을 사용한다.
- **Testing** 훈련장 기존 적, 다중 검격·접촉, 방전 범위, 모든 배치의 지형, SDL에서 전투와 두 분기 동선을 확인한다.

## Constitution Check

- [x] 몬스터 제작·첫 맵 통합·로컬 커밋은 사용자 개발 요청 범위다. 디자인은 위임에 따른 구현안이다.
- [x] 기존 맵 명세의 임시 적 제거 요구와 이번 일반 적 배치를 연결했다.
- [x] 코드, 기준 문서, 자동 및 SDL 검증을 같은 증분에 기록한다.
- [x] 기존 충돌·스프라이트·공격 효과 구조를 사용한다.

## Decisions & Alternatives

Team Cherry의 [공식 교차로 소개](https://www.teamcherry.com.au/blog/the-forgotten-crossroads-a-hollow-knight-tour)는 연결된 통로에서 탐색과 연습이 교차하는 구성을 설명한다. [출시판 무해설 플레이 7:45 직후](https://www.youtube.com/watch?v=LNjXu87zmzg&t=465s)에서 조용한 첫 착지 뒤 낮은 통로의 지상 교전과, 이후 높이가 갈리는 공간의 점프 교전을 확인했다. 흡기실을 비우고 연결부는 한 개체부터 시작하며, 팬을 높이 변화가 이미 있는 구역에 둔다.

맵 파일에 종·중심·고도·이동 한계를 둔다. 같은 방 안에서 행동하고 지상형은 플레이어가 같은 높이에 접근할 때 반응한다. 검과 몸통의 연속 검사는 적마다 수행한다. 콘덴서의 몸통 판정과 방전 판정은 독립적이며 방전 시 보이는 범위를 피해 판정에 사용한다. 모든 생존 적의 참조와 종류별 스프라이트는 R 후에도 레벨이 관리한다.

## Project Structure & Interfaces

- `assets/levels/power-supply/map.json`, `game/power_supply_map.py`에 방 배치와 좌표 변환을 연결한다.
- `game/enemy.py`, `game/scene.py`에서 종류별 상태, 수명, 전투 판정을 연결한다.
- `assets/enemies/`에 새 스프라이트와 출처를 추가한다. 다중 판정과 배치 검사는 `tests/integration/test_power_supply_enemies.py`에 둔다.

## Documentation Impact (mandatory)

| 증분 | 문서 | 검증 |
|---|---|---|
| 금속 먼지 배치와 다중 판정 | 기본 적 전투, 기술 구조, 진행 상태 | 기존 적·다중 적 검사 |
| 팬·콘덴서 제작 및 레벨 통합 | 첫 레벨, 아트 기준, 기본 적 전투, 진행 상태 | 배치·방전과 실제 SDL, 두 분기와 복구 |

`feature/power-supply-enemies`에서 각 증분의 검증·문서를 커밋한다. 독립 지형 검토에 gpt-6.2-astra medium을 사용했다.

## Verification & Risks

고도가 다른 적의 판정, 샤프트 착지면, 설비 조작 공간, 여러 적이 동시에 있는 시점과 동일 스윙 기록을 집중 검사한다. 실제 창에서 2×2 렌더, 피격 및 R 입력을 확인한다. 최종 미술과 난이도 체감은 사용자 플레이로 판단한다.
