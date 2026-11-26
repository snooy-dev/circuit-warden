# Verification: 발판 이탈 직후 점프

**Date** 2026-11-26

## 자동 검사

```powershell
.\.venv\Scripts\python.exe -m unittest tests.integration.test_jump_animation.JumpAnimationTests -v
```

- 새 검사 3개를 포함해 12개 중 11개가 통과했다. 훈련장 지형과 SDL 소프트웨어 렌더러에서 좌우 이탈 79ms 후 상승, 80ms 만료, 한 번 소비, Space 탭 높이와 착지 선입력, 대시·적 밀침·순간이동 뒤 입력을 확인했다.
- 기존 `test_real_assets_and_start_air_land_locks`는 공중 공격 클립 재생 시간 기댓값 0.2초와 실측 0.14초가 달라 실패했다. `git show e7f5388:game/character.py`로 읽은 변경 전 코드를 메모리에 로드해 같은 검사를 단독 실행했을 때도 같은 줄에서 실패했다.
- 실제 게임 창과 전체 회귀는 실행하지 않았다. 80ms의 체감은 사용자 플레이 확인을 기다린다.

## 문서 영향

공유 조작 규칙은 [기본 게임플레이](../../docs/systems/basic-gameplay.md#발판-끝에서-점프), 판정 시점은 [기술 구조](../../docs/architecture.md#warden-점프), 적용 상태는 [진행 상태](../../docs/progress.md)에 반영했다. [명세](spec.md)의 FR-001·FR-002는 일반 이동 분기와 점프 입력 소비 분기에 대응하고 SC-001의 입력 경로를 통합 검사에서 확인했다.
