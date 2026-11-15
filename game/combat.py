"""양방향 전투의 판정과 체력 표시."""

from math import inf

from game_framework import draw_rect


TIME_EPSILON = 1e-9


def first_contact(moving, fixed, times, movement, window=(0, inf)):
    start, end = times
    window_start, window_end = window
    first, last = max(start, window_start), min(end, window_end)
    if first > last or first >= window_end - TIME_EPSILON:
        return None

    enter, leave = -inf, inf
    duration = end - start
    for axis, delta in enumerate(movement):
        low, high = moving[axis], moving[axis + 2]
        other_low, other_high = fixed[axis], fixed[axis + 2]
        if delta == 0 or duration == 0:
            if low >= other_high or other_low >= high:
                return None
            continue
        a = start + duration * (other_low - high) / delta
        b = start + duration * (other_high - low) / delta
        enter = max(enter, min(a, b))
        leave = min(leave, max(a, b))

    # 공간 경계에 닿기만 하는 경우에는 겹치는 면적이 없다.
    if enter >= min(last, leave) - TIME_EPSILON or leave <= first + TIME_EPSILON:
        return None
    return max(first, enter)


def draw_health(transform, x, y, fraction, color, opacity):
    left = x - 25
    draw_rect(transform, (left - 2, y - 2, left + 52, y + 7), (28, 30, 38), opacity)
    if fraction > 0:
        draw_rect(transform, (left, y, left + 50 * fraction, y + 5), color, opacity)
