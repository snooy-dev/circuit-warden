"""실제 통합 창·SDL 입력·픽셀·출력 변경·복합 수명 검사."""

import sys
from ctypes import byref, c_ubyte
from pathlib import Path
from time import monotonic
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pico2d.pico2d as pico
from engine import Engine
from framework_demo import FrameworkDemo
from world_smoke import push_button, push_key


class IntegrationSmoke(FrameworkDemo):
    def __init__(self, variant, trace):
        super().__init__(variant)
        self.trace = trace
        self.child.update = lambda dt: trace.__setitem__('child_ticks', trace['child_ticks'] + 1)

    def enter(self, engine):
        super().enter(engine)
        if not self.trace['scenes']:
            self.trace['changed'] = monotonic()
        self.trace['scenes'].append(self)

    def handle_event(self, event):
        if ((event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_SPACE) or
                (event.type == pico.SDL_MOUSEBUTTONDOWN and event.button == pico.SDL_BUTTON_MIDDLE)):
            self.engine.change_scene(IntegrationSmoke(1 - self.variant, self.trace))
        else:
            super().handle_event(event)

    def pixel(self, transform, x, y):
        px, py = transform.point(x, y)
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
            assert pico.IMG_SavePNG(surface, str(trace['output'] / f'p5-{name}.png').encode()) == 0
            trace['saved'].add(name)
        finally:
            pico.SDL_FreeSurface(surface)

    def update(self, dt):
        super().update(dt)
        now, trace, app = monotonic(), self.trace, self.engine
        assert now - trace['started'] < 40, f"통합 검사 시간 초과: {trace['stage']}"
        if now - trace['changed'] < .4:
            return
        stage = trace['stage']
        print('integration', stage, self.variant, app.window_size, app.output_size,
              app.output_valid, flush=True)
        if stage == 0:
            assert 'initial' in trace['saved']
            push_button(pico.SDL_BUTTON_LEFT, 520, 360)
        elif stage == 1:
            assert len(self.level.objects) == 5
            obj = self.level.objects[-1]
            assert abs(obj.y + 2.5) < .01 and obj.x > 4
            push_button(pico.SDL_BUTTON_RIGHT)
            self.level.mode.speed = 12
        elif stage == 2:
            assert len(self.level.objects) == 4 and 'boundary-entry' in trace['saved']
            self.level.mode.speed = 0
            self.level.objects[0].draw_order = 1000000
            trace['positions'] = [(o.x, o.y) for o in self.level.objects]
        elif stage == 3:
            assert 'ui-over-high-world' in trace['saved']
            push_key(pico.SDLK_RIGHT)
        elif stage == 4:
            assert self.camera_center == (2, 0)
            assert [(o.x, o.y) for o in self.level.objects] == trace['positions']
            assert (self.panel.x, self.panel.y) == (280, 220)
            app.set_display(window_size=(960, 540))
        elif stage == 5:
            assert app.window_size == (960, 540) and 'resized' in trace['saved']
            assert [(o.x, o.y) for o in self.level.objects] == trace['positions']
            app.set_display(fullscreen=True)
        elif stage == 6:
            assert app.fullscreen and 'fullscreen' in trace['saved']
            app.set_display(fullscreen=False)
        elif stage == 7:
            assert not app.fullscreen and app.window_size == (960, 540)
            pico.SDL_WarpMouseInWindow(pico.window, 480, 270)
        elif stage == 8:
            expected = self.ui_transform.inverse(*app.event_to_output(SimpleNamespace(type=pico.SDL_MOUSEMOTION, x=480, y=270)))
            assert self.pointer.visible
            assert abs(self.pointer.x - expected[0]) < 1 and abs(self.pointer.y - expected[1]) < 1
            assert self.event_to_world(SimpleNamespace(type=pico.SDL_MOUSEMOTION, x=480, y=270)) == (2, 0)
            pico.SDL_MinimizeWindow(pico.window)
        elif stage == 9:
            assert not app.output_valid and self.event_to_ui(SimpleNamespace(type=pico.SDL_MOUSEMOTION, x=0, y=0)) is None
            trace['paused_draws'] = trace['draws']
        elif stage == 10:
            assert trace['draws'] == trace['paused_draws']
            pico.SDL_RestoreWindow(pico.window)
        elif stage == 11:
            assert app.output_valid and trace['draws'] > trace['paused_draws']
            trace['before_hide'] = trace['child_ticks']
            push_key(pico.SDLK_h)
        elif stage == 12:
            assert not self.panel.visible and trace['child_ticks'] > trace['before_hide']
            assert 'hidden' in trace['saved']
            push_key(pico.SDLK_DELETE)
        elif stage == 13:
            assert self.panel.canvas is None and self.child.canvas is None
            assert not self.panel.children and 'deleted' in trace['saved']
            trace['old'] = self.level.objects, self.canvas.roots
            push_key(pico.SDLK_SPACE)
        elif stage == 14:
            assert self.variant == 1 and self.level.mode.speed == -2
            assert all(o.level is None for o in trace['old'][0])
            assert all(n.canvas is None for n in trace['old'][1])
            assert self.panel.canvas is self.canvas and len(self.level.objects) == 4
            assert 'level-B' in trace['saved']
            push_button(pico.SDL_BUTTON_MIDDLE)
        elif stage == 15:
            assert self.variant == 0 and self.level.mode.speed == 2
            assert 'return-A' in trace['saved']
            trace['passed'] = True
            push_key(pico.SDLK_ESCAPE)
            print('PASS: integrated/snapshots/order/alpha/input/camera/resize/fullscreen/minimize/roundtrip/escape', flush=True)
        trace['stage'] += 1
        trace['changed'] = now

    def draw(self):
        super().draw()
        trace = self.trace
        trace['draws'] += 1
        if trace['stage'] in (0, 3):
            rgb = self.pixel(self.ui_transform, 290, 230)
            assert all(abs(a - b) <= 3 for a, b in zip(rgb, (120, 100, 65))), rgb
            rgb = self.pixel(self.ui_transform, 450, 300)
            assert all(abs(a - b) <= 3 for a, b in zip(rgb, (119, 124, 138))), rgb
            self.capture('initial' if trace['stage'] == 0 else 'ui-over-high-world')
        if trace['stage'] == 2:
            mover = self.level.objects[2]
            if -6 < mover.x < 0:
                rgb = self.pixel(self.transform, mover.x, -3)
                assert all(abs(a - b) <= 3 for a, b in zip(rgb, (95, 207, 133))), rgb
                self.capture('boundary-entry')
        width, _ = self.ui_transform.logical_size
        assert self.pixel(self.ui_transform, width - 60, 30) == (170, 80, 200)
        if self.camera_center == (2, 0):
            self.capture('camera-shift')
        if self.engine.window_size == (960, 540) and not self.engine.fullscreen:
            self.capture('resized')
        if self.engine.fullscreen:
            self.capture('fullscreen')
        if not self.panel.visible:
            self.capture('hidden')
        if self.panel.canvas is None:
            self.capture('deleted')
        if self.variant == 1:
            self.capture('level-B')
        if len(trace['scenes']) == 3:
            self.capture('return-A')


if __name__ == '__main__':
    output = Path(sys.argv[1]).resolve()
    assert output.is_dir(), '기존 출력 폴더를 지정해야 합니다.'
    trace = dict(output=output, saved=set(), scenes=[], started=monotonic(), changed=monotonic(),
                 stage=0, draws=0, child_ticks=0, passed=False)
    Engine(640, 480).run(IntegrationSmoke(0, trace))
    assert trace['passed'] and len(trace['scenes']) == 3
    assert all(scene.engine is None and not scene.level.objects and not scene.canvas.roots and
               not scene.renderer.world_items and not scene.renderer.ui_items for scene in trace['scenes'])
