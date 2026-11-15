"""실제 SDL 입력으로 전하 선택·취소·연결·창 좌표를 확인한다."""

import argparse
import sys
from ctypes import byref
from pathlib import Path
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pico2d.pico2d as pico

from engine import Engine
from game.character import BODY_HEIGHT, GROUND_Y
from game.scene import CharacterScene, DEFAULT_SIZE
from tests.smoke.character_smoke import CharacterSmoke, push_key


class ChargeSmoke(CharacterScene):
    capture = CharacterSmoke.capture

    def __init__(self, output_dir):
        super().__init__()
        self.output_dir, self.passed = output_dir, False
        self.wait = .7
        self.teleports = 0
        self.max_draw_seconds = 0

    def enter(self, engine):
        super().enter(engine)
        self.started = self.changed = monotonic()
        self.steps = self.exercise()
        self.charges = tuple(self.level.charges)

    def click(self, position):
        x, y = self.transform.point(*position)
        event = pico.SDL_Event()
        event.type = pico.SDL_MOUSEBUTTONDOWN
        event.button.button = pico.SDL_BUTTON_LEFT
        event.button.x = round(x * self.engine.window_size[0] / self.engine.output_size[0])
        event.button.y = round(y * self.engine.window_size[1] / self.engine.output_size[1])
        assert pico.SDL_PushEvent(byref(event)) == 1

    def handle_event(self, event):
        before = self.character.center
        super().handle_event(event)
        if self.character.center != before:
            self.teleports += 1
            assert self.character.jump_phase == 'fall'
            assert self.character.velocity_y == 0
            assert self.character.buffered_action is None

    def exercise(self):
        actor = self.character
        self.capture('charge-ready')
        self.click(self.charges[-1].position)
        yield .04
        assert actor.state == 'attack' and actor.grounded
        self.click(self.charges[2].position)
        yield .06
        assert actor.state == 'jump' and actor.x == 140
        self.capture('charge-attack-cancel')
        for index in (4, 1, 0):
            self.click(self.charges[index].position)
            yield .07
            assert actor.x == self.charges[index].position[0]
            self.capture(f'charge-chain-{index}')
        yield .8
        assert actor.grounded
        actor.teleport((0, GROUND_Y + BODY_HEIGHT / 2))
        push_key(pico.SDLK_SPACE)
        yield .04
        assert actor.jump_phase == 'start'
        self.click(self.charges[2].position)
        yield .06
        assert actor.jump_phase == 'fall'
        self.capture('charge-jump-cancel')
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        actor.teleport((0, GROUND_Y + BODY_HEIGHT / 2))
        push_key(pico.SDLK_LSHIFT)
        yield .14
        assert actor.state == 'dash'
        self.click(self.charges[2].position)
        yield .06
        assert actor.jump_phase == 'fall' and actor.dash_phase is None
        self.capture('charge-dash-cancel')
        push_key(pico.SDLK_LSHIFT, pico.SDL_KEYUP)
        for key, name in ((pico.SDLK_F6, 'resized'), (pico.SDLK_F11, 'fullscreen')):
            push_key(key)
            yield .12
            actor.teleport((0, GROUND_Y + BODY_HEIGHT / 2))
            count = self.teleports
            self.click(self.charges[2].position)
            yield .06
            assert self.teleports == count + 1 and actor.x == 140
            self.capture('charge-' + name)
        push_key(pico.SDLK_F11)
        yield .6
        self.capture('charge-settled')
        self.passed = True
        push_key(pico.SDLK_ESCAPE)
        yield .1

    def update(self, dt):
        assert monotonic() - self.started < 20, '전하 SDL 검사 시간 초과'
        super().update(dt)

    def draw(self):
        started = monotonic()
        super().draw()
        self.max_draw_seconds = max(self.max_draw_seconds, monotonic() - started)
        now = monotonic()
        if not self.passed and now - self.changed >= self.wait:
            self.wait = next(self.steps)
            self.changed = now


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    output = parser.parse_args().output_dir.resolve()
    if not output.is_dir() or output.is_relative_to(Path(__file__).resolve().parents[2]):
        parser.error('프로젝트 밖 기존 폴더를 지정해야 합니다.')
    scene = ChargeSmoke(output)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed and scene.teleports >= 8
    assert all(c.texture is None and c.level is None for c in scene.charges)
    assert scene.engine is None and scene.level.objects == () and pico.renderer is None
    print(f'PASS: charge click/cancel/chain/resize/fullscreen/cleanup; '
          f'teleports={scene.teleports}, max draw={scene.max_draw_seconds * 1000:.1f}ms', flush=True)
