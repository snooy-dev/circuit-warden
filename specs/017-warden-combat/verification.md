# Verification: 워든 전투와 일회성 전하

## 전투 규칙

- 기본 전투 증분은 표적 24개를 통과했다. 최종 증분에선 전하 선택·소비·R, 예약 대상이 적 몸통에 막혔을 때 보존, 보호 시간 경계, 공중 명중·즉시 이탈, 효과 및 텍스처 수명까지 확인했다.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.integration.test_charge_scene.ChargeSceneTests tests.integration.test_basic_enemy.BasicEnemySceneTests tests.unit.test_basic_enemy tests.unit.test_teleport_link.TeleportLinkTests.test_rotated_endpoints_and_playback_without_upload_or_loading tests.unit.test_teleport_link.TeleportLinkTests.test_fresh_frame_lifetime_and_shared_image_ownership tests.unit.test_charge_teleport.ChargeTeleportTests.test_distance_boundary_and_transition_reversal_partition
```

- 최종 48개 통과. `tests/performance/charge_benchmark.py --repeats 1`의 과거 비교 부하를 별도로 검증했다. 양쪽 12회 이동, PNG 실행 중 업로드 0회였다.
- 명세 FR-001–004·SC-001–003의 구현과 검사 및 game-design, 전하·기본 조작·적·architecture·art-direction·progress 문서를 대조했다. 전체 회귀는 선택하지 않았다.

## 실제 SDL 창

- `.\.venv\Scripts\python.exe tests/smoke/charge_smoke.py --output-dir $testOutput` 통과. SDL 키·마우스로 달리기, 점프, 지상 검 동작, 전하 진입 후 공중 명중, 공격 취소로 이탈, 돌진 횡단 회피, R 복구, F6/F11을 실행했다. 순간이동 7회와 선입력 1회 및 정리 검사를 통과했다. 공중 타격에서 적 체력 1 감소와 체공을, 돌진 회피에서 워든 체력 유지를 확인했다.
- `.\.venv\Scripts\python.exe tests/smoke/audit_smoke.py --output-dir $testOutput` 통과. 처음 실행에서 적 몸통 충돌이 대시를 끊었다. 예약 공격 검증 구간에서 적 접촉을 분리하고 F6와 클릭의 좌표 순서, 예약 공격의 첫 프레임, 종료 후 정리를 확인했다.

## 에셋 감사

- 내장 ImageGen이 기존 활성 전하를 참조해 실제 투명 알파를 가진 1254×1254 이미지를 반환했다. 전하 수축 4프레임의 런타임 외곽은 43×42 → 25×25 → 17×16 → 7×4px다. pixelfx `impacts/hit-spark`를 7색으로 렌더링했다. 첫 후보의 상단·오른쪽 가장자리 접촉을 보고 각도·높이를 조정했다. 이후 밝은 장면에서 보인 어두운 광륜은 pixelfx 내보내기의 사전 곱 알파를 풀고 광륜 알파를 줄여 개선했다. [원본과 출처](../../assets/combat/source/provenance.json) · [ImageGen 프롬프트](../../assets/combat/source/charge-spent.prompt.txt).
- `node .local-tools/pixelfx/tools/check.mjs impacts/hit-spark`는 1 pass, 0 fail, 0 warnings였다. generate2dsprite `assemble_frames.py --strict`로 원본을 분할해 RGBA·시트·WebP 시간과 셀 경계 침범 0을 확인했다. `loop_seam`은 2.689162 및 약 3.63으로 `needs-visual-review`를 반환했다. 둘 다 재생 끝에서 소멸하는 단발 자산이다.
- generate2dsprite `sheet_qc.py spill`의 기본 최소 면적 64px는 런타임 잔불과 작은 스파크를 `empty_cells`로 표시했다. 최종 런타임 시트는 픽셀 FX 기준인 `--alpha-threshold 16 --min-area 1`에서 검사했다. 적중 시트는 유효 14셀만 검사하고 최소 여백을 0.05로 지정했다. 두 최종 시트 모두 경계 침범·시트 가장자리 접촉 0, 실패 0, 경고 0이다. `scripts/bake-effects/combat.py`의 전 셀 경계·수축 검사와 원본/런타임 해시·RGBA·팔레트·프레임 시간도 확인했다. 런타임 PNG 두 장 합계는 5,302바이트다.
- 게임 크기의 양쪽 배경 프리뷰와 실제 SDL 화면을 비교했다. 독립 화면 검토에서 소모와 적중은 초반 형태로 구분됐고 주요 피사체를 심하게 가리거나 화면 가장자리가 잘리는 장면은 관찰되지 않았다. 밝은 배경에선 후반의 가는 흰 파편 대비가 낮고 기존 활성 전하의 어두운 고리가 보인다. [에셋 프리뷰](../../assets/combat/source/preview.png).

## 미확인 범위

사람이 직접 플레이한 반응 속도·최종 밸런스와 최종 아트 채택은 미확인이다. 전하 생성 방식은 후속 범위다.
