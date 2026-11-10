"""실제 UI 창·입력·트리·기준점·픽셀 합성 검사. 기존 출력 폴더를 받는다."""

import sys
from ctypes import byref, c_ubyte
from pathlib import Path
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pico2d.pico2d as pico
from engine import Engine
from framework_demo import UIDemo
from world_smoke import push_key


class UISmoke(UIDemo):
    def __init__(self, output):
        super().__init__()
        self.output, self.saved = output, set()
        self.stage = self.draw_count = self.child_updates = 0
        self.started = self.changed = monotonic()
        self.passed = False

    def enter(self, engine):
        super().enter(engine)
        self.started = self.changed = monotonic()
        self.child.update = lambda dt: self.tick_child()

    def tick_child(self):
        self.child_updates += 1

    def pixel(self, x, y):
        px, py = self.transform.point(x, y)
        rgba = (c_ubyte * 4)()
        assert pico.SDL_RenderReadPixels(pico.renderer,
            pico.SDL_Rect(int(px), int(py), 1, 1), pico.SDL_PIXELFORMAT_RGBA32, rgba, 4) == 0
        return tuple(rgba)[:3]

    def capture(self, name):
        if name in self.saved:
            return
        width, height = self.engine.output_size
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, width, height, 32, pico.SDL_PIXELFORMAT_RGBA32)
        assert surface
        try:
            assert pico.SDL_RenderReadPixels(pico.renderer, None, pico.SDL_PIXELFORMAT_RGBA32,
                surface.contents.pixels, surface.contents.pitch) == 0
            assert pico.IMG_SavePNG(surface, str(self.output / f'p4-{name}.png').encode()) == 0
            self.saved.add(name)
        finally:
            pico.SDL_FreeSurface(surface)

    def update(self, dt):
        super().update(dt)
        now, app = monotonic(), self.engine
        assert now - self.started < 20, f'UI 검사 시간 초과: {self.stage}'
        if now - self.changed < .4:
            return
        print('ui', self.stage, app.window_size, app.output_size, app.output_valid, flush=True)
        if self.stage == 0:
            assert 'initial' in self.saved
            push_key(pico.SDLK_RIGHT)
        elif self.stage == 1:
            assert self.back.x == 70 and 'moved' in self.saved
            self.before_hidden_updates = self.child_updates
            push_key(pico.SDLK_h)
        elif self.stage == 2:
            assert not self.back.visible and 'hidden' in self.saved
            assert self.child_updates > self.before_hidden_updates
            push_key(pico.SDLK_h)
        elif self.stage == 3:
            assert self.back.visible
            push_key(pico.SDLK_DELETE)
        elif self.stage == 4:
            assert self.back.canvas is None and self.child.canvas is None
            assert not self.back.children and len(self.canvas.roots) == 4
            assert 'deleted' in self.saved
            app.set_display(window_size=(960, 540))
        elif self.stage == 5:
            assert app.window_size == (960, 540) and 'resized' in self.saved
            assert (self.corner.x, self.corner.y) == (-80, 20)
            assert abs(self.transform.scale - .9) < .001
            app.set_display(fullscreen=True)
        elif self.stage == 6:
            assert app.fullscreen and app.output_valid and 'fullscreen' in self.saved
            app.set_display(fullscreen=False)
        elif self.stage == 7:
            assert not app.fullscreen and app.window_size == (960, 540)
            pico.SDL_WarpMouseInWindow(pico.window, 480, 270)
        elif self.stage == 8:
            expected = self.transform.inverse(app.output_size[0] / 2, app.output_size[1] / 2)
            assert self.pointer.visible
            assert abs(self.pointer.x - expected[0]) < 1 and abs(self.pointer.y - expected[1]) < 1
            pico.SDL_MinimizeWindow(pico.window)
        elif self.stage == 9:
            assert not app.output_valid and self.transform.inverse(1, 1) is None
            self.paused_draw_count = self.draw_count
        elif self.stage == 10:
            assert self.draw_count == self.paused_draw_count
            pico.SDL_RestoreWindow(pico.window)
        elif self.stage == 11:
            assert app.output_valid and self.draw_count > self.paused_draw_count
            self.passed = True
            app.stop()
            print('PASS: ui/tree/order/alpha/anchor/mouse/resize/fullscreen/minimize/cleanup', flush=True)
        self.stage += 1
        self.changed = now

    def draw(self):
        super().draw()
        self.draw_count += 1
        if self.stage == 0:
            rgb = self.pixel(300, 230)
            assert all(abs(a - b) <= 2 for a, b in zip(rgb, (152, 157, 139))), rgb
            assert self.pixel(310, 310) == (50, 210, 100), '부모 opacity 비상속'
            assert self.pixel(30, 460) == (50, 210, 100), '화면 밖 부모의 안쪽 자식'
            assert self.pixel(740, 30) == (170, 80, 200)
            self.capture('initial')
        if self.stage == 1 and self.back.x == 70:
            assert self.pixel(215, 150) == (255, 215, 50)
            self.capture('moved')
        if not self.back.visible:
            assert self.pixel(215, 150) == (200, 200, 210)
            self.capture('hidden')
        if self.back.canvas is None:
            assert self.pixel(215, 150) == (200, 200, 210)
            self.capture('deleted')
        if self.engine.window_size == (960, 540) and not self.engine.fullscreen:
            width, _ = self.transform.logical_size
            assert self.pixel(width - 60, 30) == (170, 80, 200)
            self.capture('resized')
        if self.engine.fullscreen:
            width, _ = self.transform.logical_size
            assert self.pixel(width - 60, 30) == (170, 80, 200)
            self.capture('fullscreen')


if __name__ == '__main__':
    output = Path(sys.argv[1]).resolve()
    assert output.is_dir(), '기존 출력 폴더를 지정해야 합니다.'
    scene = UISmoke(output)
    Engine(640, 480).run(scene)
    assert scene.passed and scene.engine is None
    assert not scene.canvas.roots and not scene.renderer.ui_items
    assert scene.front.canvas is None and scene.front_child.canvas is None
