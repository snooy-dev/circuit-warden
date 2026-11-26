"""파워서플라이 맵의 배치·충돌·렌더링."""

import json
from functools import partial
from math import hypot
from pathlib import Path

import pico2d.pico2d as pico

from engine.rendering.drawing import _sdl
from game_framework import Collider, GameObject, RenderItem, draw_image, draw_rect
from game_framework.collision import blocking_contact, overlaps


MAP_FILE = Path(__file__).resolve().parents[1] / 'assets/levels/power-supply/map.json'
DRAW_ORDER = {'rear': -4, 'structure': -2, 'front': 4}


class PowerSupplyMap(GameObject):
    def __init__(self, images):
        super().__init__()
        data = json.loads(MAP_FILE.read_text(encoding='utf-8'))
        world = data['world']
        self.half_width, self.half_height = world['width'] / 2, world['height'] / 2
        self.bounds = self._rect(0, 0, world['width'], world['height'])
        self.rooms = {room['id']: self._rect(*room['rect']) for room in data['camera']['rooms']}
        self.terrain = tuple(
            Collider(self._rect(*rect), 'terrain', blocks={'player', 'enemy'})
            for rect in data['collision']['rects'])
        self.devices = tuple((item['kind'], self._rect(*item['rect']))
                             for item in data['collision']['power_devices'])
        self.boss_gate = next(bounds for kind, bounds in self.devices if kind == 'boss-shutter')
        self.busbar = self._rect(*data['collision']['busbar'])
        self.teleport_barriers = tuple(self._rect(*rect) for rect in data['collision'].get('teleport_barriers', ()))
        relay = next(item for item in data['interactions'] if item['id'] == 'relay')
        self.relay = self._point(relay['x'], relay['y'])
        self.relay_reach = relay['reach']
        self.fork_approach = self._rect(*data['navigation']['fork_approach'])
        self.relay_return = self._rect(*data['navigation']['relay_return'])
        hatch = next(item for item in data['interactions'] if item['id'] == 'hatch-release')
        self.hatch_release = self._point(hatch['x'], hatch['y'])
        self.hatch_reach = hatch['reach']
        player_spawn = next(entry for entry in data['spawns'] if entry['id'] == 'start')
        self.player_start = self._point(player_spawn['x'], player_spawn['feet_y'])
        self.enemy_spawns = tuple(
            (entry['kind'], self._point(*entry['position']),
             tuple(x - self.half_width for x in entry['x_limits']))
            for entry in data['enemies'])
        self.start_room = self.room_at(self.player_start)
        _, intake_bottom, _, intake_top = self.rooms[self.start_room]
        self.start_camera_y = (intake_bottom + intake_top) / 2
        self.power_entry = self._point(*player_spawn['entry_origin'])
        self.charge_sites = tuple(tuple(self._point(*point) for point in anchor['variants'])
                                  for anchor in data['anchors'].values())
        output = next(item for item in data['interactions'] if item['id'] == 'output')
        self.output = self._point(output['x'], output['y'])
        self.output_reach = output['reach']
        self.output_lock = self._rect(*data['collision']['output_lock'])
        self.reset()

        def load(prop):
            image = images.load(MAP_FILE.parent / data['props'][prop]['image'])._borrow()
            _sdl(pico.SDL_SetTextureScaleMode(image.texture, pico.SDL_ScaleModeNearest))
            return image

        background = data['layers'][0]
        self.fan_cavity = load('fan-cavity')
        self.bridge_art = load('circuit-bridge')
        self.hatch_art = load('circuit-hatch')
        self.busbar_art = (load('hall-busbar-live'), load('hall-busbar-safe'))
        self.shutter_art = (load('shutter-closed'), load('shutter-open'))
        self.relay_art = (load('relay-off'), load('relay-on'))
        rotor = background['rotor']
        self.rotor = load(rotor['prop'])
        self.fan_bounds = self._rect(*rotor['rect'])
        self.rotor_diameter = rotor['diameter_px']
        self.rotor_speed = rotor['degrees_per_second']
        self.rotor_angle = 0.0
        self.items = [RenderItem(self._draw_background, draw_order=-5)]
        self.items.append(RenderItem(self._draw_busbar, -2, self.busbar))
        ceilings = {tuple(point) for point in background['ceilings']}
        for rect, collider in zip(data['collision']['rects'], self.terrain, strict=True):
            bounds = collider.bounds_at((0, 0))
            edge = (42, 57, 68) if tuple(rect[:2]) in ceilings else (91, 110, 117)
            self.items.append(RenderItem(partial(self._draw_structure, bounds, edge=edge), -2, bounds))
        for kind, bounds in self.devices:
            left, bottom, right, top = bounds
            if kind == 'shutter':
                right = left + self.shutter_art[0].w * 2
            artwork = (left, bottom, right, top)
            self.items.append(RenderItem(partial(self._draw_device, kind, artwork), -2, artwork))
        x, y = self.relay
        feet = y - 41.5
        bounds = (x - self.relay_art[0].w, feet, x + self.relay_art[0].w, feet + self.relay_art[0].h * 2)
        self.items.append(RenderItem(partial(self._draw_powered, self.relay_art, bounds), -2, bounds))
        x, y = self.hatch_release
        feet = y - 41.5
        bounds = (x - 26, feet, x + 26, feet + 61)
        self.items.append(RenderItem(partial(self._draw_hatch_release, bounds), -2, bounds))
        for obj in data['objects']:
            image = load(obj['prop'])
            scale = obj.get('scale', 1)
            flip = obj.get('flip_x', False)
            anchor_x, anchor_y = obj['anchor_px']
            if flip:
                anchor_x = image.w - anchor_x
            bounds = self._rect(obj['x'] - anchor_x * scale, obj['y'] - anchor_y * scale,
                                image.w * scale, image.h * scale)
            if obj['id'] == 'output-socket':
                lit = load('output-lit')
                draw = partial(self._draw_socket, image, lit, bounds)
            elif 'powered_prop' in obj:
                lit = load(obj['powered_prop'])
                draw = partial(self._draw_powered, (image, lit), bounds)
            else:
                draw = partial(self._draw, image, bounds, flip)
            self.items.append(RenderItem(draw, DRAW_ORDER[obj['layer']], bounds, opacity=obj.get('opacity', 1)))

    def _point(self, x, y):
        return x - self.half_width, self.half_height - y

    def _rect(self, x, y, w, h):
        left, top = self._point(x, y)
        return left, top - h, left + w, top

    def room_at(self, position):
        x, y = position
        return next((room for room, (left, bottom, right, top) in self.rooms.items()
                     if left <= x < right and bottom < y <= top), None)

    def update(self, dt):
        self.rotor_angle = (self.rotor_angle + self.rotor_speed * dt) % 360

    def reset(self):
        self.reached_output = False
        self.power_restored = False
        self.hatch_released = False
        self.boss_defeated = False
        self._place_devices()

    def defeat_boss(self):
        self.boss_defeated = True
        self._place_devices()

    def _place_devices(self):
        self.closed_shutters = tuple(bounds for kind, bounds in self.devices
                                     if (kind in ('shutter', 'powered-hatch') and not self.power_restored)
                                     or (kind == 'hatch' and not self.hatch_released)
                                     or (kind == 'boss-shutter' and not self.boss_defeated))
        active_bridges = tuple(bounds for kind, bounds in self.devices
                               if kind == 'bridge' and self.power_restored)
        self.colliders = self.terrain + tuple(
            Collider(bounds, 'terrain', blocks={'player', 'enemy'})
            for bounds in self.closed_shutters + active_bridges)

    def _interaction(self, player):
        if not player.hp or not player.grounded:
            return None
        px, py = player.center
        if not self.power_restored and hypot(self.relay[0] - px, self.relay[1] - py) <= self.relay_reach:
            return 'relay'
        if not self.hatch_released and hypot(self.hatch_release[0] - px, self.hatch_release[1] - py) <= self.hatch_reach:
            return 'hatch'
        return None

    def interaction_hint(self, player):
        return {'relay': 'W  RESTORE POWER', 'hatch': 'W  RELEASE HATCH'}.get(self._interaction(player))

    def navigation_hint(self, player):
        if self.boss_defeated:
            return None
        x, y = player.collision_position
        left, bottom, right, top = self.relay_return if self.power_restored else self.fork_approach
        if left <= x <= right and bottom <= y <= top:
            if self.power_restored:
                return 'LEFT AND UP TO LOAD TEST'
            return 'DROP TO COOLING  /  JUMP RIGHT FROM THE EDGE'
        return None

    def interact(self, player):
        action = self._interaction(player)
        if action == 'relay':
            self.power_restored = True
        elif action == 'hatch':
            self.hatch_released = True
        else:
            return
        self._place_devices()

    def damage_on_busbar(self, player):
        if (not self.power_restored and not player.teleport_guard_remaining
                and overlaps(player.hurt_box, self.busbar)):
            left, _, right, _ = self.busbar
            player.take_hit(-1 if player.x < (left + right) / 2 else 1)

    def blocks_teleport(self, player, x, y):
        cx, cy = player.center
        if self.room_at((x, y)) != self.room_at((cx, cy)):
            return True
        left, bottom, right, top = self.output_lock
        if not self.power_restored and left <= x <= right and bottom <= y <= top:
            return True
        return any(blocking_contact(player.hurt_box, bounds, (x - cx, y - cy)) is not None
                   for bounds in self.closed_shutters + self.teleport_barriers)

    def check_output(self, player):
        if (self.reached_output or not self.power_restored or not self.boss_defeated
                or not player.hp or not player.grounded):
            return False
        x, y = player.center
        self.reached_output = hypot(x - self.output[0], y - self.output[1]) <= self.output_reach
        return self.reached_output

    def _draw_background(self, transform, opacity):
        draw_rect(transform, transform.bounds, (9, 15, 22), opacity)
        if overlaps(self.fan_bounds, transform.bounds):
            left, bottom, right, top = self.fan_bounds
            x, y = (left + right) / 2, (bottom + top) / 2
            radius = self.rotor_diameter / 2
            draw_image(self.fan_cavity, transform, self.fan_bounds, opacity * .82)
            draw_image(self.rotor, transform, (x - radius, y - radius, x + radius, y + radius),
                       opacity * .65, angle=self.rotor_angle)

    @staticmethod
    def _draw_structure(bounds, transform, opacity, edge=(91, 110, 117)):
        left, bottom, right, top = bounds
        draw_rect(transform, bounds, (22, 32, 41), opacity)
        if right - left >= 64:
            draw_rect(transform, (left, top - 4, right, top), edge, opacity)
            if top - bottom >= 22:
                draw_rect(transform, (left + 4, top - 14, right - 4, top - 10), (39, 53, 63), opacity)
        else:
            draw_rect(transform, (left + 4, bottom, left + 7, top), (49, 66, 76), opacity)

    def _draw_busbar(self, transform, opacity):
        draw_image(self.busbar_art[self.power_restored], transform, self.busbar, opacity)

    def _draw_device(self, kind, bounds, transform, opacity):
        left, bottom, right, top = bounds
        if kind == 'bridge':
            if self.power_restored:
                draw_image(self.bridge_art, transform, bounds, opacity)
            else:
                for x in (left, right - 12):
                    draw_rect(transform, (x, top - 10, x + 12, top), (136, 92, 57), opacity)
            return
        if kind in ('hatch', 'powered-hatch'):
            opened = self.hatch_released if kind == 'hatch' else self.power_restored
            if not opened:
                draw_image(self.hatch_art, transform, bounds, opacity)
            for edge in (left, right - 12):
                draw_rect(transform, (edge, bottom, edge + 12, top),
                          (81, 157, 144) if opened else (172, 120, 62), opacity)
            return
        opened = self.boss_defeated if kind == 'boss-shutter' else self.power_restored
        image = self.shutter_art[opened]
        lower = top - image.h * 2 if opened else bottom
        draw_image(image, transform, (left, lower, right, top), opacity)

    def _draw_hatch_release(self, bounds, transform, opacity):
        draw_image(self.relay_art[self.hatch_released], transform, bounds, opacity)

    def _draw_powered(self, images, bounds, transform, opacity):
        draw_image(images[self.power_restored], transform, bounds, opacity)

    def _draw_socket(self, image, lit, bounds, transform, opacity):
        draw_image(lit if self.reached_output else image, transform, bounds, opacity)

    @staticmethod
    def _draw(image, bounds, flip, transform, opacity):
        draw_image(image, transform, bounds, opacity, flip_x=flip)

    def render_items(self):
        return self.items
