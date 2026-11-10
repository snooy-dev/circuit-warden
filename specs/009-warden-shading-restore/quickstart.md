# 검토 안내

1. [원화 대비 최신 후보](../../art/warden/shading-restore/proportion-audit/same-height-comparison.png)에서 동일 높이의 귀·머리·팔·발을 비교한다.
2. [비율 검사 결과](proportion-verification.md)를 읽는다. 최신 후보는 귀·팔 비율 미완료다.
3. [이전 색감만 복원한 Run](../../art/warden/shading-restore/review-v1/run-comparison.gif)은 색감 효과 확인용이며 최신 방향 후보의 동작이 아니다.

색감만 복원한 초기 결과의 재현 명령은 `./.local-tools/python/Scripts/python.exe specs/009-warden-shading-restore/build_review.py`다. 기존 출력이 있으면 덮어쓰기를 거부한다. 최신 후보 리그 적용은 아직 없다.
