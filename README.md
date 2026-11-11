# Circuit Warden

`feature/character-movement`에서 워든의 표시·좌우 이동 검사 장면을 구현했습니다. 엔진 기반은 [Draft PR #2](https://github.com/snooy-dev/circuit-warden/pull/2)로 main 통합을 제안한 상태입니다. 최종 게임 규칙·전투는 아직 구현하지 않았습니다. 아트 상태는 [아트 기준](docs/art-direction.md)을 따릅니다. [진행 상태](docs/progress.md)를 참조하세요.
작업을 시작할 때 [프로젝트 문서](docs/README.md), [진행 상태](docs/progress.md), [작업 규칙](AGENTS.md)을 읽습니다.
Spec Kit 개발 흐름과 설치된 에셋 도구의 사용 방법은 [워크플로우](docs/workflow.md)와 [도구 구성](docs/tooling.md)에 기록합니다.

## 요구사항

- Windows
- Python 3.14
- Pico2D 1.5.1

## 가상환경 구성 및 의존성 설치

프로젝트 루트에서 PowerShell로 실행합니다.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 게임 실행

```powershell
.\.venv\Scripts\python.exe main.py
```

A/D 또는 좌우 방향키를 누르고 있으면 이동하고, 놓으면 마지막 방향 idle로 정지합니다. 양쪽 동시 입력은 정지하고 하나를 놓으면 남은 방향으로 이동합니다. F6는 창 크기, F11은 전체화면, Escape는 종료입니다. 창 전환·최소화 때 유지 키를 비웁니다. 이동 속도·배율·경계는 검사용 임시값입니다.

## 코드와 검사 위치

게임에서 쓰는 Level·Canvas·좌표 변환·그리기 API는 `game_framework/`, 창·루프·이벤트·렌더 실행은 `engine/`에 있습니다. 게임 구현은 `game/`, 기본 실행은 `main.py`입니다. 초기 도형 데모 진입점은 정리했습니다. 회귀 검사에 필요한 월드·UI 장면만 `tests/fixtures/`에 둡니다.

`tests/unit/`은 단위 검사, `tests/integration/`은 실제 PNG·SDL 소프트웨어 그리기와 장면 조합 검사입니다. `unittest discover`가 둘 다 탐색합니다. 실제 창 검사는 `tests/smoke/`, 검사 장면은 `tests/fixtures/`에 있습니다. 작은 기능은 바뀐 동작의 직접 확인을 기본으로 하며 자동·전체 검사는 필요한 때만 [검사 선택과 실행법](tests/README.md)에 따라 실행합니다.

스프라이트는 `game_framework`의 ImageStore·SpriteFrame·SpriteClip·SpritePlayer·draw_sprite로 사용합니다. 영역 클리핑·기준점·반전·장면 이미지 정리가 연결돼 있으며 [009 검증](specs/009-sprite-runtime/verification.md)에 최신 검사와 이전 사용자 확인 미완료를 구분했습니다. 이 게임 브랜치는 `assets/warden/`의 idle·좌우 Run을 사용합니다. 원본 `art/`가 없어도 실행됩니다. [010 실행·검증](specs/010-character-movement/quickstart.md)을 참조하세요.

## 다음 게임 개발

플레이어 상태·입력·애니메이션은 `game/character.py`, 레벨 배치와 장면 연결은 `game/scene.py`, 실제 게임 자산은 `assets/`에서 확장합니다. 현재 이동 축·속도·바닥선은 검사 기본값입니다. 다음 기능의 조작·판정·수용 기준을 [게임 설계](docs/game-design.md)와 [시스템 문서](docs/systems/README.md)에 정한 뒤 작은 플레이 가능한 단위로 구현합니다. 현재 준비 상태와 미결정은 [progress](docs/progress.md)를 참조하세요.
