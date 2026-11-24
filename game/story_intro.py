"""New Game에서 전원 구역으로 이어지는 오프닝 컷신."""

from pathlib import Path

import pico2d.pico2d as pico

from engine import Scene
from game_framework import (
    Button, ButtonInput, Canvas, ImageStore, Label, Renderer, SpriteFrame,
    UIElement, draw_rect, draw_sprite,
)

from .title import MENU_FONT


ART = Path(__file__).resolve().parents[1] / 'assets' / 'story-intro'
FRAME_SIZE = (1280, 720)
SHOTS = (
    ('power-on.png', 'After a long silence, the computer powered on.', 4.0, .70),
    ('power-fault.png', 'Inside, one failure set off another.', 4.5, .67),
)


class StoryIntroScene(Scene):
    def __init__(self, first_level):
        self.first_level = first_level
        self.engine = None
        self.images = ImageStore(ART)
        self.canvas = Canvas(FRAME_SIZE)
        self.renderer = Renderer()
        self.input = ButtonInput(self.canvas)
        self.shot = 0
        self.elapsed = 0.0
        self.finishing = False

        frame = self.canvas.add(UIElement(anchor=(.5, .5), x=-640, y=-360))
        self.caption = self.canvas.add(Label(SHOTS[0][1], x=52, y=620, size=37,
                                            font_path=MENU_FONT), frame)
        self.skip = self.canvas.add(Button('Skip  [Esc]', self._finish, x=1112, y=613,
                                           width=136, height=54, size=27,
                                           color=(151, 212, 207), font_path=MENU_FONT), frame)

    def enter(self, engine):
        self.engine = engine
        self.plates = tuple(self.images.load(name) for name, *_ in SHOTS)

    @property
    def transform(self):
        viewport = self.engine.viewport if self.engine.output_valid else (0, 0, 0, 0)
        return self.canvas.transform(viewport)

    def handle_event(self, event):
        if event.type == pico.SDL_RENDER_DEVICE_RESET:
            raise RuntimeError('컷신을 그리려면 렌더링 자원을 다시 만들어야 합니다.')
        if not self.finishing:
            self.input.handle_event(event, self.transform, self.engine.event_to_output(event))

    def handle_escape(self):
        self._finish()
        return True

    def _finish(self):
        if not self.finishing:
            self.finishing = True
            self.engine.change_scene(self.first_level())

    def update(self, dt):
        if self.finishing or not self.engine.output_valid:
            return
        self.elapsed += dt
        duration = SHOTS[self.shot][2]
        if self.elapsed >= duration:
            if self.shot == len(SHOTS) - 1:
                self._finish()
            else:
                self.shot += 1
                self.elapsed -= duration
                self.caption.text = SHOTS[self.shot][1]

    def draw(self):
        transform = self.transform
        if not transform.valid:
            return
        draw_rect(transform, transform.bounds, (0, 0, 0))
        if self.finishing:
            return
        width, height = FRAME_SIZE
        cx, cy = (value / 2 for value in transform.logical_size)
        left, top = cx - width / 2, cy - height / 2
        _, _, duration, focal_x = SHOTS[self.shot]
        image = self.plates[self.shot]

        # 원화의 일부를 확대해도 16:9 표시 영역과 자막 위치를 유지한다.
        crop = .045 * self.elapsed / duration
        dx, dy = round(image.width * crop), round(image.height * crop)
        frame = SpriteFrame(image, (round(dx * focal_x), dy // 2,
                                    image.width - dx, image.height - dy))
        fade = min(1, self.elapsed / .26, (duration - self.elapsed) / .26)
        draw_sprite(frame, transform, (cx, cy), FRAME_SIZE, fade)
        draw_rect(transform, (left, top + 590, left + width, top + height), (5, 9, 13), .82)
        self.caption.opacity = fade
        self.renderer.draw_ui(self.canvas, transform)

    def exit(self):
        self.input.reset()
        try:
            self.canvas.close()
        finally:
            self.images.close()
            self.engine = None
