# Data Model

- Character: buffered_action/buffer_remaining은 마지막 예약 하나다. 허용 행동은 지역값으로 전달하고 세 *_requested 플래그는 제거한다. Machine·점프/대시 단계는 유지한다.
- Display: 현재 표시와 다음 요청을 구분한다. 입력은 현재 표시, update/draw는 적용 완료 표시를 사용한다.
- ChargeArt: 실제 PNG 바이트는 유지한다. 캐시된 합성 데이터는 premultiplied float64 배열이며 캐시 상한16·종료 해제를 유지한다.
- Level/Canvas: 내부 전달 실패에서도 snapshot 참조를 해제한다. 실패 콜백 자체의 traceback은 보존한다.
