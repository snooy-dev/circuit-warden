# Implementation Plan: 스프라이트 표시·재생과 이미지 수명

**Date**: 2026-11-11 | **Spec**: [spec.md](spec.md) | **Status**: Ready
**Branch**: feature/engine | **Base**: d7d68308 (기존 구현 출처: feature/sprite-runtime @ 1fbdfac)
**Execution state**: 기존 P1/P2 구현을 현재 패키지 구조에 통합했다. 최신 실행 결과는 verification의 Engine Package Integration을 따른다. 이전 사용자 직접 확인·임시 자료 정리는 미완료다. 아래 초기 설계의 단일 파일 경로는 마지막 Engine Integration Plan의 패키지 경로로 대체한다.

## Summary

기존 LevelScene·Renderer·WorldTransform·UITransform을 사용한다. 작은 sprites.py에 이미지 관리 참조/저장소, 불변 프레임/클립, 개체별 재생기를 둔다. GameObject와 UIElement의 기존 update/draw 연결을 사용하며 새 객체 계층이나 자동 등록 체계를 만들지 않는다.

실 시트는 런타임 자산으로 추가하지 않는다. 향후 구현 후 별도 로컬 임시 하네스에서 출력만 확인하고 사용자 확인 전까지 보존한다. [명세 FR-008~009](spec.md)를 최종 완료 조건으로 따른다.

## Technical Context

- **Language/Dependencies**: Python 3.14 + Pico2D 1.5.1, 표준 pathlib/dataclasses/bisect/math/unittest. requirements.txt 변경 없음.
- **Runtime**: 게임 환경은 원본 저장소 D:/GitHub/circuit-warden/.venv/Scripts/python.exe를 명시적으로 사용할 수 있다. 작업트리에 별도 환경을 만들거나 도구 Python으로 게임 의존성을 변경하지 않는다.
- **Platform/Performance**: 현재 Windows/Pico2D와 엔진 dt 계약 유지. 장면당 경로별 한 번 로딩, draw/update 중 파일 I/O 없음. 임의 개체 수/FPS 성능 보장은 하지 않는다.
- **Testing**: 순수/대역 자동 검사 + 실제 로컬 임시 Pico2D 화면 + 사용자 직접 확인을 구분. 실행 절차는 [quickstart](quickstart.md).
- **Research**: [research.md](research.md), [data-model.md](data-model.md), [공개 계약](contracts/sprites.md).
- **Style**: 사용자 지정 Ponytail full. 범용 로더·임포터·편집기·자동 패킹·새 의존성 제외.

## Constitution Check

- [x] 사용자 결정(계획 구현·실 시트 미반영·확인 전 삭제 금지)과 현재 진행 상태를 구분했다.
- [x] feature/engine의 architecture/progress/workflow/008 verification과 구현을 확인했다.
- [x] 문서 영향·자동 검사·실제 출력·사용자 확인·정리 증거를 계획했다.
- [x] 웹 서버/DB/다른 엔진·일반적인 추가 승인 절차를 도입하지 않는다.
- [x] 설계 후 재검토: 기존 렌더/수명 계약을 재사용하고 상세 제안을 사용자 승인으로 표시하지 않는다.
- [x] 최신 지시에 따라 tasks/analyze 이후 증분 구현하며 사용자 출력 확인 전 정리를 보류한다.

## Decisions & Alternatives

