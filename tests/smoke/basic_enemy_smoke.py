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

    def exercise(self):
        enemy = self.level.enemy
        assert enemy.hp == 3
        self.capture('enemy-initial')
        self.character.x = enemy.x - 60
        self.character.facing = 1
        for hp in (2, 1, 0):
            push_click()
            yield .4
            assert enemy.hp == hp, (enemy.hp, hp)
        assert enemy.level is None
        self.capture('enemy-defeated')
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
    print('PASS: enemy/render/three-hits/health/death/cleanup', flush=True)
