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

## 먼지와 흡기 팬 후속 검증

2026-11-24 사용자 요청과 시안 피드백에 따른 FR-005 증분이다. 바닥·발판 끝에 높이 15~34px인 회색 보풀 4종을 49곳에 배치했다. 충돌·시작점·전하·도착 데이터를 이전 커밋과 비교해 일치하고 먼지 49곳이 비충돌임을 확인했다. 착지면의 금속 테두리와 출력 단자 표시등은 SDL 캡처로 대조했다.

- 원경 편집과 회전자, 먼지 시트를 내장 ImageGen(`host_image`, `codex-image_gen`)으로 생성했다. 원경은 1774×887에서 720×360/20색으로, 회전자는 190×190/10색으로 변환했다. 먼지는 14색 다수결 축소와 이진 알파를 적용했다. 가공 스크립트에서 회전자 유효 반경 93px 이내와 중심 알파를 검사했다. 세 원본의 보관 도구 추산은 장당 USD 0.00이다. [원경 생성 기록](../../art/levels/power-supply/dust-revision/background-source/job.json) · [회전자 생성 기록](../../art/levels/power-supply/dust-revision/rotor-source/job.json) · [최종 먼지 생성 기록](../../art/levels/power-supply/dust-revision/dust-bunny-source/job.json) · [프롬프트와 가공 스크립트](../../art/levels/power-supply/dust-revision/)
- 줄기가 길어 풀처럼 보인 작업 중 솜털 시안의 추출 경고는 `edge_fringe`, value `0.0941`, threshold `0.02`였다. 파일은 `sparse/prop.png`, `fan/prop.png`, `ridge/prop.png`, `tall/prop.png`였다. 솜털 시안 전체를 낮은 회색 보풀로 교체했다. 새 원화에 `extract_prop_pack.py --threshold 110 --edge-threshold 172 --despill-radius 3`을 적용해 4종이 통과했고 경고는 0개였다. [시안 추출 기록](../../art/levels/power-supply/dust-revision/lint-pack/prop-pack.json) · [최종 추출 기록](../../art/levels/power-supply/dust-revision/dust-bunny-pack/prop-pack.json)
- `.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/dust-revision/sdl-final` 통과. 흡기구 정지 시점 두 장에서 팬 영역 143,740픽셀이 바뀌고 고정 원경 비교 영역의 픽셀은 모두 일치했다. 방열판 통과와 역방향 착지, 상부 발판, 순간이동, 출력 단자, R과 F6도 확인했다. [팬 실제 재생](../../art/levels/power-supply/dust-revision/fan-in-game.gif) · [전력 변환부](../../art/levels/power-supply/dust-revision/sdl-final/character-power-supply-gallery.png) · [출력 단자](../../art/levels/power-supply/dust-revision/sdl-final/character-power-supply-output.png)
- `map_bundle.py validate`, `map_nav.py check`, `build_scene_preview.py --verify --strict`, `export_tiled.py export`를 위 명령과 같은 도구로 최신 번들에 실행했다. 브라우저 경로 4개 통과, 경고 0개, Tiled 재렌더 차이 0픽셀이다. 브라우저와 Tiled의 원경은 팬 한 자세를 합성한 정적 이미지다. [번들](../../assets/levels/power-supply/map.json) · [브라우저 기록](../../art/levels/power-supply/dust-revision/preview-final/preview-qa.json) · [Tiled 기록](../../art/levels/power-supply/dust-revision/tiled-final/export-report.json)

전체 회귀, Tiled GUI, 사용자 직접 플레이는 미실행이다. GIF는 실제 SDL 화면 100프레임을 20fps로 담았다.

## 공통 픽셀 격자 검증

사용자 정정에 따라 1:1 고해상도 시안을 철회했다. 첫 레벨의 배경, 팬, 지형, 워든과 전하를 같은 세로 240픽셀 타깃에 합성하고 최근접 확대한다. 원경과 팬에는 먼지와 통풍망을 포함한 이전 hi-bit 에셋을 사용한다. 월드·충돌·시작점·전하·도착 데이터는 변경 전과 일치한다.

