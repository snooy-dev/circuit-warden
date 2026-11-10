# 수정본 Run 검토

1. [검토 페이지](../../art/warden/shading-restore/run-review-v1/review.html)에서 정상/느린재생,1배/3배,배경전환과프레임을확인한다.
2. [idle·기존Run·수정Run 비교](../../art/warden/shading-restore/run-review-v1/comparison.gif)에서색감·입체감·비율을본다.
3. [좌우GIF](../../art/warden/shading-restore/run-review-v1/both.gif)에서전류방향·천의펄럭임·귀/꼬리관성·발교대를본다.
4. [묶음](../../art/warden/shading-restore/run-review-v1/warden-restored-run.zip)과[검증](verification.md)을확인한다.

재현: `./.local-tools/python/Scripts/python.exe specs/009-warden-shading-restore/build_restored_run.py 새출력폴더명` (기존출력보존).
현재결과검사: `./.local-tools/python/Scripts/python.exe specs/009-warden-shading-restore/check_restored_run.py`.

검토후사용자가채택을판단한다. 기존잠정승인Run은그대로며게임통합은없다. 걷기/공격은이번수정본적용범위밖이다.
