"""수집된 항목의 안정 정렬과 그리기 실행. 소유·수집·정리는 호출자 책임이다."""


def execute(items, draw, *, key=None):
    if key is not None:
        items.sort(key=key)
    for item in items:
        draw(item)
