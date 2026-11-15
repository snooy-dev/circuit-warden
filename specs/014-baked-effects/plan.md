# Implementation Plan: PNG 효과 재생

**Date**: 2026-11-15 | **Spec**: [spec.md](spec.md) | **Status**: Ready

## Summary

승인 원본에서 전하 전환과 길이별 전류를 오프라인으로 굽고 기존 ImageStore·SpriteFrame으로 공유한다. 픽셀 계산·streaming texture를 제거한다.

## Technical Context

- 게임 Python3.14/Pico2D1.5.1/transitions0.9.3. NumPy는 게임에서 제거한다.
- 생성기는 도구 Python의 Pillow/NumPy와 로컬 pixelfx Node를 사용한다.
- 전하33단계×72위상, bob은 위상 중간 시각으로 샘플. 투명 여백을 잘라 메모리를 줄인다.
- 전류 seed7·12샘플을 길이1~32px 정수,36~64px의4px 간격,72~320px의8px 간격으로 생성한다. 중앙을 기준으로 회전하고 가로만 거리 비율로 조절한다. 1px 미만은 비표시,8px 미만은 광륜 가로 배율을 고정해 끝점 오차를0.25px 이내로 제한한다. 최근접 필터를 명시한다.
- 목표: 동일 장면 p95 감소·16.67ms 이내. 실제 PNG 메모리·로딩도 기록.
- 검증: 원본 안정 프레임, 샘플 전환 오차, 회전 끝점, 공유 수명, 초기화 실패, 게임 표적 회귀와 실제 SDL.

## Constitution Check

- [x] 사용자 미세 차이 허용과 기술 가정 구분, 요청 범위 내 진행.
- [x] 기준 docs와 코드·원본 확인.
- [x] 문서·검증·증분 커밋 계획.
- [x] 새 엔진·웹·DB 없음.

## Decisions & Alternatives

단일 고정 전환 영상은 중간 반전을 잃으므로 상태값은 유지하고 표시만 선택한다. 전류 한 장을 모든 길이에 크게 늘리지 않고 길이별로 굽는다. 정확한 모든 float 조합·셰이더는 범위와 메모리가 커 제외한다. 세부 이유는 research.md.

## Project Structure & Interfaces

scripts/bake-effects/의 Python 전하·Node 전류 생성기 → assets/charge/baked PNG/메타데이터. game/charge.py·teleport_link.py는 이미지 선택만 담당. game/scene.py에서 공유 로드, mode.py에서 링크 아트 전달. game_framework/drawing.py·engine/rendering/drawing.py에 필요한 회전 인자만 추가. tests/performance에서 Git 기준 전후 비교, unit/integration/smoke는 실제 위험에 대응.

## Documentation Impact (mandatory)

feature/baked-effects를 신규 생성. fetch 후 origin/main 추가 커밋 없음. 사용자 PNG/tmp를 보존한다. 읽기 전용 원본 탐색은 Luna medium, 최종 구현·검증은 주 에이전트. 같은 파일 동시 쓰기 없음.

| 요구사항 | docs | 변경 | 시점 | 검증 |
|---|---|---|---|---|
| FR-001/002/004 | architecture.md | PNG 선택·공유·수명 | 증분별 | 코드 대조 |
| FR-003 | art-direction.md | 파생 PNG·허용 차이 | 구현 후 | 화면 |
| FR-004 | tooling.md, tests/README.md | 생성 명령·게임 의존성·검사 | 구현 후 | 재현 |
| FR-005 | progress.md, verification.md | 시간·메모리·한계 | 증분별 | 측정 |

게임 규칙·원본 자산·루트 README는 변경하지 않는다.

## Verification & Risks

전하부터 구현·검증·문서·커밋 후 전류를 연결한다. 회전 추가로 공통 그리기 회귀를 검사한다. GPU 소요시간은 CPU 제출 시간과 구분한다. 낮은 메모리 장비·전류320px 초과 확장은 검증 범위 밖이다.
