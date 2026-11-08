# Implementation Plan: 기본 실행 기반

**Date**: 2026-11-08 | **Spec**: [spec.md](spec.md) | **Status**: Approved

## Summary

engine.py의 작은 장면 클래스와 실행 루프, main.py의 도형 검사 화면, 표준 라이브러리 테스트만 추가한다. 기술 규칙과 수치는 [architecture](../../docs/architecture.md)가 소유한다.

## Technical Context

- **Language/Dependencies**: Python 3.14.7, pico2d==1.5.1. 새 패키지 없음.
- **Runtime**: 게임 .venv/, 도구 .local-tools/python/.
- **Platform/Performance**: Windows. architecture의 검사 기본값을 사용한다. 게임 성능 목표는 아직 없음.
- **Testing**: .venv/Scripts/python.exe -m unittest discover -s tests -v; 실제 main.py 창·키·마우스·종료 검사.

## Constitution Check

- [x] 2026-11-08 사용자 계획 승인으로 상세 명세·계획 검토와 구현 진행을 확인했다.
- [x] 기준 docs를 읽고 사용자 계획 승인을 반영했다.
- [x] 자동·실제 창 검사 및 docs 대응 검토를 계획했다.
- [x] 다른 엔진·웹 서버·DB·에셋 생성·신규 의존성이 없다.

설계 후 재검토: 승인 조건을 충족하여 구현·검증을 진행한다. 기존 호출부·데이터·에셋은 없으며 파괴되는 사용자 데이터가 없다.

## Decisions & Alternatives

[research.md](research.md)를 참조한다. 장면 스택·이벤트 버스·백엔드 추상화 없이 단일 활성 장면과 지연 교체만 둔다. Pico2D의 전역 상태 때문에 동시 실행을 거부하고 부분 생성 실패 정리를 보완한다. 가변 시간 루프는 승인 범위에 충분하며 고정 물리 스텝은 제외한다.

## Project Structure & Interfaces

- engine.py: Scene, Engine, 창·루프·생명주기·종료·전환.
- main.py: 검사 장면과 실행 진입점. 기존 호출부 없음.
- tests/test_engine.py: 위 계약의 정상·실패 자동 검사.
- tests/test_demo.py: 검사 화면의 입력과 이동·전환 확인.
- README.md, docs/{README,progress,architecture,game-design,workflow}.md: 현재 상태·사용 안내.
- specs/001-engine-foundation/: 명세·계획·작업·최신 검증 증거.
- .specify/feature.json: 활성 기능 경로. 사용자 요청에 따라 feature/engine 브랜치를 사용한다.

공개 연결점은 [contracts/scene.md](contracts/scene.md), 상태는 [data-model.md](data-model.md), 실행은 [quickstart.md](quickstart.md)를 참조한다.

## Documentation Impact (mandatory)

| 요구사항/결정 | 기준 docs | 바뀌는 내용 | 갱신 시점 | 검증 방법 |
|---|---|---|---|---|
| FR-001~004 | docs/architecture.md | 루프·장면·오류·기본값 | 설계 즉시 및 구현 후 | 테스트와 코드 대조 |
| FR-005~006 | README.md, docs/README.md, docs/workflow.md | 실행·검증·현재 단계 | 구현 후 | 명령 실행 |
| 승인 범위 | docs/progress.md, docs/game-design.md | 엔진 승인과 게임 기획 분리 | 설계 즉시 및 완료 시 | 사용자 선택과 대조 |
| SC-DOC | verification.md | 실제 명령·결과·미실행·문서 검토 | 검증 후 | 누락 점검 |
| 영향 없음 | docs/systems/, docs/art-direction.md | 규칙·아트를 바꾸지 않음 | 검증 후 이유 기록 | 변경 범위 확인 |

## Verification & Risks

자동 검사: 창 성공·NULL·예외, 각 장면 콜백 오류, 중첩 실행, 종료 우선, 순서·이벤트 원형 보존, 마지막 전환 승리, 진입/퇴장 중 후속 요청, dt 제한·첫 프레임·전환 리셋·대기. 실제 창: 도형 움직임, 마우스 이동, Space 왕복, Escape 종료와 재실행 후 창 닫기. 사람의 게임 플레이 평가는 게임 미구현이므로 해당 없음. Pico2D 내부 핸들 의존은 버전 고정과 테스트로 관리한다.
