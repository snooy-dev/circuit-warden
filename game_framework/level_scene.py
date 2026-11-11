"""엔진 장면과 Level·Canvas의 연결."""

import pico2d.pico2d as pico
from engine import Scene

from .rendering import Renderer
from .transforms import WorldTransform
from .ui import _ui_snapshot


class LevelScene(Scene):
    def __init__(self, level, canvas=None, *, camera_center=(0, 0), view_height=10, images=None):
        camera = WorldTransform((0, 0, 0, 0), camera_center, view_height)
        self.level, self.canvas = level, canvas
        self.images = images
        self.camera_center, self.view_height = camera.center, camera.view_height
        self.renderer = Renderer()
        self.engine = None
        self._reset_generation = None

    @property
    def transform(self):
        viewport = self.engine.viewport if self.engine.output_valid else (0, 0, 0, 0)
        return WorldTransform(viewport, self.camera_center, self.view_height)

    @property
    def ui_transform(self):
        if self.canvas is None:
            return None
        viewport = self.engine.viewport if self.engine.output_valid else (0, 0, 0, 0)
        return self.canvas.transform(viewport)

    def enter(self, engine):
        if self.engine is not None or (self.canvas is not None and self.canvas._closed):
            raise RuntimeError('이미 진입했거나 닫힌 Canvas를 가진 장면입니다.')
        if self.images is not None and self.images.closed:
            raise RuntimeError('닫힌 이미지 저장소를 가진 장면은 재진입할 수 없습니다.')
        self.engine = engine
        self._reset_generation = engine.reset_generation
        try:
            self.level.open()
            if self.canvas is not None:
                self.ui_transform
        except BaseException as error:
            try:
                self.exit()
            except BaseException as cleanup_error:
                raise BaseExceptionGroup('장면 초기화와 정리 실패',
                                         [error, cleanup_error]) from None
            raise

    def event_to_world(self, event):
        point = self.engine.event_to_output(event)
        return None if point is None else self.transform.inverse(*point)

    def event_to_ui(self, event):
        if self.canvas is None:
            return None
        point = self.engine.event_to_output(event)
        return None if point is None else self.ui_transform.inverse(*point)

    def handle_event(self, event):
        if event.type == pico.SDL_RENDER_DEVICE_RESET:
            raise RuntimeError('렌더 리셋으로 그리기 자원을 다시 만들어야 합니다.')
        if event.type == pico.SDL_RENDER_TARGETS_RESET:
            self._reset_generation += 1
        self.level.handle_event(event)

    def update(self, dt):
        if self.canvas is None:
            return self.level.update(dt)
        self.level._check_rendering()
        self.canvas._check_rendering()
        if self.level._dispatching or self.canvas._dispatching:
            raise RuntimeError('입력/업데이트 전달에 재진입할 수 없습니다.')
        self.level._dispatching = self.canvas._dispatching = True
        world_snapshot = ui_snapshot = ()
        try:
            world_snapshot = self.level.objects
            ui_snapshot = _ui_snapshot(self.canvas._roots)
            self.level._dispatch_snapshot('on_update', 'update', dt, world_snapshot)
            self.canvas._update_snapshot(dt, ui_snapshot)
        finally:
            world_snapshot = ui_snapshot = ()
            self.level._dispatching = self.canvas._dispatching = False

    def draw(self):
        # shortcut: 장치/누락 리셋은 오류로 종료, 자동 복구가 필요해지면 재업로드로 확장한다.
        if self.engine.reset_generation != self._reset_generation:
            raise RuntimeError('렌더 리셋으로 그리기 자원을 다시 만들어야 합니다.')
        self.renderer.draw(self.level, self.transform, self.canvas)

    def exit(self):
        self.level._check_rendering()
        if self.canvas is not None:
            self.canvas._check_rendering()
        errors = []
        try:
            for owner in (self.level, self.canvas, self.images):
                if owner is not None:
                    try:
                        owner.close()
                    except BaseException as error:
                        errors.append(error)
        finally:
            self.renderer.world_items.clear()
            self.renderer.ui_items.clear()
            self.engine = None
        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise BaseExceptionGroup('장면 정리 실패', errors)
