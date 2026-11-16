# Implementation Plan: ComfyUI LTX-2.5 스프라이트 연결
**Date**: 2026-11-16 | **Spec**: [spec.md](spec.md) | **Status**: Ready

## Summary
기존 sprite_set.py의 --media-cli를 사용한다. 공식 UI 원본 두 개와 대응 고정 API 그래프를 보관한다. Python 어댑터로 입력 검증·업로드·제출·완료 대기·다운로드·재개를 처리한다. 검토에서 기존 호출기의 오류 후 자동 새 take가 중복 GPU 작업을 만드는 문제가 확인돼, 로컬 경로에만 적용되는 재개 패치를 설치기로 보존한다(FR-004).

## Technical Context
- **Language/Dependencies**: Python 표준 라이브러리, 기존 Pillow·FFmpeg/ffprobe.
- **Runtime**: .local-tools/python/, 게임 환경 불변.
- **Platform/Performance**: Windows, ComfyUI 0.45.4, RTX5090 32GB. 2초·512px 시험의 서버 실행 시간은 verification.md에 기록한다.
- **Testing**: HTTP 클라이언트 대역 unittest, 실제 모델/스키마 검사, 짧은 생성·디코딩. 게임 회귀는 영향 없어 제외.

## Constitution Check
- [x] 요청과 가정·생성 시험 범위를 구분한다.
- [x] 기준 docs와 제약을 확인했다.
- [x] 문서·실행 검증을 포함한다.
- [x] 새 서버·DB·엔진·의존성을 추가하지 않는다.

## Decisions & Alternatives
공식 그래프를 고정 API JSON으로 변환한다. 범용 UI→API 컴파일러·웹 UI 자동화는 제외한다. prompt enhancer를 우회하고 게임/만화 배제 negative를 지운다. 결과는 기존 키잉·정렬·클립 처리로 전달한다. 로컬 미완료 작업은 같은 take에서 재개하며 일반 공급자의 경로는 유지한다.

## Project Structure & Interfaces
- scripts/comfy-media/media.py: video/doctor/prepare/resume CLI.
- scripts/comfy-media/workflows/: 원본·API 그래프·라이선스·출처.
- scripts/comfy-media/install_skill_route.py: 세 스킬 안내 및 sprite_set.py의 로컬 재개 패치 재적용.
- tests/test_comfy_media.py: 입력·작업 상태·응답·재개·생성기 계약.
- tests/test_comfy_skill_install.py: 설치 멱등성·원본 불일치·실제 호출기의 중복 생성 방지.
- .agents/skills/{generate2dsprite,video2dsprite,generate2dmedia}/SKILL.md: 안내 추가, Git 제외 유지.
- docs/tooling.md, docs/progress.md: 사용·현재 상태.

## Documentation Impact (mandatory)
feature/comfy-ltx-sprites에서 기존 tmp를 보존한다. gpt-6.1-sol/high 서브에이전트는 공식 그래프와 호출기 복구 패치/설치기를 담당하고 주 에이전트가 어댑터·통합·최종 검증을 맡는다. 파일 소유를 분리한다.
| 요구사항 | 기준 docs | 변경 | 시점 | 검증 |
|---|---|---|---|---|
| FR-001~006 | docs/tooling.md | 출처·CLI·복구·스킬 | 구현 후 | 실제 명령 |
| FR-007 | docs/progress.md | 완료 수준·한계 | 검증 후 | verification 대조 |

## Verification & Risks
스키마·필수 모델 검사 후 두 경로의 짧은 로컬 생성을 각각 1회 검사한다. 끝 프레임 가이드의 시각적 정확성·스프라이트 미술 품질은 별도다. 제출 전에 prompt_id를 정하고 저장하며 응답 유실을 자동 재시도하지 않는다. timeout은 동일 job.json의 resume 또는 패치된 sprite_set에서 회수한다.

