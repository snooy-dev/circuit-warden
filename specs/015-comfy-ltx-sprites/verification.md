# Verification: ComfyUI LTX-2.5 연결

## 2026-11-16 1차 증분
- 명세 FR-001~007과 tasks 대응 분석: 누락·충돌 없음. 구현은 사용자 연결 요청 범위다.
- 공식 UI 원본 2개를 출처 커밋과 SHA-256, MIT 라이선스와 함께 보존했다.
- 설치된 ComfyUI 0.45.4의 `execution.validate_prompt`: I2V 34노드·FLF2V 30노드 모두 valid=True. GPU 제출 없음.
- `.local-tools/python/Scripts/python.exe -B scripts/comfy-media/media.py doctor`: status=ok, 설치 모델·노드 일치, generationSubmitted=false.
- `.local-tools/python/Scripts/python.exe -B -m unittest discover -s tests -p test_comfy_media.py -v`: 9개 통과. 모델 콤보 스키마, 그래프 준비, 원본/출력 보호, 외부 서버 차단, timeout/재개, 응답 유실, 기존 sprite_set subprocess JSON 계약 확인.
- 실제 영상 생성·디코딩·스킬 설치는 다음 증분에서 검사한다. 게임 실행과 전체 회귀는 게임 코드 변경이 없어 선택하지 않았다.
- 문서 영향: docs/tooling.md 연결 설계, docs/progress.md 활성 범위. 루트 README·게임 자산은 변경하지 않는다.

## 2026-11-16 최종 증분

### 자동 검사
- `.local-tools/python/Scripts/python.exe -B -m unittest discover -s tests -p "test_comfy*.py" -v`: 14개 통과, skip 0. 호출기 반복 한도를 3으로 둔 재개 검사도 별도 재실행해 3개 통과했다.
- 검토에서 기존 sprite_set의 timeout 후 자동 새 take 및 부분 MP4 채택을 발견했다. 로컬 job을 generic clip 탐색보다 먼저 재개하고, 실패 시 같은 take를 열린 상태로 유지·배치를 멈추도록 수정했다. 기본 경로로 잘못 재실행해도 기존 로컬 작업을 유료 경로로 넘기지 않는다.
- 제출 전에 UUID prompt_id를 저장·POST하며, 응답 유실 이후 POST 재시도 없이 조회한다. HTTP 4xx는 종료 오류다. 다운로드·검증 임시 파일은 `.part`이고 검증된 clip 게시 직후 중단도 로컬 history로 복구한다. 무음화·실제 ffprobe 디코딩·중단 복구 검사를 포함했다.
- `python scripts/comfy-media/install_skill_route.py`로 SKILL.md 3개·sprite_set.py 1개 설치. `--check` 통과, 재실행 변경 0. 원본 코드 불일치는 모든 파일 쓰기 전에 실패하는 것을 검사했다.
- `.local-tools/python/Scripts/python.exe -X utf8 -B C:/Users/Developer/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/<name>`: generate2dsprite·video2dsprite·generate2dmedia 모두 valid. 기본 cp949로 검사했을 때 발생한 읽기 오류는 UTF-8 모드로 해결했다.

### 실제 ComfyUI 실행과 호출기
- 두 명령의 공통 인수: `--prompt-file tmp/comfy-ltx-check/prompt.txt --reference art/warden/walk-hibit/master-v1/master.png --duration 2 --resolution 480p --timeout 1800`.
- I2V: `python scripts/comfy-media/media.py video <공통 인수> --out-dir tmp/comfy-ltx-check/i2v`, prompt_id `1cb43403-2592-426a-aaa6-b12c080a8fe3`.
- FLF2V: 위 명령에 `--last-frame art/warden/walk-hibit/master-v1/master.png --out-dir tmp/comfy-ltx-check/flf2v`, prompt_id `599a7401-50e5-413a-96f0-72dc5cc318ed`.
- 각각 status=ok, H.264 MP4, **512×512, 24fps, 49프레임, 2.041667초, 무음**. lastFrameUsed는 false/true로 분리된다. 서버 execution_start→execution_success는 I2V 36.460초, FLF2V 5.562초였다. 모델 로드·캐시 조건이 다른 1회씩의 실측이므로 성능 비교로 해석하지 않는다.
- 영상 SHA-256: I2V `7902c7ca0338ce050b54e162836ac70a288fe41c63d7ade9112f453edf13e2d0`, FLF2V `fc55641ccf945b4613f77baaec9445558ee22b85c4835d44d20be8ac57508409`.
- 실제 결과 폴더 복사본을 `SetRunner.generate()`에 전달했다. 두 경로 모두 resume subprocess를 거쳐 status=ok, route=local:comfyui-ltx25, frames=49, pinned=false/true를 받았다. 이 검사에서 추가 GPU 제출은 하지 않았다.
- 실제 출력은 `tmp/comfy-ltx-check/{i2v,flf2v}/clip.mp4`와 서버 `D:/ComfyUI/output/sprite-ltx25/`에 남겼다. tmp는 기존 사용자 파일과 함께 Git에서 제외한다.

### 완료 범위와 한계
- 기능·상태 전이·호출 계약·복원·문서까지 검사했다. 영상의 동작/캐릭터 일관성·끝 프레임 시각적 일치, 긴 720p 세트 전체 후처리, 게임 런타임 통합은 검사하거나 승인하지 않았다. 시험 결과를 게임 자산으로 채택하지 않았다.
- 전체 게임 회귀·실제 게임 창은 게임 코드/자산 변경이 없어 제외했다. 모델·ComfyUI 설정·전역 환경·유료 계정은 변경하지 않았다.
- docs/tooling.md의 경로·복원·제약 및 docs/progress.md의 완료 수준을 구현과 대조했다. `git diff --check`와 관련 문서의 로컬 링크·원본 SHA 검사도 통과했다.

### Convergence
- FR 7개, 성공 기준 3개, 수용 시나리오 6개, 계획의 구현 영역 6개와 Constitution 원칙 5개를 현재 코드·검사 결과에 대조했다. 누락/부분/충돌/범위 밖 발견 0, 추가 구현 작업 0이다.
- `check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks`에서 활성 기능 015와 필수 문서를 확인했다. 확장 hooks 파일은 없다. 완료된 tasks에 빈 Convergence 단계를 추가하지 않는다.
