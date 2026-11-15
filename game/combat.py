"""양방향 전투의 접촉 판정."""

from math import inf

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
