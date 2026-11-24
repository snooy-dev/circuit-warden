"""로컬 AABB, 레이어 응답, 연속 접촉 판정."""

from dataclasses import dataclass
from enum import IntEnum
from math import inf


TIME_EPSILON = 1e-9
CONTACT_EPSILON = 1e-9


class CollisionResponse(IntEnum):
    IGNORE = 0
    OVERLAP = 1
    BLOCK = 2


@dataclass(frozen=True)
class Collider:
    bounds: tuple[float, float, float, float]
    layer: str
    blocks: frozenset[str] = frozenset()
    overlaps: frozenset[str] = frozenset()

    def __post_init__(self):
        left, bottom, right, top = self.bounds
        if not (left < right and bottom < top):
            raise ValueError('콜라이더에는 양의 면적이 필요합니다.')
        object.__setattr__(self, 'bounds', (left, bottom, right, top))
        object.__setattr__(self, 'blocks', frozenset(self.blocks))
        object.__setattr__(self, 'overlaps', frozenset(self.overlaps))
        if self.blocks & self.overlaps:
            raise ValueError('레이어당 한 가지 충돌 응답이 필요합니다.')

    def _response(self, layer):
        if layer in self.blocks:
            return CollisionResponse.BLOCK
        if layer in self.overlaps:
            return CollisionResponse.OVERLAP
        return CollisionResponse.IGNORE

    def response_to(self, other):
        return min(self._response(other.layer), other._response(self.layer))

    def bounds_at(self, position):
        x, y = position
        left, bottom, right, top = self.bounds
        return left + x, bottom + y, right + x, top + y

    def overlap_contact(self, other, position, other_position, times, movement, window=(0, inf)):
        if self.response_to(other) != CollisionResponse.OVERLAP:
            return None
        start, end = times
        window_start, window_end = window
        first, last = max(start, window_start), min(end, window_end)
        if first > last or first >= window_end - TIME_EPSILON:
            return None
        duration = end - start
        moving, fixed = self.bounds_at(position), other.bounds_at(other_position)
        interval = _sweep_interval(moving, fixed, movement if duration else (0, 0))
        if interval is None:
            return None
        enter, leave = interval
        if duration:
            enter, leave = start + duration * enter, start + duration * leave
        if enter >= min(last, leave) - TIME_EPSILON or leave <= first + TIME_EPSILON:
            return None
        return max(first, enter)


def overlaps(moving, fixed):
    return all(moving[axis] < fixed[axis + 2] and fixed[axis] < moving[axis + 2]
               for axis in range(2))


def blocking_contact(moving, fixed, movement):
    interval = _sweep_interval(moving, fixed, movement)
    if interval is not None:
        enter, leave = interval
        # 기존 침투는 배치 단계의 책임이다. 여기서는 새 침투만 막는다.
        distance = max(map(abs, movement))
        if distance and -CONTACT_EPSILON <= enter * distance <= distance + CONTACT_EPSILON and enter < leave:
            return min(1, max(0, enter))
    return None


def _sweep_interval(moving, fixed, movement):
    enter, leave = -inf, inf
    for axis, delta in enumerate(movement):
        low, high = moving[axis], moving[axis + 2]
        other_low, other_high = fixed[axis], fixed[axis + 2]
        if delta == 0:
            if low >= other_high or other_low >= high:
                return None
            continue
        a, b = (other_low - high) / delta, (other_high - low) / delta
        enter, leave = max(enter, min(a, b)), min(leave, max(a, b))
    return enter, leave
