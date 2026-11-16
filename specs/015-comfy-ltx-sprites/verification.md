# Verification: ComfyUI LTX-2.5 연결

## 2026-11-16 1차 증분
- 명세 FR-001~007과 tasks 대응 분석: 누락·충돌 없음. 구현은 사용자 연결 요청 범위다.
- 공식 UI 원본 2개를 출처 커밋과 SHA-256, MIT 라이선스와 함께 보존했다.
- 설치된 ComfyUI 0.45.4의 `execution.validate_prompt`: I2V 34노드·FLF2V 30노드 모두 valid=True. GPU 제출 없음.
- `.local-tools/python/Scripts/python.exe -B scripts/comfy-media/media.py doctor`: status=ok, 설치 모델·노드 일치, generationSubmitted=false.
- `.local-tools/python/Scripts/python.exe -B -m unittest discover -s tests -p test_comfy_media.py -v`: 9개 통과. 모델 콤보 스키마, 그래프 준비, 원본/출력 보호, 외부 서버 차단, timeout/재개, 응답 유실, 기존 sprite_set subprocess JSON 계약 확인.
- 실제 영상 생성·디코딩·스킬 설치는 다음 증분에서 검사한다. 게임 실행과 전체 회귀는 게임 코드 변경이 없어 선택하지 않았다.
- 문서 영향: docs/tooling.md 연결 설계, docs/progress.md 활성 범위. 루트 README·게임 자산은 변경하지 않는다.
