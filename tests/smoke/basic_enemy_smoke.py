"""실제 SDL 창·이벤트로 기본 적 전투를 확인한다."""

import argparse
from pathlib import Path
from time import monotonic

import pico2d.pico2d as pico

from engine import Engine
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
                     self.level.enemy.frame.image)
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
        yield from self.wait_until(lambda: enemy.state == 'windup')
        self.capture('enemy-windup')
        push_key(pico.SDLK_SPACE)
        yield from self.wait_until(lambda: enemy.state == 'charge')
        self.capture('enemy-charge-jump')
        yield from self.wait_until(lambda: enemy.state == 'recover')
        assert actor.hp == 5, '예고를 보고 점프했지만 돌진 피해를 받음'
        self.capture('enemy-jump-evaded')
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
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
        actor.x, actor.facing = enemy.x - 60, 1
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
        actor.x, actor.facing = enemy.x + 60, -1
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
    print('PASS: enemy/render/windup/charge/recover/jump-evade/player-hit/death/reset/left-right-hit/resize/cleanup', flush=True)
