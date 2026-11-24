# Feature Specification: 게임 타이틀 메뉴

**Created**: 2026-11-24

**Input**: 사용자 요청으로 타이틀 메뉴와 재사용 가능한 UI 프레임워크를 구현한다.

## User Scenarios & Testing (mandatory)

### User Story 1 - 게임 시작과 종료 (Priority: P1)

1. 기본 실행 시 Circuit Warden 타이틀과 New Game, Settings, Quit을 표시한다.
2. New Game을 선택하면 기존 전원 구역을 새로 시작한다. `--training`은 훈련장으로 바로 진입한다.
3. Quit은 창과 장면 자원을 정상 종료한다.

### User Story 2 - 화면 설정 (Priority: P2)

1. Settings에서 창 모드와 전체화면을 전환하고 지원되는 창 크기를 순환한다.
2. 적용된 화면 모드와 창 크기를 표시한다. Back 또는 Escape로 타이틀에 돌아온다.

## Requirements (mandatory)

- **FR-001**: 타이틀과 설정 화면은 Canvas의 논리 좌표와 크기 보정을 사용한다.
- **FR-002**: 방향키·Tab으로 버튼을 선택하고 Enter·Space 또는 마우스 클릭으로 실행한다. 눌렀던 버튼에서 떼었을 때만 클릭을 확정한다.
- **FR-003**: 버튼, 텍스트, 포커스와 포인터 처리는 게임 장면과 독립적으로 재사용할 수 있다.
- **FR-004**: 화면 설정은 실행 중 적용하고 플레이로 이어진다. 저장·불러오기, 옵션 영구 저장, 오디오 옵션은 이번 범위 밖이다.
- **FR-005**: 2026-11-24 사용자 후속 요청에 따라 화면에 키 가이드를 표시하지 않는다. 타이틀과 설정은 전원 구역 원경 위에 텍스트 중심으로 배치하고 선택 항목을 표시한다.

## Documentation Contract (mandatory)

현재 동작은 [게임 설계](../../docs/game-design.md), [기술 구조](../../docs/architecture.md), [진행 상태](../../docs/progress.md)에 반영한다.
