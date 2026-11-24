"""전원 구역의 팬 기동부터 조작 인계까지 이어지는 연출."""

from game_framework import (
    Button, ButtonInput, Canvas, SpritePlayer, draw_rect, draw_sprite,
)

from .title import MENU_FONT


SPARK_AT = .95
STRIKE_AT = 1.72
HANDOFF_AT = 2.85
CLOSE_VIEW = 420


def _ease(time, start, end):
    progress = min(1, max(0, (time - start) / (end - start)))
    return progress * progress * (3 - 2 * progress)


class PowerOpening:
    def __init__(self, level, reference_size):
        self.level = level
        self.elapsed = 0.0
        self.skipped = False
        self.spark = SpritePlayer(level.combat_clips['hit_spark'])
        self.canvas = Canvas(reference_size)
        self.input = ButtonInput(self.canvas)
        self.canvas.add(Button('Skip  [Esc]', self.skip, anchor=(1, 1), x=-122, y=-49,
                               width=113, height=44, size=24, color=(151, 212, 207),
                               font_path=MENU_FONT))
        for charge in level.charges:
            charge.spawn_opacity = 0.0

    def skip(self):
        self.skipped = True

    def update(self, dt):
        level = self.level
        last = self.elapsed
        self.elapsed = t = min(HANDOFF_AT, last + dt)
        fan_speed = (_ease(t, .12, .76) * (1 - _ease(t, SPARK_AT, 1.22))
                     + _ease(t, 1.80, 2.75))
        level.layout.update((t - last) * fan_speed)
        self.spark.update(max(0, t - SPARK_AT) - max(0, last - SPARK_AT))

        strike_dt = max(0, t - STRIKE_AT) - max(0, last - STRIKE_AT)
        if strike_dt and level.power_entry_effect is not None:
            level.power_entry_effect.update(strike_dt)
            level._update_power_entry()
        for charge in level.charges:
            charge.spawn_opacity = _ease(t, 2.08, 2.65)
            charge.update(strike_dt)
        return t >= HANDOFF_AT

    def camera(self, gameplay_center, gameplay_view, aspect):
        layout = self.level.layout
        cable_x, cable_y = layout.power_entry
        left = layout.bounds[0]
        close_x = max(cable_x + 60, left + CLOSE_VIEW * aspect / 2)
        progress = _ease(self.elapsed, .24, 2.68)
        if progress == 1:
            return gameplay_center, gameplay_view
        close_y = cable_y - 126
        x, y = gameplay_center
        return ((close_x + (x - close_x) * progress, close_y + (y - close_y) * progress),
                CLOSE_VIEW + (gameplay_view - CLOSE_VIEW) * progress)

    def draw(self, world):
        t = self.elapsed
        ui = self.canvas.transform(world.viewport)
        _, _, width, height = ui.bounds
        darkness = (1 - .70 * _ease(t, 0, .56)
                    + .39 * _ease(t, SPARK_AT, 1.22)
                    - .69 * _ease(t, 1.66, 2.50))
        draw_rect(ui, ui.bounds, (0, 0, 0), max(0, darkness))
        if t >= SPARK_AT and not self.spark.finished:
            frame = self.spark.frame
            draw_sprite(frame, world, self.level.layout.power_entry,
                        (frame.rect[2] * .75, frame.rect[3] * .75))
        bar = height * .094 * (1 - _ease(t, 1.87, HANDOFF_AT))
        if bar:
            draw_rect(ui, (0, 0, width, bar), (0, 0, 0))
            draw_rect(ui, (0, height - bar, width, height), (0, 0, 0))

    def close(self):
        if self.level.power_entry_effect is not None:
            self.level.finish_power_entry()
        for charge in self.level.charges:
            charge.spawn_opacity = 1.0
        self.input.reset()
        self.canvas.close()
