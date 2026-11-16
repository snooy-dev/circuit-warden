# 도구 구성

이 문서는 현재 설치 구성과 검증 상태를 유지한다. 설치 과정의 일지나 과거 버전을 누적하지 않는다. 아트 제작·채택 상태는 [아트 기준](art-direction.md#현재-제작-상태)이 소유한다. 반복 스프라이트 생성·보정은 기능 문서 없이 진행하고 결과·검사는 채팅으로 보고한다.

## Git에 포함할 것

| 위치 | 주된 내용 | Git 관리 |
|---|---|---|
| `docs/` | 현재 게임 기획·규칙·기술 구조·아트 기준·진행 상태 | 포함 |
| `.specify/memory/constitution.md` | 개발 원칙과 완료 조건 | 포함 |
| `.specify/templates/` | 명세·계획·작업 문서 생성 양식과 프로젝트 재정의 | 포함 |
| `.specify/scripts/` | 기능 폴더·계획·템플릿을 다루는 공식 실행 스크립트 | 포함 |
| `.specify/workflows/speckit/`, `workflows/overlays/` | 기본 개발 흐름과 필수 docs 단계 | 포함 |
| `.specify/`의 초기화·통합 설정, 설치 명세, workflow registry | 버전·Codex 통합 선택·파일 해시·워크플로우 등록 정보 | 포함 |
| `.specify/feature.json`, `workflows/runs/`, 기타 `.specify/.gitignore` 항목 | 개인별 활성 기능, 실행 상태·원시 로그, 로컬 통합 패키지 | 제외 |
| `AGENTS.md`, `scripts/use-project-tools.ps1` | Codex 작업 규칙과 로컬 도구 준비 | 포함 |
| `specs/<feature>/` | 진행 중인 변경의 명세·계획·작업·최신 검증 근거 | 작업 중 포함, 완료 후 정리 조건은 AGENTS 참고 |
| `.agents/skills/`, `.local-tools/` | 설치된 스킬·도구·도구 전용 가상환경 | `.git/info/exclude`로 로컬 제외 |

`.specify/`는 **개발 방법**, `docs/`는 **현재 무엇을 만들고 있는지**를 주로 담는다. `.specify/` 전체를 무시하면 새 checkout에서 문서 필수 단계와 템플릿을 잃으므로 공유 설정은 버전 관리한다. 설정 안의 설치 명세는 현재 상태이며 변경일지가 아니다.

## 현재 설치

| 도구 | 설치 버전·원본 | 위치 |
|---|---|---|
| Spec Kit | [github/spec-kit](https://github.com/github/spec-kit), v1.3.2, `55264c2f2f2d1146f02abc543cb913dcdf1f9342` | `.local-tools/spec-kit`, `.local-tools/python` |
| Agent Sprite Forge | [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge), `6b3da5c444363378e20f3fce130ebecc22f343dd` | `.local-tools/agent-sprite-forge` |
| pixelfx | [patch-gg/pixelfx](https://github.com/patch-gg/pixelfx), 0.3.0, `a84159688af3ca37a4be05a0d422b94451b2e24e` | `.local-tools/pixelfx` |

스킬은 모두 `.agents/skills/`에 있다. Spec Kit 9개, Sprite Forge 5개(`generate2dsprite`, `generate2dmap`, `generate2dmedia`, `video2dsprite`, `codeart2d`), pixelfx 1개로 총 15개다. 새로 설치된 스킬은 다음 대화 차례의 목록에서 확인한다.

게임은 기존 `.venv/`와 `requirements.txt`의 Pico2D 1.5.1을 사용한다. 도구는 기존 Python 3.14.7로 만든 `.local-tools/python/`을 사용하며 Python 자체를 추가 설치한 것은 아니다. 이 도구 환경에는 Specify CLI와 Sprite Forge의 NumPy·Pillow·SciPy 의존성이 있다. pixelfx는 기존 Node.js v24.19.0을 사용한다. 전하 PNG 생성은 도구 환경의 NumPy·Pillow를 사용한다. 게임 requirements.txt에서 NumPy를 제거했으며 런타임은 이를 import하지 않는다. 도구 의존성과 전역 환경은 공유하거나 변경하지 않는다.

## 사용과 복원

프로젝트 루트의 PowerShell에서 현재 세션만 준비한다.

```powershell
. ./scripts/use-project-tools.ps1
specify integration status --json
specify workflow resolve speckit
```

게임 실행·검사에는 `.venv/Scripts/python.exe`를 명시한다. 준비 스크립트가 노출하는 `python`은 도구 환경용이다. pixelfx의 원본 경로는 `PIXELFX_DIR`로 설정된다.

로컬 제외 항목은 다른 checkout으로 복제되지 않는다. 복원할 때는 위 원본의 지정 버전을 `.local-tools/`에 받고 도구 전용 가상환경에 Spec Kit 패키지와 Forge `requirements.txt`를 설치한다. Codex 통합은 PowerShell·skills 방식이며 events는 비활성이다. Forge의 `tools/install_skills.py --apply --dest .agents/skills`, pixelfx 원본의 `skills/pixelfx`를 같은 스킬 폴더에 설치한다. 기존 constitution·프로젝트 templates/overrides·workflow overlay는 보존하고 설치 후 아래 검사를 다시 수행한다. `.git/info/exclude`의 두 로컬 제외 경로도 새 checkout에 설정해야 한다.

## FFmpeg와 생성 서비스

FFmpeg 9.0.2 essentials를 `.local-tools/ffmpeg/ffmpeg-9.0.2-essentials_build/bin`에 설치했다. 공식 FFmpeg 다운로드 페이지가 안내하는 [Gyan 배포본](https://www.gyan.dev/ffmpeg/builds/)이며 ZIP과 게시된 SHA256 일치를 확인했다. 준비 스크립트가 현재 세션 PATH에만 추가한다. 게임 의존성과 전역 PATH는 변경하지 않았다. FFmpeg는 영상 생성 AI가 아닌 디코딩·프레임 추출·인코딩 도구다. 아트 작업에서의 사용 여부는 사용자 요청 범위에 맞춰 정하며 도구 사용만을 위해 계획 문서를 만들지 않는다.

외부 영상 생성 서비스 인증은 미구성이다. 현재 아트 제작·채택 상태는 [아트 기준](art-direction.md#현재-제작-상태)을 따른다. 도구 설치가 새 생성 승인을 뜻하지 않는다. FFmpeg 기능 검사는 VP9 알파·H.264·PNG 지원을 확인했다. 임시 디렉터리 접근 오류는 검사 프로세스의 TEMP/TMP를 `.local-tools/tmp`로 지정해 해소했다.

### ComfyUI LTX-2.5 스프라이트 연결

`scripts/comfy-media/media.py`를 `sprite_set.py --media-cli`에 연결했다. `generate2dsprite`·`video2dsprite`·`generate2dmedia`의 프로젝트 영상 경로는 `local:comfyui-ltx25`다. 이미지 생성 경로와 기존 키잉·정렬·완성 처리는 유지한다. 로컬 연결 실패는 유료 API로 전환하지 않는다.

- 서버: `http://127.0.0.1:8188`, ComfyUI 0.45.4, RTX 5090 32GB에서 검사했다. Desktop 설치 루트는 `C:\Users\Developer\AppData\Local\Comfy-Desktop\ComfyUI-Installs\ComfyUI`, 실행 환경은 그 아래 `ComfyUI/.venv`다. 모델·입출력 루트는 `D:\ComfyUI`다.
- 모델: `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors`, `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors`, LTX-2.5 video/audio BF16 VAE, I2V용 `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors`가 필요하다. 새 모델 다운로드·전역 환경 변경은 하지 않았다.
- 출처: [공식 ComfyUI 워크플로](https://github.com/Comfy-Org/workflow_templates/tree/e7cd011d4ded3411c2f481200544f0be6fdc962e/templates)의 `video_ltx2_5_i2v.json`·`video_ltx2_5_flf2v.json`. [원본·API 그래프·출처와 SHA](../scripts/comfy-media/workflows/provenance.json) 및 MIT LICENSE를 함께 보존한다. UI 원본을 ComfyUI에 열 수도 있다. 어댑터는 평탄화한 API 그래프를 사용하며 프롬프트 보강기와 예제의 게임/만화 배제 부정 프롬프트를 제거했다.
- 입력은 불투명 키 배경의 원화다. 투명 이미지는 먼저 기존 스킬의 원화 준비 단계를 사용한다. `--last-frame`을 주면 첫/끝 프레임 가이드를 사용한다. 이는 끝 프레임 픽셀 일치나 완전한 루프를 보장하지 않는다.
- `480p`/`720p`는 기존 호출기와 호환되는 옵션명이며 실제 짧은 변은 512/768px, 두 변은 64배수다. 전체 캔버스를 크롭 없이 조정하므로 종횡비는 반올림 오차가 있다. 최대 변 2048px, 1~20초, 24fps·8n+1프레임으로 길이를 반올림한다. 실제 크기·길이·원본 크기·해시·seed는 job/result에 남긴다. 오디오는 제거한다.

프로젝트 루트에서 도구 세션을 준비한 뒤 실행한다. 출력 폴더는 새 경로를 사용한다.

```powershell
. ./scripts/use-project-tools.ps1
python scripts/comfy-media/media.py doctor
python scripts/comfy-media/media.py prepare --prompt-file <txt> --reference <png> --duration 2 --resolution 480p --out-dir <준비폴더>
python scripts/comfy-media/media.py video --prompt-file <txt> --reference <png> --duration 2 --resolution 480p --out-dir <생성폴더>
python .agents/skills/video2dsprite/scripts/sprite_set.py run --plan <set>/set_plan.json --media-cli scripts/comfy-media/media.py --jobs 1 --timeout 7200
python scripts/comfy-media/media.py resume --job <생성폴더>/job.json
```

`doctor`·`prepare`는 GPU 제출이 없다. `resume`은 기존 prompt_id의 결과만 회수한다. 스킬 실행은 로컬 job을 먼저 재개하고 오류 뒤 자동으로 새 take를 제출하지 않는다. 같은 job의 동시 재개는 피한다. `prepared` 상태에서 프로세스가 끝난 작업은 GPU 미제출이며 원본 준비 기록을 보존하고 새 폴더로 시작한다. `submitting`/`queued`/`timeout`은 새 생성 전에 기존 작업을 확인한다. 제출 응답이 유실돼도 미리 저장한 ID로 조회할 수 있다. 서버 재시작으로 history가 사라지고 로컬 history도 없으면 자동 재제출하지 않으므로 ComfyUI 큐·출력을 확인해야 한다. 전체 대기열 삭제나 다른 작업 중단은 수행하지 않는다.

스킬 설치본은 Git 제외라 업데이트/복원 뒤 아래 명령을 재실행한다. 설치기는 세 SKILL.md의 안내와 sprite_set.py의 로컬 재개 부분만 바꾸며, 예상 코드가 달라졌으면 쓰기 전에 멈춘다.

```powershell
python scripts/comfy-media/install_skill_route.py
python scripts/comfy-media/install_skill_route.py --check
```

I2V·첫/끝 프레임 경로 모두 512×512·49프레임·약 2.04초 로컬 생성과 디코딩을 통과했다. 상세 자동 검사·호출기 확인은 [연결 검증](../specs/015-comfy-ltx-sprites/verification.md)을 따른다. 시험 영상은 도구 연결 검증이며 미술 승인·게임 자산 채택이 아니다.

## 검증 기준

- Spec Kit: Codex만 등록, 스킬 누락·변경 없음. 실행 로그 제외를 추가한 `.specify/.gitignore`는 의도한 수정 1건으로 통합 검사에서 경고한다. 이를 없애려고 설치 명세의 해시를 조작하지 않는다. 프로젝트 템플릿이 기본 템플릿보다 우선한다.
- workflow resolve: 문서 읽기 → specify → 설계 문서 반영 → spec 검토 → plan → 기술 문서 반영 → plan 검토 → tasks → analyze → implement → docs 동기화 → converge 순서를 확인한다. 이 명령은 흐름을 실행하지 않는다.
- Forge: 원본 171개 파일 설치 확인 후 프로젝트 LTX 연결을 위해 SKILL.md 3개·sprite_set.py 1개를 의도적으로 수정한다. NumPy·Pillow·SciPy·pixelfx·FFmpeg는 검사했다. 여러 Python 경로 경고가 있으므로 도구 준비 스크립트나 명시적 실행 경로를 사용한다. 선택적 SVG 렌더러 resvg-py와 외부 영상 서비스 인증은 미구성이다.
- pixelfx: 원본의 `node tools/check.mjs fire/torch` 검사로 1 pass, 0 fail, 0 warn을 확인했다. 게임용 에셋은 만들지 않았다.
- 도구 준비 스크립트: 경로 설정과 도구 미설치 시 오류 처리를 확인한다.
- 문서: 링크·삭제된 결정 연표 참조·필수 docs 항목·Git 제외 범위를 확인한다.

도구 설정이 PPTX 내용 확정이나 게임 구현을 의미하지 않는다. 반복 스프라이트 생성·보정은 별도 기능 문서 없이 진행하고 결과·검사는 채팅으로 보고한다. 채택 상태·장기 기준만 기존 아트 기준·진행 상태에 반영한다. 게임 규칙·코드·런타임 통합 변경은 Spec Kit 흐름을 따른다. 자동 문서 단계만으로 완료를 판단하지 않는다.

## 효과 PNG 재생성

승인 원본과 라이선스를 보존하며 다음 명령으로 assets/charge/baked를 재생성한다. Node/pixelfx와 NumPy/Pillow는 제작 도구에만 필요하고 게임은 생성된 PNG만 읽는다.

```powershell
.\.local-tools\python\Scripts\python.exe -X utf8 -B scripts/bake-effects/charge.py
node scripts/bake-effects/link.mjs
.\.local-tools\python\Scripts\python.exe -X utf8 -B scripts/bake-effects/check.py --output-dir $testOutput
```

`$testOutput`은 비교 이미지 보관 폴더다. 과거 NumPy 구현과의 성능 비교에는 게임 환경에 별도 선택 의존성 `numpy==2.5.4`가 필요하다. 게임 실행·일반 테스트에는 필요하지 않으며 자세한 재현은 [검사 안내](../tests/README.md)를 따른다.
