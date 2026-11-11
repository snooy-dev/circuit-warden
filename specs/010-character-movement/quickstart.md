# Quickstart: 캐릭터 표시·이동

프로젝트 루트에서 게임 Python으로 main.py를 실행한다. 별도 검증 사본에서는 D:/GitHub/circuit-warden/.venv/Scripts/python.exe를 사용한다.

```powershell
& 'D:/GitHub/circuit-warden/.venv/Scripts/python.exe' main.py
```

A/D 또는 ←/→ 유지로 좌우 이동, 해제로 정지한다. 양쪽 동시 입력은 정지하며 하나를 놓으면 남은 방향으로 이동한다. F6 창 크기, F11 전체화면, Escape 종료. 창 전환 후 키를 다시 누르기 전에는 이동하지 않아야 한다.
원본 art 폴더 없이 assets만으로 실행 가능해야 한다. 초기 도형 데모 진입점은 후속 정리로 폐기했다. 필요한 엔진/월드/UI 회귀 검사는 [tests 안내](../../tests/README.md)를 따른다. 자동 입력과 사용자 직접 확인 상태는 [verification](verification.md)을 따른다.

## 실제 창 자동 검사

기존 출력 폴더를 프로젝트 밖에 만들고 아래 명령을 실행한다. 프로젝트 루트 밖에서 실행해도 에셋을 찾는다.

```powershell
& 'D:/GitHub/circuit-warden/.venv/Scripts/python.exe' -B 'D:/GitHub/circuit-warden/.local-tools/work/character-movement/tests/smoke/character_smoke.py' --output-dir 'D:/GitHub/circuit-warden/.local-tools/work/character-preview'
```

idle·좌/우 Run·정지·반대 키·포커스 상실·F6/F11·Escape·자원 정리를 검사하고 PNG 6장을 저장한다. 출력 폴더는 미리 존재해야 한다. 대역 검사와 실제 SDL 이벤트 자동 주입은 사용자 직접 키 조작과 구분한다.
