# Verification: 첫 레벨 전원 구역

검사일 2026-11-24

## 범위 및 대응

- FR-001~003은 [맵 번들](../../assets/levels/power-supply/map.json), [게임 장면](../../game/scene.py) 및 [SDL 입력 검사](../../tests/smoke/power_supply_smoke.py)에 대응한다. 월드는 3840×720이고 방열판 두 곳, 발판 10개, 금속 먼지 1마리, 환경 전하 발생 지점 16곳을 갖는다. 두 방열판의 높이는 바닥에서 192, 중간 발판을 통해 한 번에 오르는 높이는 96이다.
- FR-004는 [렌더 패스](../../game/power_supply_map.py)와 [게임 설계](../../docs/game-design.md#첫-레벨-전원-구역)에 대응한다. 방열판과 발판의 접지점은 모두 이미지 상단과 일치한다. 원경·뒷장식·구조·전경의 배치와 충돌을 대조했다.

## 생성 및 hi-bit 가공

- **원경**은 Codex 내장 ImageGen(`host_image`, 공개 모델명 `codex-image_gen`)의 1774×887 원화다. `hibit_plate.py plate --size 720x360 --colors 16 --preview-scale 3`을 실행했다. 2.464배 다수결 축소, 고립 픽셀 정리·3×3 다수결 필터를 적용했다. 크기·불투명·색 수·축소율 검사에 경고가 없었으며 SDL에서 시야와 원경 이동을 확인했다. [원본](../../art/levels/power-supply/background-source/generated.png) · [프롬프트](../../art/levels/power-supply/background-prompt.txt) · [변환 기록](../../art/levels/power-supply/hibit-background/plate.json)
- **구조와 부품**은 같은 생성 경로의 1774×887 RGBA 시트를 썼다. 여섯 부품을 잘라 24색 기준 팔레트와 약 2.4배 다수결 축소를 적용했다. 접지용 투명 여백을 정리하고 밝기와 출력 단자 변형을 가공했다. 가공 스크립트가 구조 텍스처 4장의 알파 255를 단언하고, SDL 캡처에서 금속 테두리와 발 위치를 확인했다. [원본](../../art/levels/power-supply/kit-source/generated.png) · [프롬프트](../../art/levels/power-supply/kit-prompt.txt) · [팔레트](../../art/levels/power-supply/palette.json) · [가공 스크립트](../../art/levels/power-supply/prepare-art.py)
- 원본 두 장은 `cli_media.py adopt`로 보관하고 SHA-256을 기록했다. 이 경로에 API 청구는 없고 보관 도구의 추산은 장당 USD 0.00이다. [원경 생성 기록](../../art/levels/power-supply/background-source/job.json) · [부품 생성 기록](../../art/levels/power-supply/kit-source/job.json)

## 실행 결과

| 검사 | 실제 명령과 결과 |
|---|---|
| 번들 | `map_bundle.py validate --bundle assets/levels/power-supply/map.json` 통과. 오류 0, 경고 0. |
| 충돌과 탐색 | `map_nav.py check --bundle assets/levels/power-supply/map.json --output-dir art/levels/power-supply/nav` 통과. 시작점 2개, 목표 4개, 도달 실패 0개, 얇은 틈 0개. |
| 브라우저 | `build_scene_preview.py --bundle art/levels/power-supply/web-map/map.json --output-dir art/levels/power-supply/preview --verify --strict` 통과. 번들 사본의 세 오브젝트 층을 `sortY` 순서대로 한 층에 넣고, 번들 Playwright에서 설치된 Chrome을 지정했다. 경로 4개에서 `ok: true`, 경고 0, 실패 0. |
| Tiled | `export_tiled.py export --bundle assets/levels/power-supply/map.json --output-dir art/levels/power-supply/tiled-final` 통과. TMJ/TSX를 다시 읽어 렌더링한 결과 차이 0픽셀. |
| Pico2D 실제 창 | `.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/sdl` 통과. 시작점·적 접근과 전하 후보 48개의 배치, 방열판 두 곳 및 첫 방열판 역방향 착지, 상부 발판, 좌클릭 순간이동, 출력 단자 도착, R, F6 왕복을 확인했다. 입력을 SDL 이벤트로 넣었고 경로 반복 검사에서 적을 제거해 지형 통과와 분리했다. |
| 기존 장면 | `.venv\Scripts\python.exe -m unittest tests.integration.test_character_scene tests.integration.test_resize_input tests.integration.test_basic_enemy tests.integration.test_charge_scene` 43개 통과. `main.py --help`에서 훈련장 옵션을 확인했다. |

[SDL 흡기구](../../art/levels/power-supply/sdl/character-power-supply-intake.png) · [SDL 순간이동](../../art/levels/power-supply/sdl/character-power-supply-discharge.png) · [SDL 출력 단자](../../art/levels/power-supply/sdl/character-power-supply-output.png) · [HTML 미리보기](../../art/levels/power-supply/preview/preview.html) · [브라우저 경로 결과](../../art/levels/power-supply/preview/scene-snapshot.json) · [충돌 지도](../../art/levels/power-supply/nav/nav-debug.png) · [Tiled 맵](../../art/levels/power-supply/tiled-final/map.tmj)

브라우저 검사는 평면 이동으로 도달 조건을 검사하고, 점프는 SDL에서 검사했다. Tiled GUI, 전체 회귀, 사용자 직접 플레이는 미실행이다. 이 레벨에서 출력부 도달로 구간을 마치며, 보스·패링·회복/저장·후속 구역 전환은 범위 밖이다.
