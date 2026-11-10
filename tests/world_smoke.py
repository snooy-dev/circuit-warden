"""실제 월드 창·픽셀·입력·레벨 왕복 검사. 기존 출력 폴더를 인자로 받는다."""

import sys
from ctypes import byref, c_ubyte
from pathlib import Path
from time import monotonic
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pico2d.pico2d as pico
from engine import Engine
from framework_demo import WorldDemo
from game_framework import GameObject, RenderItem, draw_image


def push_button(button, x=320, y=120):
    event = pico.SDL_Event()
    event.type = pico.SDL_MOUSEBUTTONDOWN
    event.button.button, event.button.x, event.button.y = button, x, y
    assert pico.SDL_PushEvent(byref(event)) == 1


def push_key(key):
    event = pico.SDL_Event()
    event.type = pico.SDL_KEYDOWN
    event.key.keysym.sym = key
    assert pico.SDL_PushEvent(byref(event)) == 1


class WorldSmoke(WorldDemo):
    def __init__(self, variant, trace):
        super().__init__(variant)
        self.trace = trace

    def enter(self, engine):
        super().enter(engine)
        self.trace['scenes'].append(self)
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, 2, 2, 32, pico.SDL_PIXELFORMAT_RGBA32)
        assert surface
        try:
            assert pico.SDL_FillRect(surface, None, pico.SDL_MapRGBA(
                surface.contents.format, 0, 255, 255, 128)) == 0
            texture = pico.SDL_CreateTextureFromSurface(pico.renderer, surface)
        finally:
            pico.SDL_FreeSurface(surface)
        assert texture
        fixture = GameObject()
        image = SimpleNamespace(texture=texture)
        bounds = (4, 3, 5, 4)
        fixture.render_items = lambda: (RenderItem(
            lambda transform, opacity: draw_image(image, transform, bounds, opacity),
            4, bounds, opacity=.5),)
        fixture.on_destroy = lambda: pico.SDL_DestroyTexture(texture)
        self.level.spawn(fixture)

    def handle_event(self, event):
        if ((event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_SPACE) or
                (event.type == pico.SDL_MOUSEBUTTONDOWN and event.button == pico.SDL_BUTTON_MIDDLE)):
            self.engine.change_scene(WorldSmoke(1 - self.variant, self.trace))
        else:
            super().handle_event(event)

    def update(self, dt):
        super().update(dt)
        now, trace, app = monotonic(), self.trace, self.engine
        assert now - trace['started'] < 20, f"월드 검사 시간 초과: {trace['stage']}"
        if now - trace['changed'] < .4:
            return
        stage = trace['stage']
        print('world', stage, self.variant, app.window_size, app.output_size, flush=True)
        if stage == 0:
            assert len(self.level.objects) == 5
            push_button(pico.SDL_BUTTON_LEFT)
        elif stage == 1:
            assert len(self.level.objects) == 6
            obj = self.level.objects[-1]
            assert abs(obj.y - 2.5) < .01 and obj.x > 0
            push_button(pico.SDL_BUTTON_RIGHT)
        elif stage == 2:
            assert len(self.level.objects) == 5
            self.level.mode.speed = 12
        elif stage == 3:
            mover = self.level.objects[2]
            assert -6 < mover.x < 0
            assert 'boundary-entry' in trace['saved']
            self.level.mode.speed = 0
            trace['positions'] = [(o.x, o.y) for o in self.level.objects[:4]]
            push_key(pico.SDLK_RIGHT)
        elif stage == 4:
            assert self.camera_center == (2, 0)
            app.set_display(window_size=(960, 540))
        elif stage == 5:
            assert app.window_size == (960, 540)
            assert [(o.x, o.y) for o in self.level.objects[:4]] == trace['positions']
            assert self.transform.inverse(*self.transform.point(1, 2)) == (1, 2)
            app.set_display(fullscreen=True)
        elif stage == 6:
            assert app.fullscreen and app.output_valid
            app.set_display(fullscreen=False)
        elif stage == 7:
            assert not app.fullscreen and app.window_size == (960, 540)
            trace['old'] = self.level.objects
            push_key(pico.SDLK_SPACE)
        elif stage == 8:
            assert self.variant == 1 and self.level.mode.speed == -2
            assert all(o.level is None for o in trace['old'])
            assert len(self.level.objects) == 5
            push_button(pico.SDL_BUTTON_MIDDLE)
        elif stage == 9:
            assert self.variant == 0 and self.level.mode.speed == 2
            assert len(self.level.objects) == 5
            assert 'level-B' in trace['saved'] and 'return-A' in trace['saved']
            app.stop()
            trace['passed'] = True
            print('PASS: world/alpha/image/culling/input/camera/resize/fullscreen/roundtrip', flush=True)
        trace['stage'] += 1
        trace['changed'] = now

    def pixel(self, x, y):
        px, py = self.transform.point(x, y)
        rgba = (c_ubyte * 4)()
        rect = pico.SDL_Rect(int(px), int(py), 1, 1)
        assert pico.SDL_RenderReadPixels(pico.renderer, rect, pico.SDL_PIXELFORMAT_RGBA32,
                                         rgba, 4) == 0
        return tuple(rgba)[:3]

    def capture(self, name):
        trace = self.trace
        if name in trace['saved']:
            return
        width, height = self.engine.output_size
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, width, height, 32, pico.SDL_PIXELFORMAT_RGBA32)
        assert surface
        try:
            assert pico.SDL_RenderReadPixels(pico.renderer, None, pico.SDL_PIXELFORMAT_RGBA32,
                surface.contents.pixels, surface.contents.pitch) == 0
            target = trace['output'] / f'p3-{name}.png'
            assert pico.IMG_SavePNG(surface, str(target).encode()) == 0
            trace['saved'].add(name)
        finally:
            pico.SDL_FreeSurface(surface)

    def draw(self):
        super().draw()
        trace = self.trace
        if trace['stage'] == 0:
            assert all(abs(a - b) <= 2 for a, b in zip(self.pixel(0, .6), (135, 80, 140)))
            assert self.pixel(0, 0) == (255, 215, 50)
            assert self.pixel(-6.5, 2.8) == (170, 80, 200)
            image_rgb = self.pixel(4.5, 3.5)
            assert all(abs(a - b) <= 2 for a, b in zip(image_rgb, (150, 214, 221))), image_rgb
            self.capture('initial')
        mover = self.level.objects[2]
        if trace['stage'] == 3 and -6 < mover.x < -1:
            rgb = self.pixel(mover.x, -3)
            assert all(abs(a - b) <= 2 for a, b in zip(rgb, (95, 207, 133))), (mover.x, rgb)
            self.capture('boundary-entry')
        if self.camera_center == (2, 0):
            self.capture('camera-shift')
        if self.engine.window_size == (960, 540) and not self.engine.fullscreen:
            self.capture('resized')
        if self.engine.fullscreen:
            self.capture('fullscreen')
        if self.variant == 1:
            self.capture('level-B')
        if len(trace['scenes']) == 3:
            self.capture('return-A')


if __name__ == '__main__':
    output = Path(sys.argv[1]).resolve()
    assert output.is_dir(), '기존 출력 폴더를 지정해야 합니다.'
    trace = dict(started=monotonic(), changed=monotonic(), stage=0,
                 scenes=[], saved=set(), output=output, passed=False)
    Engine(640, 480).run(WorldSmoke(0, trace))
    assert trace['passed'] and len(trace['scenes']) == 3
    assert all(scene.engine is None and not scene.level.objects and
               not scene.renderer.world_items for scene in trace['scenes'])
