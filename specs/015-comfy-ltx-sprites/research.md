# Research
- **Decision**: --media-cli 재사용. **Rationale**: video 인수·JSON 계약이 있다. **Alternative**: route_media.py provider 추가는 비용/fallback까지 건드려 제외.
- **Decision**: Comfy-Org/workflow_templates e7cd011d4ded3411c2f481200544f0be6fdc962e를 고정. **Rationale**: 재현 가능. **Alternative**: 범용 그래프 변환기는 불필요.
- **Decision**: 설치 INT8·Gemma4·VAE, prompt enhancer 끔. **Rationale**: 다운로드 없이 원문 전달.
- **Decision**: job.json 재개. **Rationale**: GPU timeout과 서버 실패 구별. **Alternative**: 무조건 재제출·전역 interrupt는 중복/타 작업 손실 위험.
출처: https://docs.comfy.org/tutorials/video/ltx/ltx-2-5, 로컬 object_info/system_stats, sprite_set.py generate().

