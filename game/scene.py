"""플레이 레벨 배치와 장면·창 조작."""

from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine, HEIGHT
from game_framework import GameObject, ImageStore, Level, LevelScene, RenderItem, draw_rect

from .character import GROUND_Y, Character, load_clips
from .mode import GameplayMode


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'warden'
DEFAULT_SIZE = (1280, 720)
ALTERNATE_SIZE = (1024, 720)


class _Ground(GameObject):
    def render_items(self):
        return (RenderItem(self._draw, draw_order=-2),)

    def _draw(self, transform, opacity):
        left, bottom, right, _ = transform.bounds
        draw_rect(transform, (left, bottom, right, GROUND_Y), (74, 79, 93), opacity)


class GameplayLevel(Level):
    def __init__(self, images):
        super().__init__(GameplayMode())
        self.images = images
        self.player = None

    def on_open(self):
        self.spawn(_Ground())
        self.player = self.spawn(Character(load_clips(self.images)))


class CharacterScene(LevelScene):
    def __init__(self):
        images = ImageStore(ASSETS)
        super().__init__(GameplayLevel(images), view_height=HEIGHT, images=images)

    @property
    def character(self):
        return self.level.player

    def enter(self, engine):
        super().enter(engine)
        pico.SDL_SetWindowTitle(pico.window, b'Circuit Warden | A/D | Space: jump | Left click: attack | F6 / F11 | Esc')

    def handle_event(self, event):
        if event.type == pico.SDL_KEYDOWN:
            if event.key == pico.SDLK_F6:
                size = ALTERNATE_SIZE if self.engine.window_size == DEFAULT_SIZE else DEFAULT_SIZE
                self.engine.set_display(fullscreen=False, window_size=size)
            elif event.key == pico.SDLK_F11:
                self.engine.set_display(fullscreen=not self.engine.fullscreen)
        super().handle_event(event)

    def update(self, dt):
        self.character.view_bounds = self.transform.bounds
        super().update(dt)


def main():
    print('게임플레이: A/D 이동 / Space 점프 / 왼쪽 클릭 공격 / F6 창 크기 / F11 전체화면 / Escape 종료', flush=True)
    Engine(*DEFAULT_SIZE).run(CharacterScene())