1. **장면 단위 이미지 저장소**: ImageStore(root)는 명시적 기준 경로를 갖고 파일 경로를 정규화하여 ImageRef를 캐시한다. 같은 파일은 한 번 로드한다. 생성은 파일/SDL 작업 없이 가능하나 load는 활성 renderer가 있을 때만 수행한다. 기본 게임 자산은 향후 assets를 기준으로 사용할 수 있지만 이번 변경은 그 폴더나 실 시트를 만들지 않는다.
2. **소유권**: 원본 pico.Image를 외부에 공개하지 않고 ImageRef가 소유한다. close에서 원본 texture 포인터를 먼저 분리하고 유효 포인터를 한 번 해제해 예외 traceback이나 외부 참조가 남아도 재해제를 막는다. 닫힌 참조 사용은 오류다. 설치 버전 소멸자의 None 처리와 오류 경로는 구현 시 실제 SDL 검사한다. 단순 dict.clear만으로 해제 시점을 보장하지 않는다.
3. **최소 데이터**: 프레임은 좌상단 원점의 정수 영역과 정규화 기준점, 클립은 프레임과 양수 초 단위 지속 시간 및 loop. 기존 durationsMs를 임시 설정에서 초로 변환할 수 있지만 범용 JSON 변환기를 제품에 추가하지 않는다.
4. **재생**: 누적 시간을 주기로 나눈 나머지와 누적 종료 시각 검색으로 프레임 선택. 같은 clip은 유지, restart=True면 초기화, 다른 clip은 0부터. 단발 완료는 마지막 프레임 고정. 부동소수점 경계는 근접/정확 경계 자동 검사로 확인하며 이벤트 시스템은 추가하지 않는다.
5. **그리기**: 기존 draw_image에 키워드 전용 source/flip_x 선택을 추가해 기존 호출의 전체 이미지 경로를 그대로 유지한다. 영역 경로만 clip_draw 또는 rad=0인 clip_composite_draw를 사용하고 알파/blend 저장·복원 처리를 공유한다. sprites.draw_sprite는 기준점을 논리 bounds로 바꾸고 이 경로에 위임한다.
6. **좌표**: source는 좌상단 → Pico2D bottom으로 한 번 변환한다. 기존 _output_rect의 출력 사각형 중심을 (center_x, pico.canvas_height-center_y)로 바꾸며 viewport offset을 다시 더하지 않는다. w/h 모두 명시한다. 월드 y-up과 UI y-down은 기존 두 transform에 맞춰 기준점 bounds만 다르게 계산한다. 수평 반전 시 pivot_x도 1-pivot_x로 바꿔 기준점이 같은 위치를 가리키게 한다.
7. **기존 렌더 계약**: Renderer 정렬·월드→UI 순서·가드·숨김은 변경하지 않는다. RenderItem bounds는 호출자가 정확한 스프라이트 영역을 제공하거나 None으로 두어 보수적으로 표시한다. 임의로 원점/원본 크기 bounds를 가정해 잘못 컬링하지 않는다.
8. **장면 연결**: LevelScene에 선택적 images 인자를 추가한다. 객체/Canvas close를 모두 시도한 다음 images.close를 시도하며 기존 복수 오류 수집을 유지한다. images=None 기존 호출은 동일하다. 저장소는 한 장면 전용이며 닫힌 저장소를 새 장면/재진입에 재사용하지 않는다. 이미지 기능을 쓰는 장면을 다시 만들 때 새 저장소를 사용한다.
9. **오류 경계**: 로딩·데이터·텍스처 상태 변경 오류와 Python draw 예외는 보존한다. Pico2D clip 함수가 SDL_RenderCopy(Ex) 반환값을 버리는 한계는 숨기지 않는다. 해당 경로의 모든 native draw 실패를 검출한다고 주장하지 않으며, 실패 검출 강화가 필요하면 source rect 직접 SDL 경로로 별도 변경한다. 기존 source=None draw_image의 _sdl 검사 계약은 유지한다.
10. **리셋**: 장치 리셋 자동 재업로드는 제외. 현행 명시 오류→장면 정리를 유지한다. TARGET texture도 계속 거부한다.

## Project Structure & Interfaces

| 경로 | 예정 변경·호출 관계 |
|---|---|
| sprites.py (신규) | ImageRef/ImageStore, SpriteFrame/SpriteClip/SpritePlayer, draw_sprite. GameObject/UIElement가 직접 사용 |
| game_framework.py | draw_image의 선택적 source/flip_x, LevelScene의 선택적 images 수명만 확장 |
| tests/test_sprites.py (신규) | 로딩·프레임/클립 검증·재생·그리기 좌표/기준점 자동 검사, 실 시트 불필요 |
| tests/test_world_rendering.py | 기존 draw_image 보존, clip 인자·상태 복원·잘못된 출력 경계 |
| tests/test_scene_integration.py | images=None 회귀, 로딩 부분 실패/정리 실패/잔존 참조/중복 exit |
| engine.py / Renderer / GameObject / UIElement | 기존 출력 크기 동기화·루프·등록·정렬 사용. 계약 변경 계획 없음 |
| main.py / framework_demo.py | 기본 실행은 변경하지 않음. 실 시트 의존 추가 없음 |
| 임시 로컬 검사 폴더 (미추적) | 별도 실행 하네스·설정·필요시 임시 복사본. 사용자 확인 전 보존, 확인 후 이번 생성물만 제거 |
| assets / art / requirements.txt | 실 시트 반영·원본 수정·신규 패키지 없음 |
| docs와 specs/009-sprite-runtime | 아래 문서 영향과 검증 근거 |

공개 호출과 소유권 상세는 [contracts/sprites.md](contracts/sprites.md). 승인된 계획에 따라 게임 소스·자동 테스트를 구현한다. 임시 화면 자료는 별도 미추적 경로에 둔다.

## Documentation Impact (mandatory)

구현은 후속 tasks/analyze 후 진행한다. 작은 검증 가능한 증분으로 나누며 각 증분의 코드·문서·검증 결과를 함께 커밋한다.

| 증분 | 관찰 가능한 결과 | 검사·기록·커밋 |
|---|---|---|
| P1 로딩과 정지 프레임 | 이미지 공유, 프레임 하나, 장면 종료 시 해제 | FR-001/005~007/010 자동 검사, docs/verification 갱신 후 커밋 |
| P2 재생과 표시 옵션 | 시간 기반 독립 재생, 반복/단발·반전·기준점·투명도 | FR-002~004와 기존 렌더/수명 회귀, docs/verification 갱신 후 커밋 |
| P3 임시 실제 출력 | 영구 자산 없이 실 시트의 로컬 화면 | Codex 관찰과 실행법 기록. **사용자 확인 대기, 임시 자료 삭제 금지** |
| P4 확인 후 정리 | 사용자 결과 반영, 이번 임시 자료 제거, 원본/자동 검사 보존 | FR-008~009 추적 파일·경로·원본 보존 확인, docs/verification 최종 갱신 후 커밋 |