- `.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/pixel-grid/sdl-final` 통과. SDL 기본 427×240 및 F6의 341×240 타깃, 방열판과 발판 착지, 실제 좌클릭 순간이동, 도착·재시작을 확인했다. 추가 SDL 입력 검사에서 F11 왕복, 매 프레임 창 타깃 복원과 종료 시 텍스처 해제를 확인했다.
- 기본 창 캡처 네 장에서 세 행씩 픽셀이 동일하고 427열 최근접 확대 경계 안에서는 색이 바뀌지 않는 것을 확인했다. [실제 프레임 100장의 GIF](../../art/levels/power-supply/pixel-grid/fan-in-game.gif) · [워든과 출력 단자](../../art/levels/power-supply/pixel-grid/sdl-final/character-power-supply-output.png)
- `.venv\Scripts\python.exe -m unittest tests.integration.test_character_scene tests.integration.test_resize_input`는 SDL 더미 드라이버에서 14개를 통과했다. `map_bundle.py validate` 오류와 경고는 0개였고 `export_tiled.py export`의 픽셀 차이도 0개였다. 맵 탐색의 충돌 입력은 이전 검사와 같고 독립적인 탐색 재검사는 생략했다.

전체 회귀와 사용자 직접 미술 평가는 미실행이다. 창 크기에 따라 물리 출력 픽셀 배율은 달라진다.

## 2픽셀과 3픽셀 비교

기본 1280×720 SDL 창에서 427×240(약 3픽셀)과 640×360(2픽셀)을 같은 카메라 및 같은 팬 각도 두 곳에서 캡처했다. 두 해상도 모두 캡처 배열에서 최근접 확대 경계를 확인했다. 2픽셀 시안에서 워든의 얼굴·팔 윤곽과 발판 모서리가 더 잘 구분되고, 3픽셀 시안은 팬과 바닥의 픽셀 덩어리가 더 굵게 보인다. [나란히 비교](../../art/levels/power-supply/pixel-grid-comparison/3px-vs-2px.png)

`.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/pixel-grid-comparison/sdl`로 기본 640×360과 F6 512×360 타깃, 발판 착지·순간이동·도착·재시작을 확인했다. 전체화면 왕복과 전체 회귀는 이번 비교에서 재실행하지 않았다.

2026-11-24 사용자가 2픽셀을 확정했다. 실행 코드와 에셋 변경 없이 결정만 기록해 기존 SDL 검사 결과를 재사용했다.

## 전원선 등장 검증

FR-007을 첫 로드와 R에 적용했다. 기존 발 위치 (288, 540)에 워든을 배치하고 전원선의 접점 (241, 498)에서 소모 효과를 재생한 뒤 약 100ms부터 워든 중심까지 전류를 연결한다. 340ms에 완전히 드러나고 조작 입력은 즉시 처리한다. 배치의 좌표는 맵 좌상단 기준이다. [실제 SDL GIF](../../art/levels/power-supply/power-entry/power-entry.gif)

- 내장 ImageGen(`host_image`, `codex-image_gen`)으로 전원선 원화를 만들고 기존 환경 24색과 이진 알파로 114×21에 가공한 뒤 2배 최근접 확대해 배치했다. 도입에 기존 전하·전류 에셋을 사용했다. [원본과 생성 기록](../../art/levels/power-supply/power-entry/source/job.json) · [프롬프트](../../art/levels/power-supply/power-entry/prompt.txt) · [가공 스크립트](../../art/levels/power-supply/power-entry/prepare.py)
- `.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/power-entry/sdl`에서 처음 숨김, 정확한 전류 양 끝, 드러나기, R 재생, 조기 방향키 이동을 확인했다. 기존 발판 착지·순간이동·출력 도착·F6도 통과했다.
- SDL 더미 드라이버로 `.venv\Scripts\python.exe -m unittest tests.integration.test_character_scene tests.integration.test_charge_scene` 34개 통과. `map_bundle.py validate`, `map_nav.py check`, `build_scene_preview.py --verify --strict`의 경고·실패는 0개이며 브라우저 경로 4개가 통과했다. `export_tiled.py export` 재렌더 차이는 0픽셀이었다. 브라우저는 정적 배치를 확인하고 등장 연출은 SDL에서 확인했다.

