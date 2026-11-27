"""게임 좌표와 값 검사를 제공하는 공개 그리기 API."""

from math import isfinite

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


def draw_horizontal_gradient(transform, bounds, color, *, left_opacity, right_opacity):
    """같은 색의 알파를 좌우로 보간해 그린다."""
    _opacity(left_opacity)
    _opacity(right_opacity)
    if transform.valid:
        backend.draw_horizontal_gradient(
            _output_rect(transform, bounds), color, left_opacity, right_opacity)


def _image_source(image, source):
    source = tuple(source)
    if len(source) != 4 or any(type(value) is not int for value in source):
        raise ValueError('source는 정수 left/top/width/height여야 합니다.')
    left, top, width, height = source
    if (min(left, top) < 0 or min(width, height) <= 0 or
            left + width > image.w or top + height > image.h):
        raise ValueError('source 영역은 이미지 안의 양수 크기여야 합니다.')
    return source


def draw_image(image, transform, bounds, opacity=1, *, source=None, flip_x=False, angle=0):
    """호출자가 소유하는 Pico2D Image의 전체 또는 지정 영역을 논리 좌표에 그린다."""
    _opacity(opacity)
    if not isfinite(angle):
        raise ValueError('angle은 유한한 출력 시계방향 각도여야 합니다.')
    if type(flip_x) is not bool:
        raise TypeError('flip_x는 bool이어야 합니다.')
    if flip_x and source is None:
        source = (0, 0, image.w, image.h)
    if source is not None:
        source = _image_source(image, source)
    if not transform.valid:
        return
    rect = _output_rect(transform, bounds)
    if angle:
        backend.draw_image(image.texture, rect, opacity, source=source, flip_x=flip_x, angle=angle)
    elif source is None:
        backend.draw_image(image.texture, rect, opacity)
    else:
        backend.draw_image(image.texture, rect, opacity, image=image, source=source, flip_x=flip_x)
