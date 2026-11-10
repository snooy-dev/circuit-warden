"""실제 SDL 창 검사. 저장 폴더를 인자로 받고 10초 이내 자동 종료한다."""

import sys
from ctypes import byref
from pathlib import Path
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pico2d.pico2d as pico
from engine import Engine
from main import CheckScene


class DisplaySmoke(CheckScene):
    def enter(self, engine):
        super().enter(engine)
        self.started = self.changed = monotonic()
        self.stage = 0
        self.draws = 0
        self.saved = set()
        self.saw_minimized = False
        self.pointer_checked = False
        engine.set_display(window_size=(640, 480))

    def update(self, dt):
        super().update(dt)
        now = monotonic()
        if now - self.started > 10:
            raise AssertionError(f'실제 창 검사 시간 초과: {self.stage}')
        if now - self.changed < .6:
            return
        app = self.engine
        print(self.stage, app.window_size, app.output_size, app.fullscreen,
              app.output_valid, flush=True)
        if self.stage == 0:
            assert app.window_size == (640, 480)
            app.set_display(window_size=(960, 540))
        elif self.stage == 1:
            assert app.window_size == (960, 540)
            app.set_display(fullscreen=True)
        elif self.stage == 2:
            assert app.fullscreen and app.output_valid
            app.set_display(fullscreen=False)
        elif self.stage == 3:
            assert not app.fullscreen and app.window_size == (960, 540)
            pico.SDL_MinimizeWindow(pico.window)
            self.before_minimize = self.draws
        elif self.stage == 4:
            assert not app.output_valid
            assert self.draws == self.before_minimize
            self.saw_minimized = True
            pico.SDL_RestoreWindow(pico.window)
        elif self.stage == 5:
            assert app.output_valid and app.window_size == (960, 540)
            pico.SDL_WarpMouseInWindow(pico.window, 240, 135)
        elif self.stage == 6:
            point = app.window_to_output(240, 135)
            assert abs(self.pointer[0] - point[0]) <= 1
            assert abs(self.pointer[1] - (app.output_size[1] - 1 - point[1])) <= 1
            self.pointer_checked = True
            app.stop()
            print('PASS: resize/fullscreen/restore/minimize/mouse/render', flush=True)
        self.stage += 1
        self.changed = now

    def draw(self):
        super().draw()
        self.draws += 1
        if self.stage in (0, 1, 2, 3, 6) and self.stage not in self.saved:
            width, height = self.engine.output_size
            surface = pico.SDL_CreateRGBSurfaceWithFormat(
                0, width, height, 32, pico.SDL_PIXELFORMAT_RGBA32)
            assert surface
            try:
                assert pico.SDL_RenderReadPixels(pico.renderer, None,
                    pico.SDL_PIXELFORMAT_RGBA32, surface.contents.pixels,
                    surface.contents.pitch) == 0
                target = Path(sys.argv[1]) / f'p2-stage-{self.stage}.png'
                assert pico.IMG_SavePNG(surface, str(target).encode()) == 0
                self.saved.add(self.stage)
            finally:
                pico.SDL_FreeSurface(surface)


if __name__ == '__main__':
    scene = DisplaySmoke()
    Engine().run(scene)
    assert scene.saw_minimized and scene.pointer_checked
