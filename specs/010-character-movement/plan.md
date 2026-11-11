# Implementation Plan: 캐릭터 표시와 좌우 이동 검사

**Date**: 2026-11-11 | **Spec**: [spec.md](spec.md) | **Status**: Ready
**Branch**: feature/character-movement (엔진 PR #2의 26f448d8 기반)

## Summary

기존 LevelScene·GameObject·ImageStore·SpritePlayer를 조합한 작은 game/character.py와 game/scene.py를 만든다. 에셋 3개·게임용 JSON 하나를 사용하고 새 엔진/범용 관리자를 추가하지 않는다.

## Technical Context

- Python 3.14 + Pico2D 1.5.1, 표준 json/pathlib. requirements 변경 없음.
- 실행·테스트: D:/GitHub/circuit-warden/.venv/Scripts/python.exe. 원본 main의 미커밋 변경은 보존하고 별도 파일 사본에서 검사, 연결 GitHub의 예상 head 검사로 게시한다.
- Windows 창 하나·캐릭터 하나. 성능 보증·대규모 벤치마크 제외.
- 검증: 상태/입력/같은 총 dt·애니메이션 회귀, 실제 PNG/SDL 창 smoke, 원본 SHA256·메타데이터 대응.

## Constitution Check

- [x] 사용자 구현 범위와 검사 기본값·최종 게임 규칙 미정을 구분했다.
- [x] architecture/art-direction/progress와 기존 008/009 API를 확인했다.
- [x] docs·자동 검사·실제 창·미확인 기록을 계획했다.
- [x] 기존 Python/Pico2D를 재사용하며 웹·DB·범용 입력 관리자·새 패키지는 제외한다.

## Decisions & Alternatives

프레임 영역은 복사 시 생성하는 assets/warden/animations.json에서 읽고 SpriteFrame/Clip으로 한 번 변환한다. frameSize, columns, count, pivot, durationsMs, file을 저장한다. 제작용 원본 JSON 전체를 런타임에 복사하지 않으며 출처·해시는 assets/warden/README.md에 둔다.
Character는 눌린 키 set·x·facing·SpritePlayer를 가진다. 같은 방향 두 키는 OR, 좌우는 상쇄한다. 포커스 상실/최소화 시 set을 비운다. 이동 후 clamp하고 실제 이동이 없으면 idle이다. idle 반전은 왼쪽만 적용하며 각 Run은 전용 시트를 사용한다. 기존 dt와 공통 발 기준점을 사용한다. 화면 축소 때 양쪽 시트 전체가 들어가는 범위로 제한하고 너무 좁으면 중앙에 둔다.
main은 게임 검사 진입으로 바꾸고 도형 검사는 python -m demos.check로 유지한다. F6/F11/종료는 기존 엔진 API를 재사용한다. 실제 화면에 필요한 최소 안내는 창 제목·콘솔과 README로 제공한다.

## Project Structure & Interfaces

- game/__init__.py, game/character.py: 게임 에셋 로딩과 캐릭터 입력/갱신/렌더 연결.
- game/scene.py, main.py: 장면·고정 바닥선·창 모드 조작·진입.
- assets/warden/{idle,run_left,run_right}.png, animations.json, README.md: 버전 없는 게임 복사본과 출처.
- .gitattributes: PNG binary, text=auto. 작은 PNG이므로 LFS 제외.
- tests/unit/test_character.py, tests/integration/test_character_scene.py: 동작·실제 자산·수명 검사.
- tests/smoke/character_smoke.py: SDL 입력·화면 캡처·종료 검사. 출력은 인자로 받은 임시 폴더에만 생성.

## Documentation Impact (mandatory)

P1 에셋 배치와 검증·출처·현재 문서를 먼저 커밋하고 P2 게임 동작·검사·문서를 다음 커밋에 포함한다. 코드·테스트는 Sol(high)이 담당하고 주 에이전트는 에셋·docs·통합·실제 검증을 담당한다. 파일 담당을 분리하며 Git 쓰기는 주 에이전트만 수행한다.

| 요구사항 | docs | 변경·검증 |
|---|---|---|
| FR-001/006 | art-direction | 실제 복사본과 잠정 승인 원본 구분·해시 |
| FR-002~005 | architecture | 검사 기본값·진입·입력/재생·수명 |
| FR-DOC | progress·README·docs/README·010 verification | PR/브랜치·실행법·실행 증거·미확인 |
| 게임 규칙·환경 | game-design·systems·tooling | 실제 게임 정책·의존성 변경 없음 |

## Verification & Risks

단위 검사는 반대/별칭 키·해제·포커스 상실·경계·dt 분할·idle/run 전환·동일 클립 유지, 자산은 크기/셀/시간/해시를 검사한다. 실제 smoke는 실행 위치 독립·좌우 재생·크기 변경·종료와 이미지 해제를 검사하고 SDL 렌더러 PNG를 관찰한다. 자동 이벤트와 사용자 직접 입력·플레이 품질은 구분한다. 장치 리셋 자동 복구·최종 이동감은 범위 밖이다.
