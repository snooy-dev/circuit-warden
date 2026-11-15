# Verification: PNG 효과 재생

2026-11-15. 요청 구현·검증 완료. 사용자 미세 형태 차이 허용은 [명세](spec.md), 작업 대응은 [tasks.md](tasks.md).

## FR-001·002·004 / 전하

- `.local-tools/python/Scripts/python.exe -X utf8 -B scripts/bake-effects/charge.py`: 승인 PNG에서33×72프레임 생성.68×70 투명 여백 crop, RGBA43.14MiB. game/charge.py의 NumPy·합성·개별 streaming texture를 제거하고 ImageStore/SpriteFrame으로 공유한다.
- 전하 상태·속도·24fps 위상은 유지하며 표시만 가장 가까운1/32단계, bob은 각 위상 중간 시각으로 선택한다. bob은 연속 시각의 이전 결과와 최대1px 차이 날 수 있다.
- `.local-tools/python/Scripts/python.exe -X utf8 -B scripts/bake-effects/check.py --output-dir <세션>/baked-014`: 원본154프레임·기존 합성1,944샘플 SHA 일치, 구운2,376프레임 PNG 복원 SHA 일치.648전환 샘플을 배경RGB(200,200,210)에 합성한 유효 픽셀(양쪽 중 alpha>4)의 채널 오차는 평균0.743/p99 4.337/최대21.000(255척도). 이는 지정 샘플의 색 오차이지 전체 시간·화면의 보증이 아니다. 비교 이미지를 직접 열어 파동·색·광륜을 확인했다.
- 안정 상태144프레임의 원본 crop RGBA는 동일하다. crop 후 확대·정수 좌표 샘플링까지 화면 픽셀 일치를 주장하지 않는다. 베기·대시·캐릭터 PNG는 변경하지 않았다.

## FR-003·004 / 전류·공통 그리기

- `node scripts/bake-effects/link.mjs`: 승인 link.js를 직접 호출해 seed7·누적1/30초의12샘플을72길이로 생성. 1~32px 정수,36~64px 간격4,72~320px 간격8. PNG의 color+light를 투명 RGBA로 합성하므로 광륜을 보존한다.
- 런타임은 가까운 길이를 선택하고 중앙 회전·가로 배율만 적용한다. 8px 미만은 광륜 폭 변화 방지를 위해 배율1, 이론상 끝점 오차≤0.25px. 임의 방향의 가지 모양·회전 픽셀과 길이 샘플 선택 차이는 사용자 허용 범위다.
- 첫 프레임·100ms 수명·선입력 규칙 유지. zero/1px미만 비표시, 역방향·11개 이상 길이/방향의 끝점3×3 주변 섬광, 1.49/1.5/5.99/6/7.99/8px 경계, 공유 해제, PNG 필터 실패 정리를 검사했다.
- 두 효과에 최근접 필터 명시. 회전 native 실패 후 alpha/blend 복원, 회전 source/flip/투명도와 비유한 각도 거부 검사 통과.
- 원본48px 첫 프레임·320px 마지막 샘플의 복원 RGBA SHA 일치. 이전 임의 방향 CPU 해시를 새 회전 결과의 동일성 기준으로 오용하지 않는다.
- 두 생성기를 다시 실행해107파일(PNG105+manifest2)의 SHA 전체 동일. PNG 합계13.095MiB, 비압축 이미지 합계59.74MiB(전하43.14+전류16.60). 프로세스/GPU 최대 메모리를 측정한 값은 아니다.

## FR-005 / 성능

`.venv/Scripts/python.exe -X utf8 -B tests/performance/charge_benchmark.py`

기준 `eb082e5`의 NumPy 전하·CPU 전류를 Git에서 메모리에 로드한다. 게임 .venv의 기존 NumPy2.5.4는 과거 기준 비교용으로 남겼고 새 게임 requirements에는 없다. 새 환경의 벤치마크 전용 준비는 tests/README.md를 따른다. 게임 import 시 numpy가 sys.modules에 없음을 별도 확인했다.

1280×720 SDL 소프트웨어 renderer, 전하5개, 고정1/60×180프레임, 클릭14회/순간이동12회. 워밍업 후 순서를 교대해5쌍, 전후각900프레임. GC 기본 설정. p95는 실행별95백분위의 중앙값이며 최대/예산초과는900프레임 전체다.

| 항목 | 변경 전 | 변경 후 |
|---|---:|---:|
| update+draw+software present p95 | 12.630ms | 1.558ms(-87.7%) |
| 같은 구간 최대 | 20.465ms | 2.304ms |
| 16.67ms 초과 | 5/900 | 0/900 |
| 실행당 프레임 텍스처 업로드 | 847 | 0 |
| 장면 enter 시간 중앙값 | 72.2ms | 295.2ms |

이벤트 처리·클릭 시 기존 텍스처 생성·SDL_RenderClear·실제 창/GPU/VSync·프레임 대기는 타이머 밖이다. 따라서 총 프레임/FPS나 GPU 실행시간으로 해석하지 않는다. 로딩 비용 약223ms 증가와 이미지 메모리 사용을 교환한 결과다. 초기 전하만 교체한 예비 실행은 최종 성능 근거로 쓰지 않는다.

## 통합·실제 창

- 전하 증분 표적14개, 회전·전류·장면 표적19개 통과. 공통 그리기 변경과 게임 통합 영향 때문에 최종 `.venv/Scripts/python.exe -B -m unittest discover -s tests -q`를 한 번 선택: **163개 통과**.
- `.venv/Scripts/python.exe -X utf8 -B tests/smoke/charge_smoke.py --output-dir <세션>/baked-014`: 실제 SDL10순간이동·2선입력·상태 취소·가로/세로/대각·F6/F11·Esc·자원 해제 통과. 최종 draw 중앙값0.1/최대0.3ms. 별도 draw-only 구간이므로 위 전체 처리 구간과 직접 비교하지 않는다.
- 세션 경로: `C:/Users/Developer/.codex/visualizations/2026/11/15/01a1dde8-74e5-7132-8171-12f342fb4cc4/baked-014`. 첫 연결·가로·세로 캡처와 charge-before-after.png를 직접 열어 확인했다. 사람의 직접 조작감 검사가 아니다.

## Documentation / Git / 한계

- architecture·art-direction·tooling·tests/README·자산 메타데이터를 현재 PNG 재생과 허용 차이에 맞췄다. 게임 규칙·원본 자산·루트 README는 변경하지 않았다. progress·명세·계획·작업·근거 대응을 확인했다. 최종 converge에서 FR5개·SC4개·수용 시나리오4개·작업12개의 필수 누락을 찾지 못했고 추가 작업은 없다.
- feature/baked-effects에서 전하 증분1862b4e를 먼저 커밋했다. fetch 성공 후 origin/main의 추가 변경 없음 확인. 사용자 점프 PNG8개 해시 보존, 기존 tmp는 삭제하지 않았고 커밋에 포함하지 않는다.
- 읽기 전용 리뷰의 짧은 광륜 폭·필터·벤치마크 환경/측정 범위 지적을 반영했다. 더 촘촘한 짧은 길이와 필터 설정 후 전체 검사·최종 벤치마크·실제 창을 실행했다.
- 다른 CPU/GPU·저메모리 장비·동시 대량 효과·320px 초과·장시간 메모리 최대값·사용자 직접 미술/조작감은 미검사. PR/push 미실시. PNG 재생은 사용자 허용 미세 차이를 포함하며 모든 픽셀 동일성을 보장하지 않는다.
