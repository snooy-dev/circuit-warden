"""통합·월드 전용·독립 UI의 좌표·수명·뎁스·알파 검사 화면."""

import argparse

import pico2d.pico2d as pico

from engine import Engine, Scene
from game_framework import GameMode, GameObject, Level, LevelScene, RenderItem, draw_rect, Canvas, UIElement, Renderer


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
            self.engine.change_scene(type(self)(1 - self.variant))
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



class UIBlock(UIElement):
    def __init__(self, color, width, height, **kwargs):
        super().__init__(bounds=(0, 0, width, height), **kwargs)
        self.color = color

    def draw(self, origin, transform, opacity):
        x, y = origin
        left, top, right, bottom = self.bounds
        draw_rect(transform, (x + left, y + top, x + right, y + bottom), self.color, opacity)


class UIDemo(Scene):
    """Level·GameMode 없이 Canvas만 검사하는 장면."""

    def __init__(self):
        self.engine = self.canvas = None
        self.renderer = Renderer()
        self._reset_generation = None

    @property
    def transform(self):
        viewport = self.engine.viewport if self.engine.output_valid else (0, 0, 0, 0)
        return self.canvas.transform(viewport)

    def enter(self, engine):
        self.engine, self._reset_generation = engine, engine.reset_generation
        self.canvas = Canvas((800, 600))
        self.back = self.canvas.add(UIBlock((220, 60, 50), 280, 220, x=50, y=90))
        self.child = self.canvas.add(UIBlock((255, 215, 50), 230, 130,
                                           x=140, y=50, draw_order=999), self.back)
        self.front = self.canvas.add(UIBlock((50, 100, 230), 280, 220,
                                            x=250, y=190, draw_order=1, opacity=.5))
        self.front_child = self.canvas.add(UIBlock((50, 210, 100), 90, 60,
                                                   x=30, y=100), self.front)
        self.corner = self.canvas.add(UIBlock((170, 80, 200), 60, 30,
                                             x=-80, y=20, anchor=(1, 0), draw_order=2))
        outside = self.canvas.add(UIBlock((220, 60, 50), 30, 30, x=-200, y=450))
        self.canvas.add(UIBlock((50, 210, 100), 50, 50, x=220), outside)
        self.pointer = self.canvas.add(UIBlock((255, 255, 255), 8, 8,
                                              visible=False, draw_order=10))
        title = ('UI | arrows move parent, H hide, Delete subtree, D order, R reset, '
                 'mouse position, F6 size, F11 fullscreen, Esc quit')
        pico.SDL_SetWindowTitle(pico.window, title.encode('utf-8'))

    def event_to_ui(self, event):
        point = self.engine.event_to_output(event)
        return None if point is None else self.transform.inverse(*point)

    def handle_event(self, event):
        if event.type == pico.SDL_RENDER_DEVICE_RESET:
            raise RuntimeError('렌더 리셋으로 그리기 자원을 다시 만들어야 합니다.')
        if event.type == pico.SDL_RENDER_TARGETS_RESET:
            self._reset_generation += 1
        elif event.type == pico.SDL_MOUSEMOTION:
            point = self.event_to_ui(event)
            if point is not None:
                self.pointer.x, self.pointer.y = point
                self.pointer.visible = True
        elif event.type == pico.SDL_KEYDOWN:
            if event.key == pico.SDLK_F11:
                self.engine.set_display(fullscreen=not self.engine.fullscreen)
            elif event.key == pico.SDLK_F6:
                size = (960, 540) if self.engine.window_size != (960, 540) else (800, 600)
                self.engine.set_display(window_size=size)
            elif event.key == pico.SDLK_r:
                self.engine.change_scene(UIDemo())
            elif self.back.canvas is self.canvas:
                if event.key == pico.SDLK_h:
                    self.back.visible = not self.back.visible
                elif event.key == pico.SDLK_DELETE:
                    self.canvas.remove(self.back)
                elif event.key == pico.SDLK_d:
                    self.back.draw_order = 2 if self.back.draw_order == 0 else 0
                elif event.key in (pico.SDLK_LEFT, pico.SDLK_RIGHT, pico.SDLK_UP, pico.SDLK_DOWN):
                    self.back.x += 20 * ((event.key == pico.SDLK_RIGHT) - (event.key == pico.SDLK_LEFT))
                    self.back.y += 20 * ((event.key == pico.SDLK_DOWN) - (event.key == pico.SDLK_UP))

    def update(self, dt):
        self.canvas.update(dt)

    def draw(self):
        if self.engine.reset_generation != self._reset_generation:
            raise RuntimeError('렌더 리셋으로 그리기 자원을 다시 만들어야 합니다.')
        self.renderer.draw_ui(self.canvas, self.transform)

    def exit(self):
        try:
            self.renderer.ui_items.clear()
            if self.canvas is not None:
                self.canvas.close()
        finally:
            self.engine = None


class FrameworkDemo(WorldDemo):
    """기존 월드 검사와 화면 고정 UI를 같은 LevelScene에 연결한다."""

    def __init__(self, variant=0):
        super().__init__(variant)
        self.canvas = Canvas((800, 600))
        self.panel = self.canvas.add(UIBlock((20, 140, 80), 180, 130,
                                            x=280, y=220, opacity=.5))
        self.child = self.canvas.add(UIBlock((255, 215, 50), 100, 45,
                                            x=20, y=20, draw_order=999), self.panel)
        self.front = self.canvas.add(UIBlock((100, 70, 210), 170, 110,
                                            x=370, y=280, draw_order=1, opacity=.5))
        self.corner = self.canvas.add(UIBlock((170, 80, 200), 60, 30,
                                             x=-80, y=20, anchor=(1, 0), draw_order=2))
        self.pointer = self.canvas.add(UIBlock((255, 255, 255), 8, 8,
                                              visible=False, draw_order=10))

    def enter(self, engine):
        super().enter(engine)
        title = (f'Integrated {"A" if self.variant == 0 else "B"} | '
                 'LMB/RMB world add/remove, Space/MMB level, arrows camera, D depth, '
                 'H hide UI, Delete UI subtree, F6 size, F11 fullscreen, Esc quit')
        pico.SDL_SetWindowTitle(pico.window, title.encode('utf-8'))

    def handle_event(self, event):
        if event.type == pico.SDL_MOUSEMOTION:
            point = self.event_to_ui(event)
            if point is not None:
                self.pointer.x, self.pointer.y = point
                self.pointer.visible = True
        elif event.type == pico.SDL_KEYDOWN:
            if event.key == pico.SDLK_h and self.panel.canvas is self.canvas:
                self.panel.visible = not self.panel.visible
            elif event.key == pico.SDLK_DELETE:
                self.canvas.remove(self.panel)
        super().handle_event(event)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--ui', action='store_true', help='Level 없는 UI 단독 검사')
    modes.add_argument('--world', action='store_true', help='Canvas 없는 월드 전용 검사')
    args = parser.parse_args()
    Engine().run(UIDemo() if args.ui else WorldDemo() if args.world else FrameworkDemo())
