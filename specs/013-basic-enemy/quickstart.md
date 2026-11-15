# Quickstart: 기본 적 전투 검증

1. 작업트리 루트에서 게임 Python을 지정한다. 이 작업트리는 `D:/GitHub/circuit-warden/.venv/Scripts/python.exe`를 재사용한다. 별도 설치에서 `.venv`가 있으면 그 경로를 사용한다.
2. 전투 규칙은 `& 'D:/GitHub/circuit-warden/.venv/Scripts/python.exe' -B -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy -q`로 확인한다. 입력·점프·대시 검사 범위는 실제 변경 위험에 따라 선택하며 실행 결과는 [verification](verification.md)에 기록한다.
3. 실제 창은 `& 'D:/GitHub/circuit-warden/.venv/Scripts/python.exe' -B -m tests.smoke.basic_enemy_smoke --output-dir art/enemies/verification`으로 검사한다.
4. 직접 플레이는 `& 'D:/GitHub/circuit-warden/.venv/Scripts/python.exe' main.py`로 실행한다. A/D 이동, Space 점프, Shift 대시, 왼쪽 클릭 공격, R 전투 재시작이다. 자동 SDL 관찰과 사용자 직접 조작은 따로 기록한다.
