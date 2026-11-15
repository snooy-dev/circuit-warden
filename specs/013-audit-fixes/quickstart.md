# Quickstart

게임 Python은 프로젝트 루트의 `.venv/Scripts/python.exe`다. 의존성 변경 시 `-m pip install -r requirements.txt`로 준비한다.

1. 예약·입력: `-B -m unittest tests.unit.test_input_buffer tests.integration.test_character_scene -q`.
2. 표시·클릭: `-B -m unittest tests.unit.test_engine tests.integration.test_charge_scene -q`.
3. 예외 참조: `-B -m unittest tests.unit.test_game_framework -q`.
4. 효과: `-B -m unittest tests.unit.test_charge_teleport tests.unit.test_teleport_link -q`.
5. 성능: `-B tests/performance/charge_benchmark.py`. 비교 옵션은 스크립트 도움말을 따른다.
6. 실제 SDL: 기존 charge_smoke와 공격/표시 변경 시나리오. 출력은 사용자 tmp 외 세션 임시 폴더에 둔다.

수용 기준은 [spec.md](spec.md), 실제 결과는 [verification.md](verification.md)에 기록한다.
