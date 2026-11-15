"""플레이 레벨의 입력 전달과 전투 초기화."""

import pico2d.pico2d as pico

from game_framework import GameMode


class GameplayMode(GameMode):
    def on_start(self):
        self.reset_held = False

    def on_event(self, event):
        if event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_r:
            if not self.reset_held:
                self.level.reset_combat()
                self.reset_held = True
            return
        if (event.type == pico.SDL_KEYUP and event.key == pico.SDLK_r
                or event.type == pico.SDL_WINDOWEVENT and event.event in (
                    pico.SDL_WINDOWEVENT_FOCUS_LOST, pico.SDL_WINDOWEVENT_MINIMIZED)):
            self.reset_held = False
        player = self.level.player
        if player.level is self.level and player.hp > 0:
            player.control(event)
