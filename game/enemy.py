"""기본 적 금속 먼지 덩어리."""

import json
from pathlib import Path

from game_framework import GameObject, RenderItem, SpritePlayer, draw_sprite

from .character import GROUND_Y, _load_clip


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'enemies'
BODY_HEIGHT = 78
HURT_HALF_WIDTH = 42
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


def load_enemy_clips(images):
    path = ASSETS / 'animations.json'
    try:
        animations = json.loads(path.read_text(encoding='utf-8'))
        clips = {name: _load_clip(images, animations[name], ASSETS)
                 for name in ('idle', 'approach', 'windup', 'charge', 'recover')}
        for name, clip in clips.items():
            if clip.loop != (name in ('idle', 'approach')):
                raise ValueError('idle/approach만 반복해야 합니다.')
        for name, seconds in (('windup', WINDUP_SECONDS), ('charge', CHARGE_SECONDS),
                              ('recover', RECOVER_SECONDS)):
            if abs(sum(clips[name].durations) - seconds) > 1e-9:
                raise ValueError(f'{name} 클립 시간이 전투 시간과 다릅니다.')
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ValueError(f'적 애니메이션 설정 오류: {path}: {error}') from error
    return clips


class Enemy(GameObject):
    MAX_HP = 3

    def __init__(self, clips):
        super().__init__()
        self.clips = clips
        self.animation = SpritePlayer(clips['idle'])
        self.x, self.y = SPAWN_X, float(GROUND_Y)
        self.facing = -1
        self.hp = self.MAX_HP
        self.hit_remaining = 0.0
        self.state = 'idle'
        self.state_remaining = IDLE_SECONDS
        self.motion = []
        self._charge_id = 0

    @property
    def frame(self):
        return self.animation.frame

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
        self.animation.play(self.clips[self.state])
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
                self.animation.update(step)
                self.motion.append(((elapsed, elapsed + step), start_x, self.x - start_x, charge_id))
            self.animation.play(self.clips[self.state])
            elapsed += step
            dt -= step

    def _draw(self, transform, opacity):
        if self.hit_remaining > 0 and int(self.hit_remaining / .045) % 2 == 0:
            opacity *= .3
        draw_sprite(self.frame, transform, (self.x, self.y),
                    self.frame.rect[2:], opacity, flip_x=self.facing < 0)

    def render_items(self):
        return (RenderItem(self._draw),)
