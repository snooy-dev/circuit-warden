# Quickstart

프로젝트 루트 PowerShell, 기존 게임 .venv 사용.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_charge_teleport tests.unit.test_teleport_link tests.integration.test_charge_scene
.\.venv\Scripts\python.exe tests/smoke/charge_smoke.py --output-dir <프로젝트 밖 기존 폴더>
.\.venv\Scripts\python.exe main.py
```

A/D로 전하 접근/이탈 → 활성 전하 왼쪽 클릭 → 공중 낙하/착지. 공격/점프/대시 중에도 전하 클릭으로 즉시 이동한다. 먼 전하/빈 곳은 기존 공격이다. 같은 전하 재클릭·여러 전하 연결·F6/F11 후 클릭을 확인한다. 상태 반전이 튀지 않고 전류가 출발/도착을 연결한 뒤 사라져야 한다. 거리/배치/공중 공격 제외가 적절한지는 사용자 플레이로 판단한다.

전류는100ms 시험값으로 짧게 표시된다. 진행 중 다음 활성 전하를 미리 클릭하면 현재 순간이동이 끝난 뒤 이어진다. 여러 번 누르면 마지막 유효 전하1개만 남고 포커스를 잃으면 예약을 취소한다. 활성 범위는 순간이동 목표 지점에서 즉시 다시 계산한다.
