"""게임 좌표와 값 검사를 제공하는 공개 그리기 API."""

from engine.rendering import drawing as backend

from ._validation import _bounds, _opacity


def _output_rect(transform, bounds):
    left, bottom, right, top = _bounds(bounds)
    x1, y1 = transform.point(left, top)
    x2, y2 = transform.point(right, bottom)
    return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)


def draw_rect(transform, bounds, color, opacity=1):
    """게임 좌표의 채운 사각형을 그린다."""
    _opacity(opacity)
    if len(color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in color):
        raise ValueError('색상은 0~255 RGB 정수 세 개여야 합니다.')
    if transform.valid:
        backend.draw_rect(_output_rect(transform, bounds), color, opacity)


def draw_image(image, transform, bounds, opacity=1):
    """호출자가 소유하는 Pico2D Image를 게임 좌표에 그린다."""
    _opacity(opacity)
    if transform.valid:
        rect = _output_rect(transform, bounds)
        backend.draw_image(image.texture, rect, opacity)
