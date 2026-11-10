# Data Model

- Source: 원화/측면 이미지 경로와 SHA-256, 생성 출처.
- RestoredMaster: 편집 원본, 원본좌표에 정합한 RGB와 기존 알파, 변환 기록.
- ReviewClip: 기존 프레임 수·시간·anchor·알파·물리·전류와 새 RGB, review-only 상태.
- Verification: 기존128PNG 보존, 알파/타이밍/물리/전류 비교, 색통계·시각판정.
