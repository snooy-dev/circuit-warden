# Circuit Warden

기본 실행 기반의 명세·계획은 사용자 승인을 받았으며 기본 실행 기반 구현·검증을 완료했습니다. [진행 상태](docs/progress.md)를 참조하세요.
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
