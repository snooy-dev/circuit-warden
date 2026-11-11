# 실행·검증 안내

> 과거 구현 당시의 실행 기록이다. 초기 도형 데모 진입점은 010 후속 정리에서 제거했고 필요한 장면을 tests/fixtures로 옮겼다. 당시 코드는 Git 이력에 보존한다. 현재 실행법은 [게임 안내](../../README.md)와 [검사 안내](../../tests/README.md)를 따른다.

프로젝트 루트 PowerShell, 기존 .venv와 requirements.txt 환경을 사용한다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

실제 창에서 움직이는 도형·마우스 표시를 확인한다. Space를 눌러 두 장면을 왕복하고 Escape로 종료한다. 다시 실행해 창 닫기로 종료한다. 입력·시간 기본값은 [architecture](../../docs/architecture.md)를 참조한다. 결과와 미실행은 verification.md에 구분한다.
