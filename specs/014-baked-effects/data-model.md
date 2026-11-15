# Data Model

- 전하 manifest: steps=32, count=72, 프레임 crop 크기·pivot·시트 경로. 24fps는 런타임 상수다. value는0~1 연속 유지, 표시 index=floor(value*steps+0.5).
- 전류 manifest: count=12, seed=7, 길이별 sheet·cell·중앙대칭 crop. 수명0.1초는 기존 코드 유지.
- 이미지: 장면 ImageStore 소유, 효과는 참조만 보관. 종료 때 참조 제거 뒤 저장소 해제.
