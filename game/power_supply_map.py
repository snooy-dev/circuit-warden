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
        self.terrain = tuple(
            Collider(self._rect(*rect), 'terrain', blocks={'player', 'enemy'})
            for rect in data['collision']['rects'])
        self.devices = tuple((item['kind'], self._rect(*item['rect']))
                             for item in data['collision']['power_devices'])
        self.busbar = self._rect(*data['collision']['busbar'])
        relay = next(item for item in data['interactions'] if item['id'] == 'relay')
        self.relay = self._point(relay['x'], relay['y'])
        self.relay_reach = relay['reach']
        spawns = {entry['id']: self._point(entry['x'], entry['feet_y']) for entry in data['spawns']}
        self.player_start, self.enemy_start = spawns['start'], spawns['metal-dust']
        player_spawn = next(entry for entry in data['spawns'] if entry['id'] == 'start')
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
        self.chamber_light = load('chamber-light')
        self.bridge_art = load('return-bridge')
        self.shutter_art = (load('shutter-closed'), load('shutter-open'))
        self.relay_art = (load('relay-off'), load('relay-on'))
        self.chambers = tuple((self._rect(*room['rect']), room['color']) for room in background['chambers'])
        self.girders = tuple(self._rect(*rect) for rect in background['girders'])
        self.lights = tuple(self._rect(*rect) for rect in background['lights'])
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
            elif obj['id'] == 'relay-feed':
                lit = load('feed-wire-on')
                draw = partial(self._draw_powered, (image, lit), bounds)
            else:
                draw = partial(self._draw, image, bounds, flip)
            self.items.append(RenderItem(draw, DRAW_ORDER[obj['layer']], bounds, opacity=obj.get('opacity', 1)))

    def _point(self, x, y):
        return x - self.half_width, self.half_height - y

    def _rect(self, x, y, w, h):
        left, top = self._point(x, y)
        return left, top - h, left + w, top

    def update(self, dt):
        self.rotor_angle = (self.rotor_angle + self.rotor_speed * dt) % 360

    def reset(self):
        self.reached_output = False
        self.power_restored = False
        self._place_devices()

    def _place_devices(self):
        self.closed_shutters = tuple(bounds for kind, bounds in self.devices
                                     if kind == 'shutter' and not self.power_restored)
        active_bridges = tuple(bounds for kind, bounds in self.devices
                               if kind == 'bridge' and self.power_restored)
        self.colliders = self.terrain + tuple(
            Collider(bounds, 'terrain', blocks={'player', 'enemy'})
            for bounds in self.closed_shutters + active_bridges)

    def near_relay(self, player):
        if not player.hp or not player.grounded or self.power_restored:
            return False
        x, y = self.relay
        px, py = player.center
        return hypot(x - px, y - py) <= self.relay_reach

    def restore_power(self, player):
        if self.near_relay(player):
            self.power_restored = True
            self._place_devices()

    def damage_on_busbar(self, player):
        if (not self.power_restored and not player.teleport_guard_remaining
                and overlaps(player.hurt_box, self.busbar)):
            left, _, right, _ = self.busbar
            player.take_hit(-1 if player.x < (left + right) / 2 else 1)

    def blocks_teleport(self, player, x, y):
        if self.power_restored:
            return False
        left, bottom, right, top = self.output_lock
        if left <= x <= right and bottom <= y <= top:
            return True
        cx, cy = player.center
        return any(blocking_contact(player.hurt_box, bounds, (x - cx, y - cy)) is not None
                   for bounds in self.closed_shutters)

    def check_output(self, player):
        if self.reached_output or not self.power_restored or not player.hp or not player.grounded:
            return False
        x, y = player.center
        self.reached_output = hypot(x - self.output[0], y - self.output[1]) <= self.output_reach
        return self.reached_output

    def _draw_background(self, transform, opacity):
        draw_rect(transform, transform.bounds, (9, 15, 22), opacity)
        for bounds, color in self.chambers:
            if overlaps(bounds, transform.bounds):
                left, bottom, right, top = bounds
                draw_rect(transform, bounds, tuple(max(0, value - 8) for value in color), opacity)
                draw_rect(transform, (left + 12, bottom, right - 12, top - 20), color, opacity)
        for bounds in self.girders:
            if overlaps(bounds, transform.bounds):
                left, bottom, right, top = bounds
                draw_rect(transform, bounds, (18, 29, 38), opacity)
                draw_rect(transform, (left + 5, bottom, left + 9, top), (36, 54, 63), opacity)
        for bounds in self.lights:
            if overlaps(bounds, transform.bounds):
                draw_image(self.chamber_light, transform, bounds, opacity)
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
        left, _, right, top = self.busbar
        body, edge = (((44, 70, 76), (99, 154, 156)) if self.power_restored
                      else ((102, 58, 25), (248, 177, 64)))
        draw_rect(transform, self.busbar, body, opacity)
        draw_rect(transform, (left, top - 4, right, top), edge, opacity)

    def _draw_device(self, kind, bounds, transform, opacity):
        left, _, right, top = bounds
        if kind == 'bridge':
            if self.power_restored:
                draw_image(self.bridge_art, transform, bounds, opacity)
            else:
                for x in (left, right - 12):
                    draw_rect(transform, (x, top - 10, x + 12, top), (136, 92, 57), opacity)
            return
        image = self.shutter_art[self.power_restored]
        draw_image(image, transform, (left, top - image.h * 2, right, top), opacity)

    def _draw_powered(self, images, bounds, transform, opacity):
        draw_image(images[self.power_restored], transform, bounds, opacity)

    def _draw_socket(self, image, lit, bounds, transform, opacity):
        draw_image(lit if self.reached_output else image, transform, bounds, opacity)

    @staticmethod
    def _draw(image, bounds, flip, transform, opacity):
        draw_image(image, transform, bounds, opacity, flip_x=flip)

    def render_items(self):
        return self.items
