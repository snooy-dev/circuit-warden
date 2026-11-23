# Verification: 전하 이동과 피격 피드백

## 전류와 도착

이전 공중 도착은 60Hz 한 프레임 약 8 월드 단위, 첫 100ms에 약 39.4 월드 단위 상승하는 동안 고정된 전류를 표시했다. 첫 렌더를 전류 도착 좌표와 공유하고 표시만 짧게 보간했다. 방향별 전류·위상·연속 이동·지상 복귀 및 공중 연계 표적 12개를 통과했다.

## 최종 표적 검사

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_basic_enemy tests.unit.test_charge_teleport tests.unit.test_teleport_link tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_basic_enemy.BasicEnemySceneTests tests.integration.test_jump_animation tests.integration.test_dash_animation tests.integration.test_resize_input
```

74개 통과. 움직이기 전의 첫 전류·도착 프레임, 지상 도착 자세와 복귀, 연속 이동, 공중 타격 연결, 상단 반동, 공중·지상 돌진 피격, 벽과 보호 시간, 대시·점프·창 입력을 확인했다. 착지 시간 검사를 적 몸통 위쪽의 새 반동과 분리했다.

`tests/performance/charge_benchmark.py --repeats 1`은 이전 비교 대상에서 경과 시간을 제공하도록 보완한 뒤 통과했다. 양쪽 이동 12회, PNG 경로의 실행 중 업로드 0회를 확인했다.

## 실제 SDL 창

- `tests/smoke/charge_smoke.py --output-dir $testOut` 통과. 수평에 가까운 이동과 대각선 및 예약 이동의 첫 섬광, 생성·소모, 기존 공중 타격 후 이탈을 확인했다. 순간이동 9회, 예약 2회였다. 첫 장면에서 고정 전류가 워든 몸에 이어지는 것을 캡처로 확인했다.
- `-m tests.smoke.basic_enemy_smoke --output-dir $testOut` 통과. 실제 돌진 회피 이후 지상 피격, 적 상단에서 무피해 반동, 공중 옆면 돌진 피격을 상황별로 재현했다. 적 상단·공중 피격 검사에는 시작 위치와 적 상태를 지정했다. 최초 지상 피격 검사는 점프 뒤의 상단 반동을 포함해 공중에서 맞았다. 지상 피격 시작 위치를 명시한 뒤 별도 캡처에서 피격 자세를 확인했다. 사망·R·좌우 검 공격·F6도 통과했다.

## 에셋 검증

기존 idle 프레임을 참조해 내장 ImageGen으로 피격 키 자세를 제작했다. 참조의 16색과 이진 알파로 128×104 셀에 등록했고 알파 범위는 `(30,12)–(104,92)`, 기준점은 `(64,92)`다. generate2dsprite의 `assemble_frames.py --strict`는 PNG/atlas RGBA 일치와 120ms 출력을 통과했고 단일 셀의 침범·반복 검사는 건너뛰었다. 검수용 미리보기와 실제 SDL의 지상·공중 캡처에서 몸체 비례, 방향, 발 기준 및 잘림을 관찰했다. [원본·프롬프트·해시](../../assets/warden/source/hurt.provenance.json).

## 대응 및 남은 확인

FR-001·002는 전류 좌표와 도착 프레임·기존 공중 연계, FR-003은 상단·옆면과 지상·공중 피격 결과에 대응한다. 관련 문서와 산출물 경로를 확인했다. 45ms 표시 전환과 120ms 피격은 기술 시험값이다. 전체 회귀와 사용자 직접 조작감은 확인 범위 밖이었다.
