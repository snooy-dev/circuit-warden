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
from game.teleport_link import TeleportLink
from tests.smoke.character_smoke import CharacterSmoke, push_key


class ChargeSmoke(CharacterScene):
    capture = CharacterSmoke.capture

    def __init__(self, output_dir):
        super().__init__()
        self.output_dir, self.passed = output_dir, False
        self.wait = .7
        self.teleports = 0
        self.buffered_clicks = 0
        self.max_draw_seconds = 0
        self.draw_times = []
        self.capture_first = None

    def enter(self, engine):
        super().enter(engine)
        self.started = self.changed = monotonic()
        self.steps = self.exercise()
        self.charges = tuple(self.level.charges)
        self.links = []

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
        if self.level.mode.pending_charge is not None:
            assert self.character.center == before
            self.buffered_clicks += 1
        if self.character.center != before:
            self.record_link()
            link = self.links[-1]
            assert (link.start, link.end) == (before, self.character.center)

    def record_link(self):
        link = self.level.mode.teleport_link
        if link is not None and link not in self.links:
            self.teleports += 1
            assert self.character.jump_phase == 'rise' and self.character.velocity_y > 0
            assert self.character.buffered_action is None and link.end == self.character.center
            self.links.append(link)
            self.capture_first = f'charge-first-{self.teleports}'

    def exercise(self):
        actor = self.character
        self.capture('charge-ready')
        self.click(self.charges[-1].position)
        yield .04
        assert actor.state == 'attack' and actor.grounded
        self.click(self.charges[2].position)
        yield .06
        assert actor.state == 'jump' and actor.x == 140
        assert actor.center[1] > self.charges[2].position[1] and actor.velocity_y > 0
        self.capture('charge-attack-cancel')
        self.capture('charge-lift-rise')
        yield .19
        assert actor.jump_phase == 'fall' and actor.center[1] > self.charges[2].position[1]
        self.capture('charge-lift-fall')
        for index in (4, 1, 0):
            self.click(self.charges[index].position)
            yield .08
            assert actor.x == self.charges[index].position[0]
            self.capture(f'charge-chain-{index}')
        yield .8
        assert actor.grounded
        assert not any(isinstance(o, TeleportLink) for o in self.level.objects)
        actor.teleport((0, GROUND_Y + BODY_HEIGHT / 2))
        push_key(pico.SDLK_SPACE)
        yield .04
        assert actor.jump_phase == 'start'
        self.click(self.charges[2].position)
        yield .06
        assert actor.jump_phase == 'rise'
        self.capture('charge-jump-cancel')
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        actor.teleport((0, GROUND_Y + BODY_HEIGHT / 2))
        push_key(pico.SDLK_LSHIFT)
        yield .14
        assert actor.state == 'dash'
        self.click(self.charges[2].position)
        yield .06
        assert actor.jump_phase == 'rise' and actor.dash_phase is None
        self.capture('charge-dash-cancel')
        push_key(pico.SDLK_LSHIFT, pico.SDL_KEYUP)
        yield .12
        target = self.charges[2]
        original = target.position
        for start, end, name in (((0, 0), (200, 0), 'horizontal'),
                                 ((200, -40), (200, 160), 'vertical')):
            actor.teleport(start)
            target.position = end
            self.click(end)
            yield .06
            assert self.links[-1].start == start and self.links[-1].end == end
            self.capture('charge-' + name)
            yield .12
        target.position = original
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
        self.record_link()

    def draw(self):
        started = monotonic()
        super().draw()
        self.max_draw_seconds = max(self.max_draw_seconds, monotonic() - started)
        self.draw_times.append(monotonic() - started)
        if self.capture_first is not None:
            self.capture(self.capture_first)
            self.capture_first = None
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
    assert scene.passed and scene.teleports >= 10 and scene.buffered_clicks >= 1
    assert all(c.texture is None and c.level is None for c in scene.charges)
    assert all(link.texture is None and link.level is None for link in scene.links)
    assert scene.engine is None and scene.level.objects == () and pico.renderer is None
    print(f'PASS: charge click/cancel/chain/resize/fullscreen/cleanup; '
          f'teleports={scene.teleports}, buffered={scene.buffered_clicks}, '
          f'max draw={scene.max_draw_seconds * 1000:.1f}ms, '
          f'median draw={sorted(scene.draw_times)[len(scene.draw_times)//2] * 1000:.1f}ms', flush=True)
