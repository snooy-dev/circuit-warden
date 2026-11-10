# Implementation Plan: P3 — 월드 좌표·렌더링

**현재 실행 근거**: 2026-11-10 사용자가 각 계획을 새 채팅에서 구현하고 독립 계획을 별도 워크트리에서 병렬 진행하도록 지시했다. 이전 검토 대기는 해제됐다. P1/P2부터 착수하고 P3는 P1/P2, P4는 P3, P5는 P1~P4의 검증된 커밋에 의존한다. 상세 기술 선택은 제안 기본값으로 구현하며 별도 사용자 확정으로 과장하지 않는다.

**Branch**: feature/world-rendering | **Date**: 2026-11-10 | **Spec**: [공통 명세](../spec.md)
**Status**: P1/P2 검증 커밋 통합 / 기본 월드 경로 자동 검증 / 데모 구현 진행
**Input**: [전체 계획](../plan.md), [기술 기준](../../../docs/architecture.md#게임프레임워크-계약-제안-미구현)

## Summary
독립 월드 좌표의 여러 이미지를 화면 밖 제외·뎁스·반투명 규칙에 맞춰 그린다.

## Technical Context
Python 3.14 + Pico2D 1.5.1, Windows. 새 의존성·외부 에셋 생성 없음. 게임 검사에는 원본 저장소 .venv/Scripts/python.exe를 명시한다. 성능 목표 수치는 아직 미정이다.

## Constitution Check
- [x] 2026-11-10 구현 지시와 상세 게임 정책 확정을 구분했다. 선행 P1/P2 검증 커밋을 통합했다.
- [x] 공통 Spec Kit 명세/작업 체계 안에서 범위·제외·선행 계약·검증·docs 영향을 정의했다.
- [x] 검증된 증분의 docs/verification 갱신·커밋과 PR 승인 경계를 유지한다.

## Scope & Dependencies
선행 조건: P1의 Level 소유/순서와 P2의 출력 viewport를 소비한다. Canvas는 필요하지 않다.

요구사항 담당: FR-005, FR-007~010의 월드 렌더링 부분, FR-004/006의 월드 장면 정리·검증.

- 카메라 중심·세로 월드 시야, 월드↔출력 투영/역변환과 실제 그림 크기 변환.
- RenderItem의 순서·bounds·visible·opacity, 등록순 수집·화면 밖 제외·동률 안정 정렬.
- 표준 알파 합성·공유 텍스처/도형 상태 복원, P2 리셋 후 이 경로가 소유한 그리기 자원의 복구 또는 명시적 오류.
- 월드 전용 LevelScene과 framework_demo.py의 월드 검사 모드. Level 수명과 렌더 임시 참조 정리를 연결.

제외: Canvas·UI 트리·UI 배율/anchor는 없다. 객체 풀·공간 인덱스·정렬 캐시·가림 제외·추적 카메라·조작용 줌은 넣지 않는다.

## Project Structure & Interfaces
변경 대상: game_framework.py의 월드 렌더링/카메라 변환/LevelScene, tests/test_world_rendering.py(기존 core 검사와 분리), framework_demo.py, tests/test_framework_demo.py. P2 출력 계약 수정이 필요하면 해당 계약·회귀도 같이 갱신한다. P3 종료 후 P4/P5는 같은 작업트리와 feature/world-rendering 브랜치를 순차 재사용한다.

인계 계약: Level 등록순을 변경하지 않고 RenderItem을 소비한다. 나중 UI 패스를 추가할 수 있지만 빈 Canvas 인스턴스나 UI 전용 인자를 필수로 만들지 않는다. 월드 전용 실행이 완결되어야 한다.

## Verification & Completion
- 객체 간 이미지 교차·뎁스 동률 복원·뎁스 변경·순서 불변·반투명 순서/상태 누출/실패 복원을 자동 검사한다.
- 화면 밖/부분 겹침/중심 밖/미확인 bounds와 update 유지, 좌표 왕복/화면비 변화, 종료·리셋 실패를 검사한다.
- 실제 도형/검사용 이미지로 월드 이동·경계 진입·반투명 겹침·레벨 왕복을 확인한다. 외부 에셋 생성은 하지 않는다.

완료 조건: UI가 없어도 월드 데모가 실행되고 객체 상태·카메라·정렬·알파·정리가 일치한다.

## Documentation Impact (mandatory)
docs/architecture.md의 이 계획 담당 계약과 구현 상태, docs/progress.md의 다음 검토/진행 계획, [verification.md](../verification.md)의 P3 상태·실제 명령/결과/미실행을 함께 갱신한다. 실행 방법이 바뀌면 quickstart.md와 README의 관련 안내만 갱신한다. 공통 spec/data-model/contracts와 어긋나면 같은 증분에서 수정한다. 미승인 정책을 구현 사실로 확정하지 않는다.

## Tasks & Review Decisions
작업은 [공통 tasks.md](../tasks.md)의 T010~T013가 단일 기준이다. 여기에서 별도 중복 체크리스트를 운영하지 않는다. 승인된 범위의 검증된 작은 증분마다 관련 docs·검증과 함께 커밋하며 PR은 별도 승인 대상이다.

미결: 월드 세로 시야 고정/가로 확장은 미승인 게임 정책이다. view_height와 월드 단위 설정은 검토 대상이며 출력 픽셀과 동일 단위로 고정하지 않는다.
