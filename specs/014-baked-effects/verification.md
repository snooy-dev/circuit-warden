# Verification: PNG 효과 재생

2026-11-15. 전하 증분 완료, 전류·최종 성능 검증 진행 중.

## US1 / FR-001·002·004

- `.local-tools/python/Scripts/python.exe -X utf8 -B scripts/bake-effects/charge.py`: 33×72 PNG, crop68×70, RGBA43.14MiB 생성. 중간 단계 contact PNG를 열어 색·광륜 확인.
- `.venv/Scripts/python.exe -B -m unittest tests.unit.test_charge_teleport tests.integration.test_charge_scene -q`: 14개 통과. 안정 상태144프레임의 crop 픽셀이 원본과 같고 상태·속도 반전, 업로드 부재, 공유 해제, 부분 로딩 실패를 검사했다.
- `.venv/Scripts/python.exe -X utf8 -B tests/performance/charge_benchmark.py --repeats 1`: 예비180프레임 p95 전10.775/후12.000ms, 로딩57.9/245.5ms, 업로드847/72회. 전류는 아직 CPU이며 전체 성능 개선을 주장하지 않는다.
- `.venv/Scripts/python.exe -X utf8 -B tests/smoke/charge_smoke.py --output-dir <세션>/baked-014-charge`: 실제 SDL10순간이동·2선입력·방향·F6/F11·종료 통과, draw중앙값0.1/최대8.6ms. 사람 손 조작 검사 아님.
- docs/architecture.md·tooling.md를 현재 전하 구현에 맞췄다. 게임 NumPy 의존성을 제거했다. 기존 .venv의 설치 패키지는 과거 기준 벤치마크 실행용으로 남겨 두며 새 설치에는 필요 없다.

## 남은 검사

전류 PNG 통합·회전·전후 반복 성능·원본 대조·문서 최종 대응. 사용자 점프 PNG8개와 tmp 보존. PR/push 미실시.
