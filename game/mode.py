"""플레이 레벨의 입력 전달과 전투 초기화."""

from math import hypot

import pico2d.pico2d as pico

from game_framework import GameMode
from .charge import CLICK_RADIUS
from .teleport_link import DURATION, TeleportLink


class GameplayMode(GameMode):
    def on_start(self):
        self.reset_held = False
        self.cast_held = False

    def __init__(self):
        super().__init__()
        self.event_to_world = None
        self.cursor_to_world = None
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
        x, y = player.center
        if hypot(x - charge.position[0], y - charge.position[1]) <= 1e-6:
            return
        start = player.visual_center
        if not player.teleport(charge.position):
            return
        self.level.spend_charge(charge)
        player.teleport_guard_remaining = DURATION
        self.teleport_link = self.level.spawn(TeleportLink(
            start, player.center, self.level.link_art, self.level.combat_clips['charge_spent']))
        player.arrival_link = self.teleport_link
        for candidate in self.level.charges:
            candidate.active = candidate.in_range(self.activation_origin)

    def after_update(self):
        if self.level.player.hp == 0:
            self.pending_charge = None
            self.level.player.arrival_link = None
            if self.teleport_link is not None:
                self.teleport_link.destroy()
                self.teleport_link = None
            return
        if self.level.player.view_bounds is None:
            self.pending_charge = None
        if self.teleport_link is not None and self.teleport_link.level is not self.level:
            finished, self.teleport_link = self.teleport_link, None
            self.level.player.arrival_link = None
            charge, self.pending_charge = self.pending_charge, None
            if charge is not None:
                self._teleport(charge, finished.end)
                if self.teleport_link is not None:
                    # 갱신 후 생성한 효과는 다음 프레임부터 경과 시간을 모두 소비한다.
                    self.teleport_link.update(0)
        for candidate in self.level.charges:
            candidate.active = candidate.in_range(self.activation_origin)

    def on_end(self):
        self.level.charge_art = None
        self.level.link_art = None
        self.level.combat_clips.clear()
        self.pending_charge = self.teleport_link = None

    def on_event(self, event):
        if event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_w and self.level.power_supply:
            self.level.layout.restore_power(self.level.player)
            return
        if event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_r:
            if not self.reset_held:
                self.level.reset_combat()
                self.reset_held = True
            return
        if event.type == pico.SDL_KEYUP:
            if event.key == pico.SDLK_r:
                self.reset_held = False
            elif event.key == pico.SDLK_e:
                self.cast_held = False
        if event.type == pico.SDL_WINDOWEVENT and event.event in (
                pico.SDL_WINDOWEVENT_FOCUS_LOST, pico.SDL_WINDOWEVENT_MINIMIZED):
            self.reset_held = self.cast_held = False
            self.pending_charge = None
        player = self.level.player
        if player.level is self.level and player.hp > 0:
            if player.view_bounds is None:
                self.pending_charge = None
            if event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_e:
                if not self.cast_held and self.cursor_to_world is not None:
                    self.cast_held = True
                    self.level.cast_charge(self.cursor_to_world())
                return
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
