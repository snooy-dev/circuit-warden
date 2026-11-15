"""플레이 레벨의 플레이어 입력 전달."""

from math import hypot

import pico2d.pico2d as pico

from game_framework import GameMode
from .charge import CLICK_RADIUS
from .teleport_link import TeleportLink


class GameplayMode(GameMode):
    def __init__(self):
        super().__init__()
        self.event_to_world = None
        self.teleport_link = None
        self.pending_charge = None

    @property
    def activation_origin(self):
        if self.teleport_link is not None and self.teleport_link.level is self.level:
            return self.teleport_link.end
        return self.level.player.center

    def _teleport(self, charge, origin):
        player = self.level.player
        if (charge.level is not self.level or not charge.in_range(origin)
                or not player.can_teleport(charge.position)):
            return
        start = player.center
        if player.teleport(charge.position) and hypot(
                start[0] - player.center[0], start[1] - player.center[1]) > 1e-6:
            self.teleport_link = self.level.spawn(TeleportLink(start, player.center, self.level.link_art))
        for candidate in self.level.charges:
            candidate.active = candidate.in_range(self.activation_origin)

    def after_update(self):
        if self.level.player.view_bounds is None:
            self.pending_charge = None
        if self.teleport_link is not None and self.teleport_link.level is not self.level:
            finished, self.teleport_link = self.teleport_link, None
            charge, self.pending_charge = self.pending_charge, None
            if charge is not None:
                self._teleport(charge, finished.end)
                if self.teleport_link is not None:
                    # 갱신 후 생성한 효과는 다음 프레임부터 경과 시간을 모두 소비한다.
                    self.teleport_link.update(0)
            for candidate in self.level.charges:
                candidate.active = candidate.in_range(self.activation_origin)

    def on_end(self):
        self.level.link_art = None
        self.pending_charge = self.teleport_link = None

    def on_event(self, event):
        player = self.level.player
        if player.level is self.level:
            if player.view_bounds is None:
                self.pending_charge = None
            if event.type == pico.SDL_WINDOWEVENT and event.event in (
                    pico.SDL_WINDOWEVENT_FOCUS_LOST, pico.SDL_WINDOWEVENT_MINIMIZED):
                self.pending_charge = None
            if (event.type == pico.SDL_MOUSEBUTTONDOWN
                    and event.button in (pico.SDL_BUTTON_LEFT, pico.SDL_BUTTON_RIGHT)
                    and player.view_bounds is not None):
                automatic = event.button == pico.SDL_BUTTON_RIGHT
                point = self.activation_origin if automatic else (
                    self.event_to_world(event) if self.event_to_world is not None else None)
                if point is not None:
                    candidates = [(hypot(point[0] - charge.position[0], point[1] - charge.position[1]),
                                   index, charge) for index, charge in enumerate(self.level.charges)
                                  if charge.level is self.level and charge.in_range(self.activation_origin)
                                  and player.can_teleport(charge.position)]
                    if candidates:
                        distance, _, charge = min(candidates)
                        if automatic or distance <= CLICK_RADIUS:
                            if self.teleport_link is not None and self.teleport_link.level is self.level:
                                self.pending_charge = charge
                            else:
                                self._teleport(charge, self.activation_origin)
                            return
            player.control(event)
