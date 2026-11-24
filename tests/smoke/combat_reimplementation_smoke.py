"""실제 SDL 창에서 전투 조작과 플랫폼 훈련장을 검사한다."""

import argparse
from math import isclose
from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine
from game.character import GROUND_Y, JUMP_HEIGHT
from game.scene import CharacterScene, DEFAULT_SIZE
from game.training_map import LOW_WALL, PLATFORMS
from tests.smoke.character_smoke import CharacterSmoke, push_key


class CombatSmoke(CharacterScene):
    capture = CharacterSmoke.capture

    def __init__(self, output_dir, *, power_supply=False):
        super().__init__(power_supply=power_supply)
        self.output_dir = output_dir
        self.elapsed = self.next_step = 0.0
        self.screenshot = None
        self.passed = False

    def enter(self, engine):
        super().enter(engine)
        self.level.enemy.destroy()
        self.scenario = self.exercise()

    def update(self, dt):
        super().update(dt)
        self.elapsed += dt
        if self.elapsed >= self.next_step:
            try:
                self.next_step = self.elapsed + next(self.scenario)
            except StopIteration:
                self.passed = True
                self.engine.stop()

    def draw(self):
        super().draw()
        if self.screenshot:
            self.capture(self.screenshot)
            self.screenshot = None

    def wait_until(self, condition):
        deadline = self.elapsed + 3
        while not condition():
            assert self.elapsed < deadline, '훈련장 검사에서 예상 상태에 도달하지 못했습니다.'
            yield 0

    def running_jump(self, short):
        actor = self.character
        actor.x = 0
        push_key(pico.SDLK_d)
        push_key(pico.SDLK_SPACE)
        if short:
            yield .035
            push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: actor.velocity_y > 0)
        yield from self.wait_until(lambda: actor.velocity_y <= 0)
        height = actor.y - GROUND_Y
        yield from self.wait_until(lambda: actor.grounded)
        distance = actor.x
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        yield .25
        return height, distance

    def exercise(self):
        actor = self.character
        yield .08
        push_key(pico.SDLK_d)
        yield .1
        assert 0 < self.camera_center[0] < actor.x
        start = actor.x
        push_key(pico.SDLK_j)
        yield from self.wait_until(lambda: actor.state == 'attack' and actor.player.elapsed >= .14)
        assert actor.x > start and actor.attack_facing == 1
        self.screenshot = 'ground-moving-swing-right'
        start = actor.x
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        push_key(pico.SDLK_a)
        yield .055
        assert actor.state == 'attack' and actor.x < start and actor.attack_facing == 1
        yield from self.wait_until(lambda: actor.state == 'run' and actor.x < start)
        assert actor.facing == -1
        push_key(pico.SDLK_j, pico.SDL_KEYUP)
        yield .035
        start = actor.x
        push_key(pico.SDLK_j)
        yield from self.wait_until(lambda: actor.state == 'attack' and actor.player.elapsed >= .14)
        assert actor.x < start and actor.attack_facing == -1
        self.screenshot = 'ground-moving-swing-left'
        push_key(pico.SDLK_j, pico.SDL_KEYUP)
        push_key(pico.SDLK_a, pico.SDL_KEYUP)
        yield .25

        short = yield from self.running_jump(short=True)
        long = yield from self.running_jump(short=False)
        assert 65 < short[0] < 105 and 161 < long[0] <= JUMP_HEIGHT
        assert long[1] > short[1] + 40
        print(f'점프 높이 / 거리: 짧게 {short[0]:.1f} / {short[1]:.1f}, '
              f'길게 {long[0]:.1f} / {long[1]:.1f}', flush=True)

        actor.x = 0
        push_key(pico.SDLK_SPACE)
        yield from self.wait_until(lambda: actor.jump_phase == 'fall')
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: actor.y <= GROUND_Y + 65)
        assert not actor.grounded
        push_key(pico.SDLK_SPACE)
        for _ in self.wait_until(lambda: actor.jump_phase == 'rise'):
            assert not actor.grounded, '선입력 재점프가 착지에서 멈췄습니다.'
            yield 0
        self.screenshot = 'buffered-jump-takeoff'
        yield .05
        assert actor.y > GROUND_Y
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: actor.jump_phase == 'land')
        yield .19
        print('착지 직전 Space 선입력으로 즉시 재이륙', flush=True)

        actor.x = 385
        push_key(pico.SDLK_d)
        push_key(pico.SDLK_SPACE)
        yield from self.wait_until(lambda: actor.y > GROUND_Y + 123)
        push_key(pico.SDLK_j)
        yield from self.wait_until(lambda: actor.state == 'attack' and actor.player.elapsed >= .15)
        self.screenshot = 'air-swing-over-platform'
        push_key(pico.SDLK_j, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: actor.grounded)
        assert isclose(actor.y, PLATFORMS[3][3]), actor.y
        self.screenshot = 'on-platform'
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        yield .25

        actor.x, actor.y = 863, GROUND_Y
        self.camera_center = (700, 0)
        push_key(pico.SDLK_d)
        wall_contact = LOW_WALL[0] - actor.body.bounds[2]
        yield from self.wait_until(lambda: isclose(actor.x, wall_contact))
        camera_x = self.camera_center[0]
        self.screenshot = 'wall-blocked'
        yield .32
        assert isclose(actor.x, wall_contact) and self.camera_center[0] == camera_x < actor.x
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        push_key(pico.SDLK_r)
        yield .05
        assert self.character is not actor and self.camera_center == (0, 0)
        print(f'벽 접촉 x={wall_contact}, 고정 카메라 x={camera_x:.1f}', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = CombatSmoke(args.output_dir)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed, 'SDL 창이 검사를 마치기 전에 닫혔습니다.'
    print('PASS: combat reimplementation smoke', flush=True)


if __name__ == '__main__':
    main()
