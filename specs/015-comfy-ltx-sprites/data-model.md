# Data Model
- Workflow: 원본/API 파일·SHA256·upstream 커밋·노드 매핑.
- Job: 프롬프트·이미지 해시·해상도·프레임 수·seed·서버·client_id·prompt_id·상태. prepared → submitting → queued → complete 또는 error/timeout. 응답 유실은 재제출 없이 확인.
- Result: status, route=local:comfyui-ltx25, model, artifact(절대 경로), sha256, estimateUsd=0(API 요금 없음), lastFrameUsed, durationRequested/Used, fps, frames, job.
새 생성은 새 출력 폴더만 허용한다. 재개는 같은 job.json만 사용한다.

