# Quickstart: 기본 적 전투 검증

1. 작업트리에서 게임용 `.venv`의 Python을 사용한다. 게임 환경이 주 체크아웃에 있으면 해당 경로를 명시한다.
2. `.\.venv\Scripts\python.exe -m unittest tests.unit.test_basic_enemy tests.integration.test_basic_enemy tests.integration.test_character_scene tests.integration.test_jump_animation tests.integration.test_dash_animation tests.unit.test_character tests.unit.test_input_buffer`로 표적 검사를 실행한다.
3. `.\.venv\Scripts\python.exe -m tests.smoke.basic_enemy_smoke`로 실제 SDL 창에서 기본 전투를 검사한다.
4. 필요하면 `.\.venv\Scripts\python.exe main.py`로 화면을 직접 열어 양쪽에서 베기, 제자리 점프 회피, 워든 체력 0 및 R 재시작을 확인한다. 화면 관찰과 사용자 직접 조작은 별도로 기록한다.
