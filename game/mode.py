"""플레이 레벨의 플레이어 입력 전달."""

from math import hypot

import pico2d.pico2d as pico

from game_framework import GameMode
from .charge import CLICK_RADIUS


class GameplayMode(GameMode):
    def __init__(self):
        super().__init__()
        self.event_to_world = None

    def on_event(self, event):
        player = self.level.player
        if player.level is self.level:
            if (event.type == pico.SDL_MOUSEBUTTONDOWN and event.button == pico.SDL_BUTTON_LEFT
                    and self.event_to_world is not None):
                point = self.event_to_world(event)
                if point is not None:
                    candidates = [(hypot(point[0] - charge.position[0], point[1] - charge.position[1]),
                                   index, charge) for index, charge in enumerate(self.level.charges)
                                  if charge.in_range(player) and player.can_teleport(charge.position)]
                    if candidates:
                        distance, _, charge = min(candidates)
                        if distance <= CLICK_RADIUS:
                            player.teleport(charge.position)
                            return
            player.control(event)
