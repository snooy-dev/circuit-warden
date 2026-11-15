"""기본 적 금속 먼지 덩어리."""

from pathlib import Path

from game_framework import GameObject, RenderItem, SpriteFrame, draw_rect, draw_sprite

from .character import GROUND_Y


IMAGE_PATH = Path(__file__).resolve().parents[1] / 'assets' / 'enemies' / 'metal_dust.png'
WIDTH, HEIGHT = 128, 96
BODY_HEIGHT = 55
HURT_HALF_WIDTH = 30
SPAWN_X = 220.0


def load_enemy_frame(images):
    image = images.load(IMAGE_PATH)
    return SpriteFrame(image, (0, 0, WIDTH, HEIGHT), (76 / WIDTH, 80 / HEIGHT))


class Enemy(GameObject):
    MAX_HP = 3

    def __init__(self, frame):
        super().__init__()
        self.frame = frame
        self.x, self.y = SPAWN_X, float(GROUND_Y)
        self.facing = -1
        self.hp = self.MAX_HP
        self.hit_remaining = 0.0

    @property
    def hurt_box(self):
        return self.x - HURT_HALF_WIDTH, self.y, self.x + HURT_HALF_WIDTH, self.y + BODY_HEIGHT

    def take_hit(self):
        if self.hp > 0:
            self.hp -= 1
            self.hit_remaining = .18
            if self.hp == 0:
                self.destroy()

    def update(self, dt):
        self.hit_remaining = max(0.0, self.hit_remaining - dt)

    def _draw(self, transform, opacity):
        if self.hit_remaining > 0 and int(self.hit_remaining / .045) % 2 == 0:
            opacity *= .3
        draw_sprite(self.frame, transform, (self.x, self.y), (WIDTH, HEIGHT),
                    opacity, flip_x=self.facing < 0)

    def _draw_health(self, transform, opacity):
        left, y = self.x - 25, self.y + BODY_HEIGHT + 8
        draw_rect(transform, (left - 2, y - 2, left + 52, y + 7), (28, 30, 38), opacity)
        draw_rect(transform, (left, y, left + 50 * self.hp / self.MAX_HP, y + 5),
                  (232, 90, 90), opacity)

    def render_items(self):
        return RenderItem(self._draw), RenderItem(self._draw_health, draw_order=1)
