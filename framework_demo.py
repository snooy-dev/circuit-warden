"""에셋·Canvas 없이 월드 좌표·수명·뎁스·알파를 검사하는 화면."""

import pico2d.pico2d as pico

from engine import Engine
from game_framework import GameMode, GameObject, Level, LevelScene, RenderItem, draw_rect


class Block(GameObject):
    def __init__(self, x, y, color, *, order=0, opacity=1, width=3, height=3,
                 moving=False, weapon=False):
        super().__init__()
        self.x, self.y, self.color = x, y, color
        self.draw_order, self.opacity = order, opacity
        self.width, self.height = width, height
        self.moving, self.weapon = moving, weapon

    @property
    def bounds(self):
        return (self.x - self.width / 2, self.y - self.height / 2,
                self.x + self.width / 2, self.y + self.height / 2)

    @property
    def weapon_bounds(self):
        return self.x - .2, self.y - .15, self.x + 2.5, self.y + .15

    def update(self, dt):
        if self.moving:
            self.x += self.level.mode.speed * dt
            if self.x > 14:
                self.x = -14
            elif self.x < -14:
                self.x = 14

    def _draw_body(self, transform, opacity):
        draw_rect(transform, self.bounds, self.color, opacity)

    def _draw_weapon(self, transform, opacity):
        draw_rect(transform, self.weapon_bounds, (255, 215, 50), opacity)

    def render_items(self):
        yield RenderItem(self._draw_body, self.draw_order, self.bounds, opacity=self.opacity)
        if self.weapon:
            yield RenderItem(self._draw_weapon, self.draw_order + 2, self.weapon_bounds)


class DemoMode(GameMode):
    def __init__(self, speed):
        super().__init__()
        self.speed = speed


class DemoLevel(Level):
    def __init__(self, variant=0):
        self.variant = variant
        super().__init__(DemoMode(2 if variant == 0 else -2))

    def on_open(self):
        self.spawn(Block(-1, 0, (220, 60, 50), weapon=True))
        self.spawn(Block(1, 0, (50, 100, 230), order=1, opacity=.5))
        self.spawn(Block(-10 if self.variant == 0 else 10, -3, (50, 210, 100),
                         order=2, opacity=.7, width=1, height=1, moving=True))
        self.spawn(Block(-8, 2.8, (170, 80, 200), width=4, height=1.5))


class WorldDemo(LevelScene):
    def __init__(self, variant=0):
        super().__init__(DemoLevel(variant))
        self.variant = variant

    def enter(self, engine):
        super().enter(engine)
        title = (f'World {"A" if self.variant == 0 else "B"} | LMB add, RMB remove, '
                 'Space/MMB level, arrows camera, D depth, F6 size, F11 fullscreen, Esc quit')
        pico.SDL_SetWindowTitle(pico.window, title.encode('utf-8'))

    def handle_event(self, event):
        if ((event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_SPACE) or
                (event.type == pico.SDL_MOUSEBUTTONDOWN and event.button == pico.SDL_BUTTON_MIDDLE)):
            self.engine.change_scene(WorldDemo(1 - self.variant))
            return
        if event.type == pico.SDL_MOUSEBUTTONDOWN:
            point = self.event_to_world(event)
            if point is not None and event.button == pico.SDL_BUTTON_LEFT:
                self.level.spawn(Block(*point, (240, 160, 50), order=1, opacity=.6,
                                       width=1, height=1, moving=True))
            elif event.button == pico.SDL_BUTTON_RIGHT and self.level.objects:
                self.level.objects[-1].destroy()
        elif event.type == pico.SDL_KEYDOWN:
            if event.key == pico.SDLK_F11:
                self.engine.set_display(fullscreen=not self.engine.fullscreen)
            elif event.key == pico.SDLK_F6:
                size = (960, 540) if self.engine.window_size != (960, 540) else (800, 600)
                self.engine.set_display(window_size=size)
            elif event.key == pico.SDLK_d and self.level.objects:
                obj = self.level.objects[0]
                obj.draw_order = (obj.draw_order + 1) % 3
            elif event.key in (pico.SDLK_LEFT, pico.SDLK_RIGHT, pico.SDLK_UP, pico.SDLK_DOWN):
                x, y = self.camera_center
                self.camera_center = (x + 2 * ((event.key == pico.SDLK_RIGHT) -
                                             (event.key == pico.SDLK_LEFT)),
                                      y + 2 * ((event.key == pico.SDLK_UP) -
                                               (event.key == pico.SDLK_DOWN)))
        super().handle_event(event)


if __name__ == '__main__':
    Engine().run(WorldDemo())
