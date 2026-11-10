"""프레임워크 공유 값 검사."""

from math import isfinite


def _bounds(value):
    value = tuple(value)
    if (len(value) != 4 or not all(isfinite(v) for v in value) or
            value[0] > value[2] or value[1] > value[3]):
        raise ValueError('bounds는 유한한 (left, bottom, right, top)이어야 합니다.')
    return value


def _opacity(value):
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError('opacity는 유한한 0~1이어야 합니다.')
    return value


def _pair(value):
    value = tuple(value)
    if len(value) != 2 or not all(isfinite(v) for v in value):
        raise ValueError('유한한 좌표 두 개가 필요합니다.')
    return value
