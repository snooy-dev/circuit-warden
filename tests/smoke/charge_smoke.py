"""실제 SDL 입력으로 전투·전하 소비·연결·창 좌표를 확인한다."""

import argparse
import sys
from ctypes import byref
from pathlib import Path
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pico2d.pico2d as pico

from engine import Engine
from game.effects import SpriteEffect
from game.scene import CharacterScene, DEFAULT_SIZE
from game.teleport_link import TeleportLink
from tests.smoke.character_smoke import CharacterSmoke, push_key


def window_point(scene, position):
    x, y = scene.transform.point(*position)
    return (round(x * scene.engine.window_size[0] / scene.engine.output_size[0]),
            round(y * scene.engine.window_size[1] / scene.engine.output_size[1]))


class ChargeSmoke(CharacterScene):
    capture = CharacterSmoke.capture

    def __init__(self, output_dir):
        super().__init__()
        self.output_dir, self.passed = output_dir, False
        self.wait = .1
        self.teleports = 0
        self.buffered_clicks = 0
        self.max_draw_seconds = 0
        self.draw_times = []
        self.capture_first = None

    def enter(self, engine):
        super().enter(engine)
        self.started = self.changed = monotonic()
        self.steps = self.exercise()
        self.observed_charges = set(self.level.charges)
        self.links = []

    def click(self, position, button=pico.SDL_BUTTON_LEFT):
        event = pico.SDL_Event()
        event.type = pico.SDL_MOUSEBUTTONDOWN
        event.button.button = button
        event.button.x, event.button.y = window_point(self, position)
        assert pico.SDL_PushEvent(byref(event)) == 1

    def handle_event(self, event):
        before, previous = self.character.center, self.level.mode.pending_charge
        super().handle_event(event)
        if self.level.mode.pending_charge is not None and self.level.mode.pending_charge is not previous:
            assert self.character.center == before
            self.buffered_clicks += 1
        link = self.record_link()
        if link is not None:
            assert (link.start, link.end) == (before, self.character.center)

    def record_link(self):
        link = self.level.mode.teleport_link
        if link is not None and link not in self.links:
            self.teleports += 1
            assert self.character.jump_phase == 'rise' and self.character.velocity_y > 0
            assert self.character.buffered_action is None and link.end == self.character.center
            assert link.arrival is not None
            self.links.append(link)
            self.capture_first = f'charge-first-{self.teleports}'
            return link

    def tap(self, symbol):
        push_key(symbol)
        push_key(symbol, pico.SDL_KEYUP)

    def exercise(self):
        actor = self.character
        self.capture('charge-ready')
        push_key(pico.SDLK_d)
        yield .05
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        assert actor.x > 0 and actor.facing == 1
        self.tap(pico.SDLK_j)
        yield .04
        assert actor.player.clip is actor.clips['attack'] and actor.grounded
        self.capture('combat-ground-swing')
        yield .47
        self.tap(pico.SDLK_SPACE)
        yield .20
        assert actor.jump_phase == 'rise' and not actor.grounded
        self.capture('combat-jump')

        self.tap(pico.SDLK_r)
        yield .04
        actor, enemy = self.character, self.level.enemy
        entry, escape = self.level.charges[2:4]
        self.click(entry.position)
        yield .02
        assert entry.spent and not entry.render_items()
        self.tap(pico.SDLK_j)
        hit_deadline = monotonic() + .3
        while enemy.hp == enemy.MAX_HP and monotonic() < hit_deadline:
            yield .001
        assert actor.player.clip is actor.clips['air_attack'] and not actor.grounded
        assert enemy.hp == enemy.MAX_HP - 1
        assert any(isinstance(obj, SpriteEffect) for obj in self.level.objects)
        self.capture('combat-air-hit')
        self.click(escape.position)
        yield .02
        assert actor.state == 'jump' and actor.x == escape.position[0] and escape.spent
        assert actor.active_attack is None and enemy.hp == enemy.MAX_HP - 1
        self.capture('combat-air-escape')

        self.tap(pico.SDLK_r)
        yield .04
        prior = entry, escape
        entry, escape = self.level.charges[2:4]
        assert all(old.level is None and old.position != fresh.position
                   for old, fresh in zip(prior, (entry, escape), strict=True))
        assert not entry.spent and not escape.spent
        self.click(entry.position)
        self.click((-400, 200), pico.SDL_BUTTON_RIGHT)
        yield .15
        assert self.character.x == escape.position[0] and entry.spent and escape.spent
        self.capture('charge-buffered-chain')

        self.tap(pico.SDLK_r)
        yield .04
        actor, enemy = self.character, self.level.enemy
        entry = self.level.charges[2]
        for _ in range(200):
            if enemy.state == 'charge':
                break
            yield .001
        assert enemy.state == 'charge'
        self.click(entry.position, pico.SDL_BUTTON_RIGHT)
        yield .025
        assert actor.x == entry.position[0] and actor.x > enemy.x
        assert entry.spent and actor.hp == actor.MAX_HP
        self.capture('combat-dodge')

        for key, name in ((pico.SDLK_F6, 'resized'), (pico.SDLK_F11, 'fullscreen')):
            self.tap(key)
            self.tap(pico.SDLK_r)
            yield .08
            entry = self.level.charges[2]
            count = self.teleports
            self.click((entry.position[0] + 44, entry.position[1]))
            yield .035
            assert self.teleports == count + 1 and self.character.x == entry.position[0]
            self.capture('charge-' + name)
        self.tap(pico.SDLK_F11)
        yield .2
        assert not any(isinstance(o, TeleportLink) for o in self.level.objects)
        self.capture('charge-settled')

        self.tap(pico.SDLK_r)
        yield .04
        target = (-90, -30)
        for _ in range(20):
            point = self.cursor_to_world()
            if point is not None and all(abs(a - b) < 1 for a, b in zip(point, target, strict=True)):
                break
            pico.SDL_WarpMouseInWindow(pico.window, *window_point(self, target))
            yield .025
        else:
            raise AssertionError('SDL 커서가 생성 위치에 도달하지 않았습니다.')
        self.tap(pico.SDLK_e)
        yield .025
        skill = self.level.skill_charge
        assert skill is not None and skill.active, (
            self.cursor_to_world(), pico.SDL_GetWindowFlags(pico.window), self.character.center,
            self.level.mode.cast_held, self.engine.window_size)
        assert all(abs(a - b) < 1 for a, b in zip(skill.position, target, strict=True))
        self.capture('charge-skill-created')
        self.click(skill.position)
        yield .025
        assert skill.spent and skill.level is None and self.level.skill_charge is None
        environmental = self.level.charges[1]
        self.click(environmental.position)
        yield .16
        assert environmental.spent and not environmental.render_items()
        self.capture('charge-environment-spent')
        for _ in range(30):
            if self.level.charges[1] is not environmental:
                break
            yield .1
        replacement = self.level.charges[1]
        assert environmental.level is None and replacement.position != environmental.position
        assert not replacement.spent
        self.capture('charge-environment-regenerated')

        self.passed = True
        push_key(pico.SDLK_ESCAPE)
        yield .1

    def update(self, dt):
        assert monotonic() - self.started < 20, '전하 SDL 검사 시간 초과'
        super().update(dt)
        self.observed_charges.update(self.level.charges)
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
    assert scene.passed and scene.teleports == 9 and scene.buffered_clicks >= 1
    assert all(c.art is None and c.level is None for c in scene.observed_charges)
    assert all(link._frames is None and link.arrival is None and link.level is None for link in scene.links)
    assert scene.engine is None and scene.level.objects == () and pico.renderer is None
    print(f'PASS: run/jump/swing/air-hit/dodge/cast/spend/regenerate/chain/resize/fullscreen/cleanup; '
          f'teleports={scene.teleports}, buffered={scene.buffered_clicks}, '
          f'max draw={scene.max_draw_seconds * 1000:.1f}ms, '
          f'median draw={sorted(scene.draw_times)[len(scene.draw_times)//2] * 1000:.1f}ms', flush=True)
