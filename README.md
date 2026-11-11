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

## 실행과 자동 검사

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

A/D 또는 좌우 방향키를 누르고 있으면 이동하고, 놓으면 마지막 방향 idle로 정지합니다. 양쪽 동시 입력은 정지하고 하나를 놓으면 남은 방향으로 이동합니다. F6는 창 크기, F11은 전체화면, Escape는 종료입니다. 창 전환·최소화 때 유지 키를 비웁니다. 이동 속도·배율·경계는 검사용 임시값입니다.

기존 도형 검사 화면은 `python -m demos.check`로 실행합니다. Space는 장면 전환, 마우스는 표시 이동이며 F6/F11/Escape도 유지합니다.

기본 통합 화면은 `.venv/Scripts/python.exe framework_demo.py`로 실행합니다. 월드와 반투명 UI를 함께 표시하며 마우스 흰색 표시는 UI 논리 위치, H는 UI 하위 트리 숨김/표시, Delete는 해당 하위 트리 삭제입니다. 레벨 왕복 때 월드와 UI를 함께 정리하고 새 초기 배치로 만듭니다.

월드 전용 검사 화면은 `.venv/Scripts/python.exe framework_demo.py --world`로 실행합니다. 왼쪽 클릭은 객체 생성, 오른쪽 클릭은 최근 객체 제거, Space/가운데 클릭은 레벨 왕복, 방향키는 카메라 이동, D는 뎁스 변경입니다. F6/F11/Escape 조작은 유지합니다. 겹친 반투명 도형·여러 이미지의 교차 순서·화면 밖 이동을 확인하는 도형 화면입니다. 실행 증거와 실제 창 자동 검사 방법은 [008 quickstart](specs/008-game-framework/quickstart.md)에 있습니다.

독립 UI 검사는 `.venv/Scripts/python.exe framework_demo.py --ui`로 실행합니다. 방향키는 뒤 패널 이동, H는 하위 트리 숨김/표시, Delete는 하위 트리 삭제, D는 패널 순서 변경, R은 새 UI로 초기화합니다. 마우스는 UI 논리 위치를 표시하고 F6/F11/Escape도 동작합니다. 오른쪽 보라색 표시의 기준점과 패널 비율은 창 크기가 바뀌어도 유지됩니다. 이 모드는 Level·GameMode 없이 UI만 검사합니다.

## 코드와 검사 위치

게임에서 쓰는 Level·Canvas·좌표 변환·그리기 API는 `game_framework/`, 창·루프·이벤트·렌더 실행은 `engine/`에 있습니다. 게임 검사 구현은 `game/`, 기존 엔진 검사 예제는 `demos/`입니다. `main.py`는 캐릭터 검사, `framework_demo.py`는 기존 프레임워크 검사 진입점입니다.

`tests/unit/`은 모의 단위 검사, `tests/integration/`은 장면/데모 조합과 SDL 소프트웨어 그리기 검사입니다. 기존 `python -m unittest discover -s tests -v`로 둘 다 탐색합니다. 실제 창 smoke는 `tests/smoke/`에 있으며 실행은 [008 quickstart](specs/008-game-framework/quickstart.md)를 따릅니다.

스프라이트는 `game_framework`의 ImageStore·SpriteFrame·SpriteClip·SpritePlayer·draw_sprite로 사용합니다. 영역 클리핑·기준점·반전·장면 이미지 정리가 연결돼 있으며 [009 검증](specs/009-sprite-runtime/verification.md)에 최신 검사와 이전 사용자 확인 미완료를 구분했습니다. 이 게임 브랜치는 `assets/warden/`의 idle·좌우 Run을 사용합니다. 원본 `art/`가 없어도 실행됩니다. [010 실행·검증](specs/010-character-movement/quickstart.md)을 참조하세요.
