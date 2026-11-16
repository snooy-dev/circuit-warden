# Implementation Plan: ComfyUI LTX-2.5 스프라이트 연결
**Date**: 2026-11-16 | **Spec**: [spec.md](spec.md) | **Status**: Ready

## Summary
기존 sprite_set.py의 --media-cli를 사용한다. 공식 UI 원본 두 개와 대응 고정 API 그래프를 보관한다. Python 어댑터로 입력 검증·업로드·제출·완료 대기·다운로드·재개를 처리하며 vendor 런타임은 수정하지 않는다.

## Technical Context
- **Language/Dependencies**: Python 표준 라이브러리, 기존 Pillow·FFmpeg/ffprobe.
- **Runtime**: .local-tools/python/, 게임 환경 불변.
- **Platform/Performance**: Windows, ComfyUI 0.45.4, RTX5090 32GB. 시간은 실측 전 미정.
- **Testing**: 가짜 HTTP unittest, 실제 모델/스키마 검사, 짧은 생성·디코딩. 게임 회귀는 영향 없어 제외.

## Constitution Check
- [x] 요청과 가정·생성 시험 범위를 구분한다.
- [x] 기준 docs와 제약을 확인했다.
- [x] 문서·실행 검증을 포함한다.
- [x] 새 서버·DB·엔진·의존성을 추가하지 않는다.

## Decisions & Alternatives
공식 그래프를 고정 API JSON으로 변환한다. 범용 UI→API 컴파일러·웹 UI 자동화·vendor 코드 분기는 제외한다. prompt enhancer를 우회하고 게임/만화 배제 negative를 지운다. 결과는 기존 키잉·정렬·클립 처리로 전달한다.

## Project Structure & Interfaces
- scripts/comfy-media/media.py: video/doctor/prepare/resume CLI.
- scripts/comfy-media/workflows/: 원본·API 그래프·라이선스·출처.
- scripts/comfy-media/install_skill_route.py: 세 스킬의 프로젝트 경로 안내 재적용.
- tests/test_comfy_media.py: 입력·작업 상태·응답·재개·생성기 계약.
- .agents/skills/{generate2dsprite,video2dsprite,generate2dmedia}/SKILL.md: 안내 추가, Git 제외 유지.
- docs/tooling.md, docs/progress.md: 사용·현재 상태.

## Documentation Impact (mandatory)
feature/comfy-ltx-sprites에서 기존 tmp를 보존한다. gpt-6.1-sol/high 서브에이전트는 공식 그래프 조사/API 변환 파일만 담당하고 주 에이전트가 통합·검증한다.
| 요구사항 | 기준 docs | 변경 | 시점 | 검증 |
|---|---|---|---|---|
| FR-001~006 | docs/tooling.md | 출처·CLI·복구·스킬 | 구현 후 | 실제 명령 |
| FR-007 | docs/progress.md | 완료 수준·한계 | 검증 후 | verification 대조 |

## Verification & Risks
스키마·필수 모델 검사 후 짧은 로컬 생성 1회. 끝 프레임 경로는 스키마/계약 검증하며 시각적 정확성은 별도다. 제출 전 상태를 저장하고 응답 유실을 자동 재시도하지 않는다. timeout은 resume으로 회수한 뒤 sprite_set을 재실행한다.

