"""실제 SDL 창·이벤트로 기본 적 전투를 확인한다."""

import argparse
from pathlib import Path
from time import monotonic

import pico2d.pico2d as pico

from engine import Engine
from game.character import BODY_HEIGHT, GROUND_Y
from game.effects import SpriteEffect
from game.scene import CharacterScene, DEFAULT_SIZE
from tests.smoke.character_smoke import CharacterSmoke, push_click, push_key


class BasicEnemySmoke(CharacterScene):
    capture = CharacterSmoke.capture

    def __init__(self, output_dir):
        super().__init__()
        self.output_dir = output_dir
        self.passed = False

    def enter(self, engine):
        super().enter(engine)
        self.started = monotonic()
        self.next_step = self.started + .15
        self.steps = self.exercise()
        self.refs = (*[clip.frames[0].image for clip in self.character.clips.values()],
                     *[clip.frames[0].image for clip in self.level.enemy.clips.values()])
        self.previous_hp = self.level.enemy.hp
        self.previous_player_hp = self.character.hp

    def wait_until(self, condition):
        while not condition():
            yield .02

    def exercise(self):
        actor, enemy = self.character, self.level.enemy
        assert actor.hp == 5 and enemy.hp == 3
        self.capture('enemy-initial')
        yield from self.wait_until(lambda: enemy.state == 'approach')
        self.capture('enemy-approach')
        yield .20
        self.capture('enemy-approach-middle')
        yield from self.wait_until(lambda: enemy.state == 'windup')
        self.capture('enemy-windup')
        push_key(pico.SDLK_SPACE)
        yield .25
        self.capture('enemy-windup-peak')
        yield from self.wait_until(lambda: enemy.state == 'charge')
        self.capture('enemy-charge-jump')
        yield from self.wait_until(lambda: enemy.state == 'recover')
        assert actor.hp == 5, '예고를 보고 점프했지만 돌진 피해를 받음'
        self.capture('enemy-jump-evaded')
        yield .18
        self.capture('enemy-recover-middle')
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)

        # 점프 회피와 지상 피격을 분리해 피격 순간의 포즈를 확인한다.
        assert actor.teleport((enemy.x - 70, GROUND_Y + BODY_HEIGHT / 2))
        enemy.state, enemy.state_remaining, enemy.facing = 'charge', .28, -1
        yield from self.wait_until(lambda: actor.hp < actor.MAX_HP)
        assert actor.state == 'hurt' and GROUND_Y < actor.y < GROUND_Y + 8
        self.capture('player-ground-recoil')
        yield from self.wait_until(lambda: actor.hp == 0)
        self.capture('enemy-player-defeated')
        stopped = actor.x, actor.y, enemy.x, enemy.state, enemy.state_remaining
        push_key(pico.SDLK_a)
        push_key(pico.SDLK_SPACE)
        push_key(pico.SDLK_LSHIFT)
        push_click()
        yield .2
        assert stopped == (actor.x, actor.y, enemy.x, enemy.state, enemy.state_remaining)
        push_key(pico.SDLK_a, pico.SDL_KEYUP)
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        push_key(pico.SDLK_LSHIFT, pico.SDL_KEYUP)
        push_key(pico.SDLK_r)
        yield .05
        assert self.character is not actor and self.level.enemy is not enemy
        assert self.character.hp == 5 and self.level.enemy.hp == 3
        assert not self.character.pressed
        push_key(pico.SDLK_r, pico.SDL_KEYUP)
        self.capture('enemy-restarted')

        actor, enemy = self.character, self.level.enemy
        enemy.state, enemy.state_remaining = 'recover', 10.0
        actor.x, actor.y = enemy.x, enemy.hurt_box[3] + 5
        actor.velocity_y, actor.jump_phase = -190, 'fall'
        actor._machine.jump()
        yield from self.wait_until(lambda: actor.velocity_y > 0)
        assert actor.x != enemy.x and actor.hp == actor.MAX_HP and actor.state == 'jump'
        self.capture('player-top-rebound')
        for _ in range(30):
            if actor.grounded:
                break
            yield .025
        assert actor.grounded
        assert actor.hurt_box[2] <= enemy.hurt_box[0] or actor.hurt_box[0] >= enemy.hurt_box[2]
        self.capture('player-top-clear')

        actor.x, actor.y = enemy.x - 70, enemy.hurt_box[3] - 9
        actor.velocity_y, actor.jump_phase = -130, 'fall'
        if actor.state == 'idle':
            actor._machine.jump()
        enemy.state, enemy.state_remaining, enemy.facing = 'charge', .28, -1
        yield from self.wait_until(lambda: actor.hp < actor.MAX_HP)
        assert actor.state == 'hurt' and not actor.grounded and actor.velocity_y > 0
        self.capture('player-air-recoil')
        yield from self.wait_until(lambda: actor.state == 'jump')
        push_key(pico.SDLK_j)
        yield .025
        push_key(pico.SDLK_j, pico.SDL_KEYUP)
        assert actor.state == 'attack' and not actor.grounded
        assert actor.invulnerability_remaining > 0
        self.capture('player-air-counter')

        push_key(pico.SDLK_r)
        yield .05
        push_key(pico.SDLK_r, pico.SDL_KEYUP)
        actor, enemy = self.character, self.level.enemy
        enemy.state, enemy.state_remaining = 'recover', 10.0
        actor.x, actor.facing = enemy.x - 70, 1
        push_key(pico.SDLK_LSHIFT)
        yield .27
        assert actor.hurt_box[2] < enemy.hurt_box[0]
        assert actor.x < enemy.x - 70 and actor.state != 'dash' and actor.hp == 5
        assert not any(isinstance(obj, SpriteEffect) for obj in self.level.objects)
        self.capture('enemy-contact-rebound')
        push_key(pico.SDLK_LSHIFT, pico.SDL_KEYUP)

        actor.x = enemy.x - 70
        for hp in (2, 1, 0):
            actor.facing = 1 if enemy.x >= actor.x else -1
            push_click()
            yield .4
            assert enemy.hp == hp, (enemy.hp, hp)
        assert enemy.level is None
        self.capture('enemy-defeated')
        push_key(pico.SDLK_r)
        yield .05
        push_key(pico.SDLK_r, pico.SDL_KEYUP)
        actor, enemy = self.character, self.level.enemy
        assert enemy.hp == 3 and actor.hp == 5
        enemy.state, enemy.state_remaining = 'recover', 10.0
        actor.x, actor.facing = enemy.x + 70, -1
        push_click()
        yield .4
        assert enemy.hp == 2
        self.capture('enemy-left-hit')
        push_key(pico.SDLK_F6)
        yield .1
        self.capture('enemy-resized')
        self.passed = True
        push_key(pico.SDLK_ESCAPE)
        yield .1

    def update(self, dt):
        assert monotonic() - self.started < 40, '기본 적 SDL 검사 시간 초과'
        super().update(dt)

    def draw(self):
        super().draw()
        hp = self.level.enemy.hp
        if 0 < hp < self.previous_hp:
            self.capture(f'enemy-hit-{hp}')
        self.previous_hp = hp
        if self.character.hp < self.previous_player_hp:
            self.capture(f'player-hit-{self.character.hp}')
        self.previous_player_hp = self.character.hp
        if not self.passed and monotonic() >= self.next_step:
            self.next_step = monotonic() + next(self.steps)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    output = parser.parse_args().output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene = BasicEnemySmoke(output)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed and all(ref.closed for ref in scene.refs)
    assert scene.engine is None and scene.level.objects == () and pico.renderer is None
    print('PASS: enemy/windup/charge/jump-evade/body-top-bounce/ground-and-air-hurt/death/reset/left-right-hit/resize/cleanup', flush=True)
