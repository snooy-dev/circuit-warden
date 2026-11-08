# 실행·검증 안내

프로젝트 루트 PowerShell, 기존 .venv와 requirements.txt 환경을 사용한다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

실제 창에서 움직이는 도형·마우스 표시를 확인한다. Space를 눌러 두 장면을 왕복하고 Escape로 종료한다. 다시 실행해 창 닫기로 종료한다. 입력·시간 기본값은 [architecture](../../docs/architecture.md)를 참조한다. 결과와 미실행은 verification.md에 구분한다.
