"""캐릭터 검사 장면과 창 조작."""

from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine, HEIGHT, WIDTH
from game_framework import GameObject, ImageStore, Level, LevelScene, RenderItem, draw_rect

from .character import GROUND_Y, Character, load_clips


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'warden'
DEFAULT_SIZE = (WIDTH, HEIGHT)
LARGE_SIZE = (1024, 720)


class _Ground(GameObject):
    def render_items(self):
        return (RenderItem(self._draw),)

    def _draw(self, transform, opacity):
        left, bottom, right, _ = transform.bounds
        draw_rect(transform, (left, bottom, right, GROUND_Y), (74, 79, 93), opacity)


class _CharacterLevel(Level):
    def __init__(self, images):
        super().__init__()
        self.images = images

    def on_open(self):
        self.spawn(_Ground())
        self.spawn(Character(load_clips(self.images)))


class CharacterScene(LevelScene):
    def __init__(self):
        images = ImageStore(ASSETS)
        super().__init__(_CharacterLevel(images), view_height=HEIGHT, images=images)

    @property
    def character(self):
        return self.level.objects[-1]

    def enter(self, engine):
        super().enter(engine)
        pico.SDL_SetWindowTitle(pico.window, b'Circuit Warden | A/D or arrows | F6 / F11 | Esc')

    def handle_event(self, event):
        if event.type == pico.SDL_KEYDOWN:
            if event.key == pico.SDLK_F6:
                size = LARGE_SIZE if self.engine.window_size == DEFAULT_SIZE else DEFAULT_SIZE
                self.engine.set_display(fullscreen=False, window_size=size)
            elif event.key == pico.SDLK_F11:
                self.engine.set_display(fullscreen=not self.engine.fullscreen)
        super().handle_event(event)

    def update(self, dt):
        self.character.view_bounds = self.transform.bounds
        super().update(dt)


def main():
    print('캐릭터 검사: A/D 또는 좌우 방향키 이동 / F6 창 크기 / F11 전체화면 / Escape 종료', flush=True)
    Engine().run(CharacterScene())
