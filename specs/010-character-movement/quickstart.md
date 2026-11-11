# Quickstart: 캐릭터 표시·이동

프로젝트 루트에서 게임 Python으로 main.py를 실행한다. 별도 검증 사본에서는 D:/GitHub/circuit-warden/.venv/Scripts/python.exe를 사용한다.

```powershell
& 'D:/GitHub/circuit-warden/.venv/Scripts/python.exe' main.py
& 'D:/GitHub/circuit-warden/.venv/Scripts/python.exe' -B -m unittest discover -s tests -v
```

A/D 또는 ←/→ 유지로 좌우 이동, 해제로 정지한다. 양쪽 동시 입력은 정지하며 하나를 놓으면 남은 방향으로 이동한다. F6 창 크기, F11 전체화면, Escape 종료. 창 전환 후 키를 다시 누르기 전에는 이동하지 않아야 한다.
원본 art 폴더 없이 assets만으로 실행 가능해야 한다. 기존 도형 검사는 `python -m demos.check`, 프레임워크 검사는 `python framework_demo.py`로 실행한다. 자동 입력과 사용자 직접 확인 상태는 [verification](verification.md)을 따른다.
