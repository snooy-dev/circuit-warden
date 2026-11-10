"""월드·UI 논리 좌표와 출력 픽셀 변환."""

from dataclasses import dataclass
from math import isfinite

from ._validation import _pair


@dataclass(frozen=True)
class WorldTransform:
    """월드 y 위 방향과 출력 픽셀 y 아래 방향 사이의 직교 변환."""

    viewport: tuple
    center: tuple = (0, 0)
    view_height: float = 10

    def __post_init__(self):
        viewport, center = tuple(self.viewport), tuple(self.center)
        if (len(viewport) != 4 or not all(isfinite(v) for v in viewport) or
                min(viewport[2:]) < 0 or len(center) != 2 or
                not all(isfinite(v) for v in center) or
                not isfinite(self.view_height) or self.view_height <= 0):
            raise ValueError('카메라·viewport 값은 유한하고 시야는 양수여야 합니다.')
        object.__setattr__(self, 'viewport', viewport)
        object.__setattr__(self, 'center', center)

    @property
    def valid(self):
        return min(self.viewport[2:]) > 0

    @property
    def scale(self):
        return self.viewport[3] / self.view_height

    @property
    def bounds(self):
        if not self.valid:
            return None
        half_width = self.view_height * self.viewport[2] / self.viewport[3] / 2
        cx, cy = self.center
        return (cx - half_width, cy - self.view_height / 2,
                cx + half_width, cy + self.view_height / 2)

    def point(self, x, y):
        if not self.valid:
            return None
        vx, vy, vw, vh = self.viewport
        return (vx + vw / 2 + (x - self.center[0]) * self.scale,
                vy + vh / 2 - (y - self.center[1]) * self.scale)

    def inverse(self, x, y):
        if not self.valid:
            return None
        vx, vy, vw, vh = self.viewport
        return (self.center[0] + (x - vx - vw / 2) / self.scale,
                self.center[1] - (y - vy - vh / 2) / self.scale)

    def length(self, value):
        return value * self.scale


@dataclass(frozen=True)
class UITransform:
    """좌상단 UI 논리 좌표와 실제 출력 픽셀의 균등 변환."""

    viewport: tuple
    reference_size: tuple

    def __post_init__(self):
        viewport, reference = tuple(self.viewport), _pair(self.reference_size)
        if (len(viewport) != 4 or not all(isfinite(v) for v in viewport) or
                min(viewport[2:]) < 0 or min(reference) <= 0):
            raise ValueError('viewport는 유한한 비음수 크기, reference_size는 양수여야 합니다.')
        object.__setattr__(self, 'viewport', viewport)
        object.__setattr__(self, 'reference_size', reference)

    @property
    def valid(self):
        return min(self.viewport[2:]) > 0

    @property
    def scale(self):
        return min(self.viewport[2] / self.reference_size[0],
                   self.viewport[3] / self.reference_size[1])

    @property
    def logical_size(self):
        if not self.valid:
            return None
        return self.viewport[2] / self.scale, self.viewport[3] / self.scale

    @property
    def bounds(self):
        size = self.logical_size
        return None if size is None else (0, 0, *size)

    def point(self, x, y):
        if not self.valid:
            return None
        return self.viewport[0] + x * self.scale, self.viewport[1] + y * self.scale

    def inverse(self, x, y):
        if not self.valid:
            return None
        return (x - self.viewport[0]) / self.scale, (y - self.viewport[1]) / self.scale

    def length(self, value):
        return value * self.scale
