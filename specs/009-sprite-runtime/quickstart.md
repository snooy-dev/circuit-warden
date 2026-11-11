# Quickstart: 스프라이트 통합 검증

현재 제품 경로는 `game_framework/sprites.py`, 검사 경로는 `tests/unit/test_sprites.py`다. 프로젝트 루트에서 실행한다.

```powershell
& 'D:/GitHub/circuit-warden/.venv/Scripts/python.exe' -B -m unittest discover -s tests -v
```

통합 검증 사본: `D:/GitHub/circuit-warden/.local-tools/work/engine-sprite-integration/engine`.
현재 실제 PNG 검사 사본은 같은 상위 폴더의 `preview/`에 있고, `preview.py --project <통합 사본 절대 경로> --smoke`로 실행한다. 생성된 PNG는 SDL 렌더러에서 읽은 화면이며 사용자 직접 키 조작을 대신하지 않는다.

## 이전 임시 화면 보존

아래 실행기와 사용자 확인·정리 조건은 그대로 보존한다. 이전 100개 결과와 현재 패키지 통합 검사는 [verification](verification.md)에서 구분한다.

## 2. 현재 미추적 임시 화면

2026-11-11 idle와 Run 원본을 읽기 전용으로 사용하는 임시 하네스를 만들었다. 원본 복사·수정은 없고 제품 assets/main에 연결하지 않았다.

임시 폴더: C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c602-4806-7d43-aaed-3468b12931a0/sprite-preview

```powershell
& 'C:/Users/Developer/.codex/visualizations/2026/11/10/01a1c602-4806-7d43-aaed-3468b12931a0/sprite-preview/launch.ps1'
```

launch.ps1은 게임 Python으로 같은 폴더의 preview.py를 실행한다. sources.json에는 로컬 원본 경로·시트 행/열·원본 SHA256, created-files.txt에는 이번 임시 생성물 목록이 있다. 이 파일들과 출력 PNG는 전부 저장소 밖이며 미추적이다. 종료해도 삭제되지 않으므로 다시 실행할 수 있다.

| 키 | 동작 |
|---|---|
| Space / N | 일시정지·재생 / 한 프레임 진행 |
| I / R | idle / Run 선택 |
| F / L / Home | 수평 반전 / 반복·단발 전환 / 처음부터 |
| + / - | 확대 배율 변경 |
| F6 / Tab | 창 크기 변경 / 장면 다시 열기 |
| Escape | 창 종료, 임시 자료 유지 |

윗줄은 월드, 아랫줄은 UI다. 각 줄은 기본 크기·2배·반대 방향 45% 투명도를 비교한다. 주황색 십자는 프레임 기준점이다. N은 다음 프레임 경계로 진행한다. 단발 완료 후에는 Home으로 재시작한다.

## 3. 검사 결과와 사용자 대기

실제 PNG 로딩/공유, 재생, 일시정지/한 프레임, 동작 전환, 수평 반전, 단발 완료, 1100×720↔900×600, 장면 재진입/해제, 원본 해시 확인의 자동 8단계가 통과했다. 이 입력은 SDL 이벤트 주입이며 사용자 물리 키 조작 검사가 아니다. 저장된 실제 SDL 출력 PNG를 열어 자르기·투명 배경·확대·기준점·두 좌표계와 출력 크기를 관찰했다.

사용자 직접 확인은 아직 받지 않았다. 창 종료·시간 경과·자동 검사 통과를 확인으로 간주하지 않는다. 문제 보고가 있으면 수정하고 다시 직접 확인할 수 있게 임시 자료를 유지한다.

## 4. 사용자 확인 후에만 정리

사용자가 확인한 범위와 결과를 기록한다. created-files.txt의 절대 경로를 재확인해 이번 하네스·설정·출력 이미지만 제거한다. 원본 시트/메타데이터·제품 코드·자동 테스트·기존 smoke 검사는 보존한다. 광범위 temp/art 폴더 삭제는 금지한다.

- git status / git ls-files로 실 시트와 임시 실행 자료가 추적되지 않았는지 확인한다.
- sources.json의 해시로 원본이 유지되는지 확인한 후 임시 설정을 정리한다.
- 임시 실행 연결이 기본 프로그램에 남지 않았는지 확인한다.
- verification/progress에 사용자 확인과 정리 결과를 각각 기록한다. 미완료 항목이 있으면 기능 전체 완료로 표시하지 않는다.
