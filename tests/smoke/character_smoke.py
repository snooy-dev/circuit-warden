"""실제 SDL 창에서 캐릭터 표시·입력·자원 수명을 검사한다."""

import argparse
import sys
from ctypes import byref
from pathlib import Path
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pico2d.pico2d as pico

from engine import Engine
from game.scene import CharacterScene, DEFAULT_SIZE
from game.effects import SwordTrail


def push_key(symbol, kind=pico.SDL_KEYDOWN):
    event = pico.SDL_Event()
    event.type = kind
    event.key.keysym.sym = symbol
    assert pico.SDL_PushEvent(byref(event)) == 1


def push_focus_loss():
    event = pico.SDL_Event()
    event.type = pico.SDL_WINDOWEVENT
    event.window.event = pico.SDL_WINDOWEVENT_FOCUS_LOST
    assert pico.SDL_PushEvent(byref(event)) == 1


def push_click():
    event = pico.SDL_Event()
    event.type = pico.SDL_MOUSEBUTTONDOWN
    event.button.button = pico.SDL_BUTTON_LEFT
    assert pico.SDL_PushEvent(byref(event)) == 1


class CharacterSmoke(CharacterScene):
    def __init__(self, output_dir):
        super().__init__()
        self.output_dir = output_dir
        self.passed = False

    def enter(self, engine):
        super().enter(engine)
        self.refs = tuple(clip.frames[0].image for clip in self.character.clips.values())
        self.started = self.changed = monotonic()
        self.steps = self.exercise()

    def capture(self, name):
        width, height = self.engine.output_size
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, width, height, 32, pico.SDL_PIXELFORMAT_RGBA32)
        assert surface
        try:
            assert pico.SDL_RenderReadPixels(pico.renderer, None, pico.SDL_PIXELFORMAT_RGBA32,
                                             surface.contents.pixels, surface.contents.pitch) == 0
            path = self.output_dir / f'character-{name}.png'
            assert pico.IMG_SavePNG(surface, str(path).encode('utf-8')) == 0, path
        finally:
            pico.SDL_FreeSurface(surface)

    def exercise(self):
        actor = self.character
        assert self.engine.window_size == (1280, 720)
        idle, left, right = (actor.clips[name] for name in ('idle', 'run_left', 'run_right'))
        assert actor.player.clip is idle and actor.player.elapsed > 0 and actor.x == 0
        self.capture('idle')
        push_key(pico.SDLK_d)
        yield

        assert actor.player.clip is right and actor.x > 0 and actor.facing == 1
        self.capture('run-right')
        right_x = actor.x
        push_key(pico.SDLK_a)
        yield

        assert actor.player.clip is idle and actor.x == right_x and actor.facing == 1
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        yield

        assert actor.player.clip is left and actor.x < right_x and actor.facing == -1
        self.capture('run-left')
        stopped_x = actor.x
        push_key(pico.SDLK_a, pico.SDL_KEYUP)
        yield

        assert actor.player.clip is idle and actor.x == stopped_x and actor.facing == -1
        self.capture('idle-left')
        push_click()
        yield

        assert actor.state == 'attack' and actor.x == stopped_x and actor.facing == -1
        trail = next(obj for obj in self.level.objects if isinstance(obj, SwordTrail))
        assert trail.position[0] == stopped_x and trail.facing == -1
        self.capture('attack-left')
        push_key(pico.SDLK_d)
        push_click()
        yield

        assert actor.state == 'run' and actor.x > stopped_x and actor.facing == 1
        assert trail.level is self.level and trail.position[0] == stopped_x and trail.facing == -1
        self.capture('attack-resume-right')
        attack_x = actor.x
        push_click()
        yield

        assert actor.state == 'attack' and actor.x == attack_x and actor.facing == 1
        assert trail.level is None
        self.capture('attack-right')
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        push_click()
        yield

        assert actor.state == 'idle' and actor.x == attack_x and actor.facing == 1
        stopped_x = actor.x
        self.capture('attack-release-idle')
        push_key(pico.SDLK_a)
        yield

        assert actor.player.clip is left and actor.x < stopped_x
        stopped_x = actor.x
        push_focus_loss()
        yield

        assert actor.player.clip is idle and actor.x == stopped_x and not actor.pressed
        push_key(pico.SDLK_F6)
        yield

        assert self.engine.window_size == (1024, 720) and actor.x == stopped_x
        self.capture('resized')
        push_key(pico.SDLK_F11)
        yield

        assert self.engine.fullscreen
        self.capture('fullscreen')
        push_key(pico.SDLK_F11)
        yield

        assert not self.engine.fullscreen and self.engine.window_size == (1024, 720)
        self.passed = True
        push_key(pico.SDLK_ESCAPE)
        yield

    def update(self, dt):
        assert monotonic() - self.started < 15, '캐릭터 SDL 검사 시간 초과'
        super().update(dt)

    def draw(self):
        super().draw()
        if self.character.state == 'attack' and self.character.player.elapsed == 0:
            self.capture('attack-first-' + ('right' if self.character.facing > 0 else 'left'))
        now = monotonic()
        if not self.passed and now - self.changed >= .25:
            next(self.steps)
            self.changed = now


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    output = parser.parse_args().output_dir.resolve()
    if not output.is_dir() or output.is_relative_to(Path(__file__).resolve().parents[2]):
        parser.error('프로젝트 밖의 기존 출력 폴더를 지정해야 합니다.')
    scene = CharacterSmoke(output)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed and all(ref.closed for ref in scene.refs)
    assert scene.engine is None and scene.level.objects == () and pico.renderer is None
    print('PASS: idle/run-right/opposite/run-left/attack-left/resume/attack-right/release/focus-loss/resize/fullscreen/escape/cleanup',
          flush=True)
