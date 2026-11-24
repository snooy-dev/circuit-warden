"""실제 SDL 창에서 표시 전환과 예약 공격의 회귀를 확인한다."""

import argparse
import sys
from pathlib import Path
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pico2d.pico2d as pico

from engine import Engine
from game.character import BODY_HEIGHT, GROUND_Y
from game.scene import ALTERNATE_SIZE, DEFAULT_SIZE, CharacterScene
from tests.smoke.character_smoke import CharacterSmoke, push_click, push_key
from tests.smoke.charge_smoke import ChargeSmoke


class AuditSmoke(CharacterScene):
    capture = CharacterSmoke.capture
    click = ChargeSmoke.click

    def __init__(self, output_dir):
        super().__init__()
        self.output_dir = output_dir
        self.passed = False
        self.forced_dt = None

    def enter(self, engine):
        super().enter(engine)
        self.started = monotonic()
        self.steps = self.exercise()
        self.refs = tuple(clip.frames[0].image for clip in self.character.clips.values())
        for art in (self.level.charges[0].art, self.level.link_art):
            self.refs += tuple(frames[0].image for frames in art.frames)

    def exercise(self):
        actor = self.character
        target = self.level.charges[2]
        push_key(pico.SDLK_F6)
        yield

        assert self.engine.window_size == DEFAULT_SIZE
        self.capture('audit-before-resize')
        self.click(target.position)
        yield

        assert self.engine.window_size == ALTERNATE_SIZE and actor.x == target.position[0]
        self.link = self.level.mode.teleport_link
        assert self.link.end == target.position
        self.capture('audit-after-resize')

        # SDL 입력은 그대로 전달하며 예약 공격 재현에만 고정 dt를 사용한다.
        self.level.enemy.destroy()
        assert actor.teleport((0, GROUND_Y + BODY_HEIGHT / 2))
        push_key(pico.SDLK_LSHIFT)
        yield from (0, .1, .1, .1, .0672)
        assert actor.state == 'dash'
        push_click()
        yield from (.0166,) * 6
        assert actor.state == 'dash' and actor.buffered_action == 'attack'
        yield .08

        assert actor.state == 'attack'
        attack = actor.clips['attack']
        assert actor.player.clip is attack and actor.player.elapsed == 0
        assert actor.player.frame is attack.frames[0]
        self.capture('audit-buffered-attack-first')
        yield .05

        assert actor.player.elapsed == .05 and actor.player.frame is attack.frames[2]
        self.capture('audit-buffered-attack-fx')
        self.passed = True
        push_key(pico.SDLK_ESCAPE)
        yield

    def update(self, dt):
        assert monotonic() - self.started < 20, '감사 SDL 검사 시간 초과'
        if self.forced_dt is not None:
            dt, self.forced_dt = self.forced_dt, None
        super().update(dt)

    def draw(self):
        super().draw()
        if not self.passed:
            self.forced_dt = next(self.steps)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    output = parser.parse_args().output_dir.resolve()
    if not output.is_dir() or output.is_relative_to(Path(__file__).resolve().parents[2]):
        parser.error('프로젝트 밖의 기존 출력 폴더를 지정해야 합니다.')
    scene = AuditSmoke(output)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed and all(ref.closed for ref in scene.refs)
    assert all(charge.art is None and charge.level is None for charge in scene.level.charges)
    assert scene.link._frames is None and scene.link.level is None
    assert scene.engine is None and scene.level.objects == () and pico.renderer is None
    print('PASS: SDL queued click before F6 resize; buffered attack with forced dt; Escape and cleanup',
          flush=True)
