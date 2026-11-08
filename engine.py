"""창 하나와 활성 장면 하나를 실행하는 Pico2D 기반 루프."""

from time import perf_counter, sleep

import pico2d.pico2d as pico

WIDTH, HEIGHT = 800, 600
FRAME_SECONDS = 1 / 60
MAX_DT = 0.1
_active_engine = None


class Scene:
    def enter(self, engine: 'Engine') -> None:
        pass

    def handle_event(self, event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        pass

    def exit(self) -> None:
        pass


class Engine:
    def __init__(self):
        self._running = False
        self._scene = None
        self._pending = None

    def stop(self) -> None:
        self._running = False

    def change_scene(self, scene: Scene) -> None:
        self._pending = scene

    def _leave_scene(self) -> None:
        scene, self._scene = self._scene, None
        if scene is not None:
            scene.exit()

    def run(self, initial_scene: Scene) -> None:
        global _active_engine
        if _active_engine is not None:
            raise RuntimeError('Pico2D 엔진은 동시에 하나만 실행할 수 있습니다.')
        _active_engine = self
        self._running = True
        self._pending = None
        # Pico2D는 부분 생성 실패와 이전 실행의 핸들을 자체 정리하지 않는다.
        pico.window = pico.renderer = None
        pico.audio_on = False
        try:
            pico.open_canvas(WIDTH, HEIGHT)
            if not pico.window or not pico.renderer:
                raise RuntimeError('Pico2D 창 또는 렌더러를 생성하지 못했습니다.')
            pico.hide_lattice()
            self._scene = initial_scene
            self._scene.enter(self)
            previous = None
            while self._running:
                started = perf_counter()
                dt = 0.0 if previous is None else min(started - previous, MAX_DT)
                previous = started
                for event in pico.get_events():
                    if event.type == pico.SDL_QUIT or (
                        event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_ESCAPE
                    ):
                        self.stop()
                    else:
                        self._scene.handle_event(event)
                    if not self._running:
                        break
                if not self._running:
                    break
                self._scene.update(dt)
                if not self._running:
                    break
                pico.clear_canvas()
                self._scene.draw()
                if not self._running:
                    break
                pico.update_canvas()
                if self._pending is not None:
                    next_scene, self._pending = self._pending, None
                    self._leave_scene()
                    if not self._running:
                        break
                    self._scene = next_scene
                    self._scene.enter(self)
                    previous = None
                if self._running:
                    sleep(max(0.0, FRAME_SECONDS - (perf_counter() - started)))
        finally:
            self._running = False
            try:
                self._leave_scene()
            finally:
                self._pending = None
                try:
                    pico.close_canvas()
                finally:
                    pico.window = pico.renderer = None
                    _active_engine = None
