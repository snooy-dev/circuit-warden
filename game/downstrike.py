"""공중 아래 베기의 타이밍과 발밑 방전 표시."""

from game_framework import GameObject, RenderItem, draw_rect


WINDUP = .065
ACTIVE_END = .155
DURATION = .245
BOUNCE_SPEED = 550
REACH = 76
HALF_WIDTH = 27
BURST_DURATION = .12


def draw_blade(transform, feet, elapsed, opacity):
    x, y = feet
    if elapsed < WINDUP:
        opacity *= elapsed / WINDUP
        draw_rect(transform, (x - 4, y - 10, x + 4, y - 3), (110, 232, 255), opacity)
        return
    if elapsed >= ACTIVE_END:
        opacity *= max(0, (DURATION - elapsed) / (DURATION - ACTIVE_END))
    for top, bottom, offset, width in ((2, 21, -5, 11), (21, 42, 1, 10),
                                       (42, 63, -2, 8), (63, REACH, -7, 5)):
        draw_rect(transform, (x + offset - width, y - bottom, x + offset + width, y - top),
                  (27, 147, 247), opacity * .62)
        draw_rect(transform, (x + offset - 2, y - bottom, x + offset + 2, y - top),
                  (201, 252, 255), opacity)
    draw_rect(transform, (x - 25, y - 30, x - 12, y - 26), (89, 231, 255), opacity)
    draw_rect(transform, (x + 11, y - 50, x + 22, y - 46), (89, 231, 255), opacity)


class DownstrikeBurst(GameObject):
    def __init__(self, position):
        super().__init__()
        self.position = position
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= BURST_DURATION:
            self.destroy()

    def _draw(self, transform, opacity):
        x, y = self.position
        progress = self.elapsed / BURST_DURATION
        spread = 8 + 25 * progress
        for dx, dy in ((-1, .15), (1, .15), (-.65, .65), (.65, .65), (0, .9)):
            px, py = x + spread * dx, y + spread * dy
            draw_rect(transform, (px - 4, py - 2, px + 4, py + 2),
                      (155, 244, 255), opacity * (1 - progress))

    def render_items(self):
        return (RenderItem(self._draw, draw_order=1),)
