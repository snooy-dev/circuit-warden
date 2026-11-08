# 기술 구조

상태: **게임 기술 설계 전**

## 현재 환경

- Python 기반 프로젝트. 기존 게임 가상환경은 .venv/다.
- requirements.txt에는 pico2d==1.5.1이 지정되어 있다.
- 게임 코드 구조·실행 진입점·루프·장면 관리·테스트 구조는 아직 설계하거나 구현하지 않았다.

## 도구와 게임의 분리

Spec Kit과 아트 후처리 패키지는 .local-tools/python/에서 실행한다. 게임 실행·테스트에는 .venv/Scripts/python.exe를 명시한다. 상세 경로와 버전은 [tooling](tooling.md)을 참조한다.

기술 계획이 승인되면 구조와 중요한 선택 이유를 여기에 남기고 개별 구현 단계는 specs의 plan.md에서 관리한다.
