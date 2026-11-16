# Quickstart
프로젝트 루트의 .local-tools/python/Scripts/python.exe 사용. 서버 http://127.0.0.1:8188 필요.
1. `python scripts/comfy-media/media.py doctor`: 모델/노드 점검, 생성 없음.
2. `python scripts/comfy-media/media.py prepare --prompt-file <txt> --reference <png> --duration 2 --resolution 480p --out-dir <새폴더>`: 입력 준비만.
3. `python scripts/comfy-media/media.py video --prompt-file <txt> --reference <png> --duration 2 --resolution 480p --out-dir <다른새폴더>`: 로컬 생성. 선택 `--last-frame <png>`.
4. `python scripts/comfy-media/media.py resume --job <출력>/job.json`: 재제출 없이 회수.
5. `python .agents/skills/video2dsprite/scripts/sprite_set.py run --plan <plan> --media-cli scripts/comfy-media/media.py --jobs 1 --timeout 7200`: 기존 파이프라인 연결.
실제 검사 결과는 verification.md에 기록한다. 시험 클립은 미술 승인/게임 채택이 아니다.