전체 회귀와 사용자 직접 플레이는 미실행이다.

## 바닥 전력 접점 검증

2026-11-24 사용자 정정에 따라 FR-007의 연출 시작점을 바닥 회로판에 매립된 내부 전력 접점으로 바꿨다. 접점 표면과 워든 발 위치는 맵 좌표 (288, 540)으로 같다. 전류가 그곳에서 워든 중심까지 수직으로 연결된다. 기존 등장 시간과 충돌, 전하·적 배치는 유지했다.

- ImageGen으로 회로판 내장 접점을 제작하고 기존 환경 팔레트와 2픽셀 격자에 맞춰 68×14 PNG를 만들었다. 접점 중앙의 첫 불투명 행을 바닥선에 맞췄다. [생성 기록](../../art/levels/power-supply/deck-contact/source/job.json) · [가공 스크립트](../../art/levels/power-supply/deck-contact/prepare.py)
- `.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/deck-contact/sdl`에서 워든의 발 위치와 접점 일치, 전류의 양 끝, R과 조기 이동을 확인했다. 기존 경로와 F6도 통과했다. [실제 SDL GIF](../../art/levels/power-supply/deck-contact/deck-entry.gif)
- `map_bundle.py validate`, `map_nav.py check`, `build_scene_preview.py --verify --strict`의 경고·실패는 0개이고 브라우저 경로 4개가 통과했다. `export_tiled.py export` 재렌더 차이는 0픽셀이었다. 전체 회귀와 사용자 직접 플레이는 미실행이다.

## 벽면 전원 인렛 검증

