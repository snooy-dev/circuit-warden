# Verification: 기본 게임플레이

상태: US1 모드·A/D 연결 검증 완료, US2 공격 구현 예정.

## Analyze

FR-001→T001, FR-002/003→T003/004, FR-004/005→T006~009, FR-006→T007/008, FR-DOC→T002/005/010/011. 7개 요구·두 흐름·헌법 대조에서 차단 충돌/누락 없음. requirements checklist 7개 충족. 확장 hooks 파일 없음. 별도 계획 승인으로 표시하지 않는다.

## US1

명령: `.\.venv\Scripts\python.exe -B -m unittest tests.unit.test_character tests.integration.test_character_scene.CharacterSceneTests.test_gameplay_mode_delivers_once_and_keeps_player_reference -v` → **7개 통과**.

A/D 유지·상쇄·해제·시간 분할·포커스 정리·경계·방향 출력을 확인했다. 구체 모드에서 control 호출이 정확히 1회이며 다른 객체를 추가해도 player 참조가 유지된다. engine/game_framework는 수정하지 않았다. 실제 창은 공격 증분에서 함께 확인할 예정이다.

systems/basic-gameplay·game-design에 사용자 규칙, architecture에 입력 소유, progress에 활성 범위를 반영했다. README의 최종 조작 안내는 공격 구현 후 갱신한다. 모든 요구 완료를 뜻하지 않는다.
