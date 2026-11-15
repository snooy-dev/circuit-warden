# Quickstart

1. 도구 환경: `.local-tools/python/Scripts/python.exe scripts/bake-effects/charge.py`, `node scripts/bake-effects/link.mjs`.
2. 게임 환경: `.venv/Scripts/python.exe -B -m unittest tests.unit.test_charge_teleport tests.unit.test_teleport_link tests.integration.test_charge_scene`.
3. 과거 구현 성능 비교에는 선택적으로 numpy==2.5.4가 필요하다([검사 안내](../../tests/README.md)). 성능·실제 창 명령과 결과는 [verification.md](verification.md)에 기록한다.