feature/sprite-runtime은 feature/engine에서 분기한 별도 작업트리다. main의 무관한 미커밋 변경은 보존한다. 구현 통합은 주 에이전트가 맡는다. 독립 인터페이스·검증 검토는 gpt-6.1-sol/medium, 명확한 링크·범위 점검은 gpt-6-luna/medium을 사용하며 작은 수정을 과도하게 나누지 않는다. 동시 쓰기는 담당 파일/작업트리를 분리한다.

| 요구사항/결정 | 기준 docs | 바뀌는 내용 | 갱신 시점 | 검증 방법 |
|---|---|---|---|---|
| FR-001~007/010 | architecture | 미구현 설계 안내, 구현 후 실제 API·좌표·수명 | 설계/각 구현 증분 | 계약과 코드 대조 |
| FR-008~009 | art-direction / progress | 실 시트 미반영, 사용자 확인 전 보존, 확인 후 임시 자료만 정리 | 설계/대기/정리 | Git 추적 여부·사용자 발화·원본 보존 |
| FR-DOC / SC-DOC | docs/README / progress / 009 verification | 진입 링크·현재 단계·실행 증거와 한계 | 각 증분 | 링크·상태 일치 |
| 게임 규칙 | game-design / systems | 영향 없음: 게임 정책/판정 미변경 | 완료 점검 | 범위 대조 |
| 일반 개발/환경 | workflow / tooling / requirements | 영향 없음: 임시 검사 예외만 009에 한정 | 완료 점검 | 변경 목록 |

## Verification & Risks

- [verification.md](verification.md)는 현재 구현·검사 결과와 미실행을 기록한다. 이전 008 검사를 새 스프라이트 성공으로 전용하지 않는다.
- 자동 검사: 프레임 경계/가변 시간/큰 dt/단발/독립성, 경로 정규화와 실패 캐시, 기준점/반전/크기, 두 transform·비영점 viewport, 알파/blend 성공·예외 복원, 해제 중 예외와 traceback 보유, 기존 호출 보존.
- 실제 화면: 임시 시트로 선택 영역·행 방향·투명 배경·원본/확대·반전·기준점 표시·월드/UI·화면 크기 변경·장면 재진입 확인.
- 사용자 직접 확인: 자동/도구 관찰과 별도. 확인 전 P3 대기를 유지하고 P4를 실행하지 않는다. 종료·침묵·일부 항목 확인은 전체 확인이 아니다.
- 삭제는 생성 목록에 적힌 임시 파일만 대상으로 한다. 정규화 절대 경로를 확인한 뒤 처리하고 art 원본·광범위 폴더·자동 테스트는 삭제하지 않는다.
- 위험: clip 경로의 SDL 오류 코드 미노출, 정수 출력 좌표 반올림, DPI별 시각 품질, 기준점과 원본 시트 배치의 불일치. 실제 출력 전에는 정상 동작 완료로 보고하지 않는다.

## Engine Integration Plan

현재 통합 기준은 `feature/engine`의 d7d68308이다. 기존 009 구현을 재작성하지 않고 최신 패키지에 배치한다. 공개 경로는 `game_framework`와 `game_framework.sprites`이며 루트 `sprites.py`는 기존 임시 실행기의 import 호환만 제공한다. image source 검사·좌표 투영은 게임 API에, Pico2D clip 호출과 공유 상태 복원은 엔진 backend에 둔다. 이미지 없는 장면과 전체 이미지 draw의 동작은 유지한다.

1. 기존 009 테스트를 unit/integration 배치에 맞추고 실패를 확인한다.
2. 이미지·프레임·재생·장면 정리를 이식하고 008의 최신 회귀 검사를 보존한다.
3. 전체 자동 검사와 실제 PNG·SDL 출력을 확인한다. 원본 시트는 읽기 전용으로 사용한다.
4. docs·009 검증을 동기화하고 한국어 설명의 커밋을 `feature/engine`에 게시한다. main의 커밋된 최신 아트 상태를 보존한다.
5. `feature/engine → main` PR을 생성한다. 이전 사용자 직접 확인이 남으면 Draft로 표시하고 완료로 주장하지 않는다. PR 생성 후 게임 작업을 별도 브랜치에서 진행하며 main 병합은 이번 지시에서 수행하지 않는다.

로컬 Git 메타데이터 쓰기가 제한되어 원본의 무관한 미커밋 변경을 보존한 파일 사본에서 검사하고 GitHub의 예상 head 검사로 원격 커밋을 게시한다. 원격 head가 바뀌면 덮어쓰지 않고 재검토한다.
