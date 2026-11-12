# Quickstart

프로젝트 루트 PowerShell, 게임 .venv 사용.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

A/D 이동·상쇄·해제 → 양 방향 왼쪽 클릭 → 공격 중 이동키 변경/해제·재클릭 → 종료 복귀를 확인한다. F6/F11과 포커스 전환 후 유지 입력이 남지 않아야 한다. 우클릭은 공격하지 않는다.
선택한 자동 검사와 실제 명령·결과는 [verification](verification.md)을 따른다. 기본 창은 1280×720이며 공격은 아웃라인 있음 v6, 베기는 전기 v4다. 공격 종료 후 이동해도 이전 베기는 시작 위치에 남아 700ms에 소멸한다. 피해 판정·타이틀은 없다.

Space로 제자리 점프, A/D+Space로 달리기 점프를 확인한다. 공중 A/D 변경·해제는 즉시 반영되고 idle/Run을 재사용한다. 공중 클릭/재점프는 무시한다. 버튼을 계속 누르면 착지 후 자동으로 뛰지 않으며 Space를 놓고 다시 눌러야 한다. 점프 높이는 idle 몸체 키(귀 포함, 투명 여백 제외)의 2배다.
