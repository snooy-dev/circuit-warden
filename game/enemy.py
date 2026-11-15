"""기본 적 금속 먼지 덩어리."""

from pathlib import Path

from game_framework import GameObject, RenderItem, SpriteFrame, draw_sprite

from .character import GROUND_Y


IMAGE_PATH = Path(__file__).resolve().parents[1] / 'assets' / 'enemies' / 'metal_dust.png'
WIDTH, HEIGHT = 128, 96
BODY_HEIGHT = 55
HURT_HALF_WIDTH = 30
SPAWN_X = 220.0
IDLE_SECONDS = .18
APPROACH_SPEED = 100
WINDUP_RANGE = 72
WINDUP_SECONDS = .45
CHARGE_SPEED = 350
CHARGE_SECONDS = .28
RECOVER_SECONDS = .60

NEXT_PHASE = {
    'idle': ('approach', 0),
    'windup': ('charge', CHARGE_SECONDS),
    'charge': ('recover', RECOVER_SECONDS),
    'recover': ('idle', IDLE_SECONDS),
}
POSE_SCALE = {'windup': (1.12, .76), 'charge': (1.15, .90), 'recover': (1.04, .88)}


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
        self.state = 'idle'
        self.state_remaining = IDLE_SECONDS
        self.motion = []
        self._charge_id = 0

    @property
    def hurt_box(self):
        return self.hurt_box_at(self.x)

    def hurt_box_at(self, x):
        return x - HURT_HALF_WIDTH, self.y, x + HURT_HALF_WIDTH, self.y + BODY_HEIGHT

    def take_hit(self):
        if self.hp > 0:
            self.hp -= 1
            self.hit_remaining = .18
            if self.hp == 0:
                self.destroy()

    def update(self, dt):
        self.motion.clear()
        self.hit_remaining = max(0.0, self.hit_remaining - dt)
        target = self.level.player
        elapsed = 0.0
        while dt > 0:
            start_x = self.x
            charge_id = None
            if self.state == 'approach':
                gap = target.x - self.x
                if gap:
                    self.facing = 1 if gap > 0 else -1
                time_to_windup = max(0.0, (abs(gap) - WINDUP_RANGE) / APPROACH_SPEED)
                step = min(dt, time_to_windup)
                self.x += self.facing * APPROACH_SPEED * step
                if step == time_to_windup:
                    self.state, self.state_remaining = 'windup', WINDUP_SECONDS
                    self._charge_id += 1
            else:
                step = min(dt, self.state_remaining)
                if self.state == 'charge':
                    self.x += self.facing * CHARGE_SPEED * step
                    charge_id = self._charge_id
                self.state_remaining -= step
                if self.state_remaining == 0:
                    self.state, self.state_remaining = NEXT_PHASE[self.state]
            if step > 0:
                self.motion.append(((elapsed, elapsed + step), start_x, self.x - start_x, charge_id))
            elapsed += step
            dt -= step

    def _draw(self, transform, opacity):
        if self.hit_remaining > 0 and int(self.hit_remaining / .045) % 2 == 0:
            opacity *= .3
        width_scale, height_scale = POSE_SCALE.get(self.state, (1, 1))
        draw_sprite(self.frame, transform, (self.x, self.y),
                    (WIDTH * width_scale, HEIGHT * height_scale), opacity, flip_x=self.facing < 0)

    def render_items(self):
        return (RenderItem(self._draw),)