2026-11-24 사용자가 외부 AC 전력을 받는 부품에서 등장하기를 원한다고 명확히 했다. IEC C14 인렛의 나사 고정판과 안쪽 금속 단자를 참고해 왼쪽 벽에 배치했다. 전류 시작점은 (147, 468), 워든의 발은 (224, 540)이다. 기존 등장 시간, 충돌과 전하 배치를 유지했다. [부품 자료](https://www.schurter.com/en/datasheet/6100-3) · [실제 SDL GIF](../../art/levels/power-supply/chassis-inlet/chassis-entry.gif)

- ImageGen 원화를 기존 환경 팔레트로 가공한 128×112 에셋을 썼다. 고정판이 왼쪽 벽과 겹치는 모습과 전류가 구리 단자에 닿는 모습을 실제 캡처로 확인했다. [생성 기록](../../art/levels/power-supply/chassis-inlet/source/job.json) · [가공 스크립트](../../art/levels/power-supply/chassis-inlet/prepare.py)
- `.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/chassis-inlet/sdl`에서 새 스폰, 전류의 양 끝, R·조기 이동과 기존 경로를 확인했다.
- `map_bundle.py validate`, `map_nav.py check`, `build_scene_preview.py --verify --strict` 통과. 브라우저 경로 4개에서 실패 및 경고는 0개이고 `export_tiled.py export` 재렌더 차이는 0픽셀이었다. 전체 회귀와 사용자 직접 플레이는 미실행이다.

## 전원 인렛 외형과 돌출 보정

사용자 피드백에 따라 제품 사진과 치수도에서 검은 삽입구의 깎인 모서리, 삼각형으로 배치된 세 핀, 양쪽 나사 자리를 반영했다. 원화를 86×40으로 가공해 벽 오른쪽으로 보이는 배치 폭을 120px에서 64px로 줄였다. 전류는 오른쪽 짧은 구리 접점 (93, 486)에서 시작하고 워든은 (172, 540)에 선다. [제조사 사진과 도면](https://www.schurter.com/en/part/6100.3100) · [생성 기록](../../art/levels/power-supply/recognizable-inlet/source/job.json) · [실제 SDL GIF](../../art/levels/power-supply/recognizable-inlet/chassis-entry.gif)

`.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/recognizable-inlet/sdl`에서 전류의 양 끝, 새 스폰, R·조기 이동과 기존 경로를 확인했다. 맵 번들·탐색·브라우저 경로 4개와 Tiled 재렌더를 통과했고, 경고 0개와 재렌더 차이 0픽셀을 확인했다. 전체 회귀와 사용자 직접 플레이는 미실행이다.

## 상단 케이블 낙뢰 등장 검증

2026-11-24 사용자 후속 지시에 따라 벽면 인렛을 제거하고 기존 상단 케이블의 구리 부분 (142, 82)에서 전류가 떨어지도록 변경했다. 워든의 발 위치 (172, 540), 340ms 등장 시간, 2×2 화면 픽셀, 충돌·지형·전하 배치를 유지했다. [실제 SDL 캡처](../../art/levels/power-supply/ceiling-entry/ceiling-entry.gif)

- `.venv\Scripts\python.exe art/levels/power-supply/ceiling-entry/entry_review.py current`에서 초기 착지, 전류의 양 끝, 등장 완료, R 재시작과 조기 이동을 통과했다. `tmp/power-entry/capture.py`로 실제 화면 27장을 캡처했고 케이블에서 워든까지 이어지는 방전을 확인했다.
- `map_bundle.py validate`는 오류·경고 0개, `map_nav.py check`는 목표 4개 중 도달 불가 0개, `export_tiled.py export`는 재렌더 차이 0픽셀이다.
- `.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir art/levels/power-supply/ceiling-entry/sdl`은 등장 확인 뒤 주행 단계에서 시간 초과했다. 변경 전 `ec617f4` 맵에서도 같은 주행 단계의 시간 초과를 재현해 전체 레벨 SDL 완주는 확인하지 못했다. 사용자 직접 플레이는 미실행이다.

## 낙뢰 타격과 등장 강화 검증

사용자 요청에 따라 상단 케이블의 선행 방전, 굵게 갈라지는 본줄기, 착지점 섬광과 바닥 불꽃을 등장 전용 pixelfx 시트로 적용했다. 논리 한 칸은 기본 창에서 2×2 화면 픽셀이다. 타격은 80ms에 시작하고 워든은 타격부터 드러나며 340ms에 등장 연출을 마친다. [실제 SDL 캡처](../../art/levels/power-supply/lightning-strike/lightning-strike.gif)

- `node scripts/bake-effects/power-entry.mjs`에서 맵의 케이블·착지 좌표, 타격 프레임의 두 접점, 이미지 여백 및 마지막 프레임의 투명성을 확인했다.
- `.venv\Scripts\python.exe art/levels/power-supply/lightning-strike/smoke.py art/levels/power-supply/lightning-strike/final-frames`로 첫 타격·등장 완료, 효과 정리, R 재시작과 조기 이동을 실제 SDL에서 확인했다.
- `.venv\Scripts\python.exe -m unittest tests.unit.test_teleport_link` 4개 통과. 전체 레벨 주행과 사용자 직접 플레이는 미실행이다.

## 노출 구리 심선 검증

ImageGen 편집본에서 손상 구간만 선택해 기존 케이블에 합성하고 환경 팔레트와 2×2 픽셀에 맞췄다. 맵의 첫 케이블만 교체하고 낙뢰의 시작점을 심선 끝 (142, 92)에 맞췄다. [실제 게임의 접점 확대](../../art/levels/power-supply/exposed-cable/contact.png) · [등장 GIF](../../art/levels/power-supply/exposed-cable/exposed-cable.gif)

- `map_bundle.py validate --bundle assets/levels/power-supply/map.json` 오류·경고 0개. 이전 맵과 대조해 첫 케이블과 전류 시작점만 바뀌었고 시작점은 구리색 불투명 픽셀에 닿는다.
- `node scripts/bake-effects/power-entry.mjs`에서 케이블과 착지 접점, 여백, 종료 프레임을 확인했다. `.venv\Scripts\python.exe art/levels/power-supply/lightning-strike/smoke.py art/levels/power-supply/exposed-cable/frames`로 실제 SDL에서 심선 방전, 워든 등장, R 재시작과 조기 이동을 확인했다. 전체 레벨 주행은 미실행이다.

## 낙뢰 카메라 흔들림 검증

낙뢰 타격부터 100ms 동안 논리 픽셀 단위로 카메라를 흔들고 진폭을 줄인다. 기본 창에서는 상하 최대 6px, 좌우 최대 4px 이동한다. [실제 SDL 캡처](../../art/levels/power-supply/entry-camera-shake/entry-camera-shake.gif)

- `.venv\Scripts\python.exe art/levels/power-supply/entry-camera-shake/smoke.py art/levels/power-supply/entry-camera-shake/frames`로 실제 SDL에서 12.5ms 간격으로 진행하며 타격 전과 직후의 카메라 위치, 그리기 직후 입력 좌표 복원, R 재시작과 조기 이동 중단을 확인했다.
- 실제 화면 5장에서 케이스 벽의 같은 영역을 픽셀 단위로 대조해 예상 변위와 최종 원위치를 확인했다. 전체 레벨 주행과 사용자 직접 플레이는 미실행이다.

## 레벨 동선 재설계

2026-11-24 FR-008~FR-010을 확인했다. 변경 전에는 네 발판의 하부가 72px로 워든 키 83px보다 낮았다. 실제 충돌 계산에서 32px 중앙 틈에 폭 48px인 몸통이 양쪽으로 8px씩 걸렸다. 대기·달리기 프레임의 발 기준점과 불투명 발끝은 0~1px 차이였다.

- **배치 검사** `map_bundle.py validate --bundle assets/levels/power-supply/map.json`은 오류·경고 0개, `map_nav.py check --bundle assets/levels/power-supply/map.json --output-dir .local-tools/level-redesign-nav`는 목표 4곳 도달과 얇은 틈 0개를 보고했다. 텍스처 알파 경계를 대조해 발판 9개와 방열판 2개의 그림·충돌 경계가 일치하는 것을 확인했다. 하부 최소 높이는 110px, 상부 중앙 틈은 80px다.
- **실제 SDL 입력** `.venv\Scripts\python.exe -m tests.smoke.power_supply_smoke --output-dir .local-tools/level-redesign-sdl` 통과. 입구 발판 아래로 양방향 주행, 연습 발판 착지, 두 방열판 왕복, 변환부 하부 주행, 중앙 발판 양방향 점프와 틈에서 바닥까지 낙하, 상부 전하 좌클릭 순간이동, 경로 합류, 출력 점등, R·F6을 확인했다. 전하 후보 48곳의 배치도 검사했다. 적의 접근을 확인한 뒤 지형 반복 검사에서는 적을 제거했다. SDL 캡처에서 방열판 착지, 중앙 틈 낙하, 출력 점등을 관찰했다.
- **훈련장** `test_jump_onto_training_platform_and_walk_off`, `test_camera_freezes_at_low_wall_inside_world_bounds`, `test_lands_on_platform_and_stops_rise_at_ceiling`을 `unittest`로 실행해 3개가 통과했다. 하부 최소 높이는 104px이며 기존 훈련장 검사에 발판 하부를 달리는 입력을 추가했다.
- 점프를 재현하는 SDL을 경로 검증에 사용했다. 이전 브라우저·Tiled 산출물은 재생성하지 않았다. 이번 범위의 전체 회귀와 사용자 직접 플레이는 미실행이다.
