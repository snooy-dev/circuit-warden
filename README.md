# Circuit Warden

현재 기능 브랜치에는 GameplayMode 기반 Warden A/D 이동·왼쪽 클릭 단발 공격·베기 이펙트와 애니메이션이 구현돼 있습니다. 피해·승패 규칙은 없으며 사용자 직접 조작감·미술 품질 평가는 미확인입니다. 아트 상태는 [아트 기준](docs/art-direction.md), 현재 범위는 [진행 상태](docs/progress.md)를 참조하세요.
작업을 시작할 때 [작업 규칙](AGENTS.md)과 [진행 상태](docs/progress.md)를 확인하고, 작업별 참고 문서는 [프로젝트 문서](docs/README.md)에서 찾습니다.
Spec Kit 개발 흐름과 설치된 에셋 도구의 사용 방법은 [워크플로우](docs/workflow.md)와 [도구 구성](docs/tooling.md)에 기록합니다.

## 요구사항

- Windows
- Python 3.14
- Pico2D 1.5.1, transitions 0.9.3

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

기본 게임 창은 1280×720(16:9)입니다. A/D를 누르고 있으면 이동하고, 놓으면 마지막 방향 idle로 정지합니다. 양쪽 동시 입력은 정지하고 하나를 놓으면 남은 방향으로 이동합니다. 왼쪽 클릭은 현재 방향으로 공격 1회입니다. 공격 중 정지하고 추가 클릭은 무시하며, 종료 후 현재 누른 A/D를 반영합니다. 베기 잔상은 공격 위치에서 700ms까지 남습니다. F6는 창 크기, F11은 전체화면, Escape는 종료입니다. 창 전환·최소화 때 유지 키를 비웁니다. 이동 속도·배율·경계는 검사용 임시값입니다.

## 코드와 검사 위치

게임에서 쓰는 Level·Canvas·좌표 변환·그리기 API는 `game_framework/`, 창·루프·이벤트·렌더 실행은 `engine/`에 있습니다. 게임 구현은 `game/`, 기본 실행은 `main.py`입니다. 초기 도형 데모 진입점은 정리했습니다. 회귀 검사에 필요한 월드·UI 장면만 `tests/fixtures/`에 둡니다.

`tests/unit/`은 단위 검사, `tests/integration/`은 실제 PNG·SDL 소프트웨어 그리기와 장면 조합 검사입니다. `unittest discover`가 둘 다 탐색합니다. 실제 창 검사는 `tests/smoke/`, 검사 장면은 `tests/fixtures/`에 있습니다. 작은 기능은 바뀐 동작의 직접 확인을 기본으로 하며 자동·전체 검사는 필요한 때만 [검사 선택과 실행법](tests/README.md)에 따라 실행합니다.

스프라이트는 `game_framework`의 ImageStore·SpriteFrame·SpriteClip·SpritePlayer·draw_sprite로 사용합니다. 영역 클리핑·기준점·반전·장면 이미지 정리가 연결돼 있으며 [009 검증](specs/009-sprite-runtime/verification.md)에 최신 검사와 이전 사용자 확인 미완료를 구분했습니다. 현재 실행은 `assets/warden/`의 idle·좌우 Run·아웃라인 공격 v6·전기 베기 v4를 사용합니다. 원본 `art/`가 없어도 실행됩니다. [011 실행·검증](specs/011-basic-gameplay/quickstart.md)을 참조하세요.

## 다음 게임 개발

모드 입력 전달은 `game/mode.py`, 플레이어 상태·입력·애니메이션은 `game/character.py`, 레벨 배치와 장면 연결은 `game/scene.py`, 실제 게임 자산은 `assets/`에서 확장합니다. 수평 A/D 이동과 공격 정책은 [기본 게임플레이](docs/systems/basic-gameplay.md)를 따르며 속도·바닥선은 기술 기본값입니다. 다음 기능의 조작·판정·수용 기준을 [게임 설계](docs/game-design.md)와 [시스템 문서](docs/systems/README.md)에 정한 뒤 작은 플레이 가능한 단위로 구현합니다. 현재 준비 상태와 미결정은 [progress](docs/progress.md)를 참조하세요.
