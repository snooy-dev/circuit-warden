# Verification: 수정본 Run 적용

2026-11-10 사용자 지시로 귀·팔 비율을 맞춘 proportion-fix-v1 이미지를 Run의 제작 기준으로 사용했다. 현재 결과는 [run-review-v1](../../art/warden/shading-restore/run-review-v1/review.html)이며 검토 후보다. 이번 제작 범위는 좌우 Run이다. 걷기·공격 적용과 게임 통합은 제외했다.

## FR-001/002: 색감·비율·출처

지정 소스의 SHA-256은 `2654e9adab12347a5a554518b9d0aead29e73cb7b963e3468065d5e78c87e4d2`다. 입력 높이 938px를 몸 높이 80px로 등록했고 source.png 복사본도 동일하다. 수정된 머리/몸 방향·짧은 귀/팔·둥근 꼬리를 유지했다. 팔이 움직일 때 인위적인 빈 영역이 드러나지 않도록 작은 몸통 겹침 영역을 복원했다. 새 이미지/영상 모델 호출 없이 기존 래스터와 코드 애니메이션을 사용했다.

공통 16색에서 밝은 시안(G≥171) 비율은 idle 26.59%, 이전 Run 50.98%, 수정 Run 23.98%다. 평균 선형 상대 휘도는 각각 0.23687/0.31701/0.22374다. 히스토그램을 강제로 맞추지 않았으며 시점에 따른 차이를 허용한다. 수치는 곡면 표현과 주관적 채택을 대신하지 않는다. [동일 배경 비교](../../art/warden/shading-restore/run-review-v1/comparison.gif)와 전체 시트에서 청색 중간 명암을 관찰했다.

## FR-003: Run·전류·관성·천

- `./.local-tools/python/Scripts/python.exe specs/009-warden-shading-restore/build_restored_run.py`: 종료 0. 좌우 각 16개 고유 프레임·480ms·128×104·16색·몸 높이 80px, 기준점 (64 또는 63),92. 왼쪽은 오른쪽의 정확한 반전이다. 직립 자세와 기존 Run의 속도·발 궤적·상하 움직임을 유지했다.
- `./.local-tools/python/Scripts/python.exe specs/009-warden-shading-restore/check_restored_run.py`: 종료 0. 실제 gait.json/physics.json은 기존 잠정 승인 Run과 동일하다. 새 그림에 맞춰 부위 연결점과 전류 곡선 6개를 다시 정했다.
- 전류를 끄면 매 프레임 25~45픽셀이 달라진다. 밝은 선두 픽셀을 곡선에 투영해 경로 길이의 약 0.19~0.21 지점에서 약 0.78~0.81 지점으로 진행함을 검사했다.
- 천 7질점의 연결점 변위는 0, 끝의 상대 왕복 범위는 10.015px, 중간/끝의 최대 차이는 6.268px다. 꼬리 끝은 1.609px, 가까운 귀는 0.952px, 먼 귀는 0.812px 왕복한다. 모든 뿌리 변위는 0이며 물리 주기 오차는 1e-14 미만이다. 물리를 끄면 프레임당 340~728픽셀이 달라진다.
- 발 하단 2.6px는 형태를 유지해 이동하고, 위쪽 짧은 연결부만 변형한다. 단독 발 렌더의 바닥 목표 오차는 최대 0.211px, 하단 폭 변화는 각 발 0.25px로 검토 허용치 1px 이내다.
- 모든 프레임의 알파는 8방향 단일 연결 성분(비율 1.0)이고 닫힌 투명 구멍은 0개다. 구멍을 일괄 메우는 후처리는 하지 않았다.
- 0/1 위상 렌더의 정확한 일치, 모든 PNG의 이진 알파·16색·4px 여백·좌우 반전·시트와 프레임 일치·GIF 16프레임/480ms를 검사했다.

## FR-004: 보존

잠정 승인 idle 48개·걷기 48개·Run 32개, 총 128개 PNG를 approval.json 해시와 대조해 모두 일치했다. 지정 수정본의 해시도 일치했다. 기존 잠정 승인 분류를 바꾸지 않고 art 안에 별도 검토본을 만들었다. 게임 코드·assets·의존성은 변경하지 않았다.

## FR-005: 외부 QA·시각 검사·묶음

양방향에 다음 형식으로 실행했다.

`./.local-tools/python/Scripts/python.exe .agents/skills/codeart2d/scripts/pixel_qa.py --input "art/warden/shading-restore/run-review-v1/run_right/frame_*.png" --palette art/warden/shading-restore/run-review-v1/palette.hex --anchor 64,92 --onion --strict --report art/warden/shading-restore/run-review-v1/pixel-qa-right.json`

왼쪽은 run_left와 anchor 63,92 및 pixel-qa-left.json을 사용했다. 두 명령 모두 종료 0, status=pass, failed=[], warned=[]다. loop_seam=1.18, threshold=2.0이다. outline_gaps(value=null, threshold=0)와 l_corners(value=null, threshold=10)는 외곽선 색 미지정으로 skipped이며 통과로 계산하지 않았다.

주 에이전트와 Sol/medium 읽기 전용 담당이 좌우 전체 16프레임 시트를 직접 관찰했다. 귀·팔 비율과 청색 명암, 천이 위로 굽고 뒤로 펴지는 모습, 부착 유지와 둥근 꼬리를 확인했다. 눈에 띄는 분리나 닫힌 가랑이 구멍은 없다. 다리가 겹치는 구간에는 먼발이 작은 돌기처럼 보인다. 매 프레임 원화의 발이 그대로 노출된다고 주장하지 않는다. GIF 재생 리듬과 최종 자연스러움의 판단은 사용자 검토로 남긴다.

[검토 묶음](../../art/warden/shading-restore/run-review-v1/warden-restored-run.zip)은 60개 파일·32개 프레임 PNG이며 CRC 검사를 통과했다. [자동 검사 근거](run-verification.json), [좌우 GIF](../../art/warden/shading-restore/run-review-v1/both.gif), [원화 비율 수정 기록](proportion-verification.md)을 참조한다.

## 범위와 한계

앞서 사용자가 지시한 코드 애니메이션 경로를 유지했다. `route_media.py resolve --kind video`는 no-route를 반환했다. 새 모델 호출은 없으며, 원본 이미지의 미제공 모델/비용 정보는 추정하지 않았다. 천은 2D 질점의 횡변위 근사로 실제 접힘·자체 충돌을 계산하지 않는다. 왼쪽은 조명까지 반전한다. HTML 브라우저 실재생과 게임 실행/통합은 검사하지 않았다. 자동 프레임 검사와 시트 관찰은 사용자 채택을 대신하지 않는다.

## Documentation & Convergence

현재 Run 범위의 FR-001~005가 수정본 입력·렌더·검사·시각 자료·보존·docs에 대응한다. T002~T005/T009를 완료하고 Run 검토 대기로 표시한다. 걷기·공격의 최신 자세 적용은 이번 범위 밖이다. docs/art-direction·progress·색감 검사와 009 spec/plan/tasks/quickstart를 실제 결과로 갱신했다.

최종 문서와 HTML 정적 링크 38개의 파일 존재를 확인했다. `git diff --check`는 종료 0이며 기존 파일의 줄바꿈 안내만 출력됐다.
