# Circuit Warden

기본 실행 기반과 게임프레임워크 P1~P5의 구현·자동/실제 SDL 검증을 완료했습니다. 현재 엔진 통합 브랜치는 `feature/engine`이며 실제 게임 규칙은 아직 구현하지 않았습니다. 아트 상태는 [아트 기준](docs/art-direction.md)을 따릅니다. [진행 상태](docs/progress.md)를 참조하세요.
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

Space로 두 검사 장면을 전환하고 마우스로 표시를 이동합니다. F6로 검사 창 크기를 바꾸고 F11로 보더리스 전체화면과 창 모드를 전환합니다. 창 테두리를 끌어 크기를 바꿀 수도 있습니다. Escape 또는 창 닫기로 종료합니다. 이 화면은 엔진 검사 전용입니다.

기본 통합 화면은 `.venv/Scripts/python.exe framework_demo.py`로 실행합니다. 월드와 반투명 UI를 함께 표시하며 마우스 흰색 표시는 UI 논리 위치, H는 UI 하위 트리 숨김/표시, Delete는 해당 하위 트리 삭제입니다. 레벨 왕복 때 월드와 UI를 함께 정리하고 새 초기 배치로 만듭니다.

월드 전용 검사 화면은 `.venv/Scripts/python.exe framework_demo.py --world`로 실행합니다. 왼쪽 클릭은 객체 생성, 오른쪽 클릭은 최근 객체 제거, Space/가운데 클릭은 레벨 왕복, 방향키는 카메라 이동, D는 뎁스 변경입니다. F6/F11/Escape 조작은 유지합니다. 겹친 반투명 도형·여러 이미지의 교차 순서·화면 밖 이동을 확인하는 도형 화면입니다. 실행 증거와 실제 창 자동 검사 방법은 [008 quickstart](specs/008-game-framework/quickstart.md)에 있습니다.

독립 UI 검사는 `.venv/Scripts/python.exe framework_demo.py --ui`로 실행합니다. 방향키는 뒤 패널 이동, H는 하위 트리 숨김/표시, Delete는 하위 트리 삭제, D는 패널 순서 변경, R은 새 UI로 초기화합니다. 마우스는 UI 논리 위치를 표시하고 F6/F11/Escape도 동작합니다. 오른쪽 보라색 표시의 기준점과 패널 비율은 창 크기가 바뀌어도 유지됩니다. 이 모드는 Level·GameMode 없이 UI만 검사합니다.
