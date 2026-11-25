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
ARC_PERIOD = 3.2
ARC_WARNING_START = 2.1
ARC_LIVE_START = 2.7
RELAY_REACH = 66


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
        self.devices = tuple((item['kind'], item['stage'], self._rect(*item['rect']))
                             for item in data['collision']['power_devices'])
        self.relays = tuple(self._point(item['x'], item['y']) for item in data['interactions']
                            if item['id'].startswith('relay-'))
        spawns = {entry['id']: self._point(entry['x'], entry['feet_y']) for entry in data['spawns']}
        self.player_start, self.enemy_start = spawns['start'], spawns['metal-dust']
        player_spawn = next(entry for entry in data['spawns'] if entry['id'] == 'start')
        self.power_entry = self._point(*player_spawn['entry_origin'])
        self.charge_sites = tuple(tuple(self._point(*point) for point in anchor['variants'])
                                  for anchor in data['anchors'].values())
        output = next(item for item in data['interactions'] if item['id'] == 'output')
        self.output = self._point(output['x'], output['y'])
        self.output_reach = output['reach']
        self.reset()

        def load(file):
            image = images.load(MAP_FILE.parent / file)._borrow()
            _sdl(pico.SDL_SetTextureScaleMode(image.texture, pico.SDL_ScaleModeNearest))
            return image

        background = data['layers'][0]
        self.fan_cavity = load(data['props']['fan-cavity']['image'])
        self.chamber_light = load(data['props']['chamber-light']['image'])
        self.chambers = tuple((self._rect(*room['rect']), room['color']) for room in background['chambers'])
        self.girders = tuple(self._rect(*rect) for rect in background['girders'])
        self.lights = tuple(self._rect(*rect) for rect in background['lights'])
        rotor = background['rotor']
        self.rotor = load(data['props'][rotor['prop']]['image'])
        self.fan_bounds = self._rect(*rotor['rect'])
        self.rotor_diameter = rotor['diameter_px']
        self.rotor_speed = rotor['degrees_per_second']
        self.rotor_angle = 0.0
        self.items = [RenderItem(self._draw_background, draw_order=-5)]
        ceilings = {tuple(point) for point in background['ceilings']}
        for rect, collider in zip(data['collision']['rects'], self.terrain, strict=True):
            bounds = collider.bounds_at((0, 0))
            edge = (42, 57, 68) if tuple(rect[:2]) in ceilings else (91, 110, 117)
            self.items.append(RenderItem(partial(self._draw_structure, bounds, edge=edge), -2, bounds))
        for kind, stage, bounds in self.devices:
            self.items.append(RenderItem(partial(self._draw_device, kind, stage, bounds), -2, bounds))
        for index, (x, y) in enumerate(self.relays):
            bounds = (x - 42, y - 40, x + 42, y + 62)
            self.items.append(RenderItem(partial(self._draw_relay, index, bounds), -2, bounds))
        for obj in data['objects']:
            image = load(data['props'][obj['prop']]['image'])
            scale = obj.get('scale', 1)
            flip = obj.get('flip_x', False)
            anchor_x, anchor_y = obj['anchor_px']
            if flip:
                anchor_x = image.w - anchor_x
            bounds = self._rect(obj['x'] - anchor_x * scale, obj['y'] - anchor_y * scale,
                                image.w * scale, image.h * scale)
            if obj['id'] == 'output-socket':
                lit = load(data['props']['output-lit']['image'])
                draw = partial(self._draw_socket, image, lit, bounds)
            elif obj['id'] == 'arc-emitter':
                self.arc_images = (image, *(load(data['props'][prop]['image']) for prop in obj['active_props']))
                self.arc_hit_box = self._rect(*obj['hit_rect'])
                draw = partial(self._draw_arc, bounds)
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
        self.arc_elapsed = (self.arc_elapsed + dt) % ARC_PERIOD

    def reset(self):
        self.reached_output = False
        self.arc_elapsed = 0.0
        self.power_stage = 0
        self._place_devices()

    def _place_devices(self):
        self.closed_shutters = tuple(bounds for kind, stage, bounds in self.devices
                                     if kind == 'shutter' and self.power_stage < stage)
        active_bridges = tuple(bounds for kind, stage, bounds in self.devices
                               if kind == 'bridge' and self.power_stage >= stage)
        self.colliders = self.terrain + tuple(
            Collider(bounds, 'terrain', blocks={'player', 'enemy'})
            for bounds in self.closed_shutters + active_bridges)

    def near_relay(self, player):
        if not player.hp or not player.grounded or self.power_stage >= len(self.relays):
            return False
        x, y = self.relays[self.power_stage]
        px, py = player.center
        return hypot(x - px, y - py) <= RELAY_REACH

    def restore_power(self, player):
        if self.near_relay(player):
            self.power_stage += 1
            self._place_devices()

    def blocks_teleport(self, player, x, y):
        cx, cy = player.center
        return any(blocking_contact(player.hurt_box, bounds, (x - cx, y - cy)) is not None
                   for bounds in self.closed_shutters)

    @property
    def arc_phase(self):
        if self.arc_elapsed >= ARC_LIVE_START:
            return 2
        return int(self.arc_elapsed >= ARC_WARNING_START)

    def check_arc(self, player):
        if self.arc_phase == 2 and overlaps(player.hurt_box, self.arc_hit_box):
            left, _, right, _ = self.arc_hit_box
            player.take_hit(direction=-1 if player.x < (left + right) / 2 else 1)

    def check_output(self, player):
        if self.reached_output or self.power_stage < len(self.relays) or not player.hp or not player.grounded:
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

    def _draw_device(self, kind, stage, bounds, transform, opacity):
        left, bottom, right, top = bounds
        powered = self.power_stage >= stage
        if kind == 'bridge':
            if powered:
                self._draw_structure(bounds, transform, opacity, (108, 181, 176))
            for x in (left, right - 12):
                draw_rect(transform, (x, top - 10, x + 12, top + 2),
                          (108, 181, 176) if powered else (109, 81, 53), opacity)
            return
        height = 22 if powered else top - bottom
        draw_rect(transform, (left, top - height, right, top), (44, 60, 70), opacity)
        draw_rect(transform, (left + 4, top - height, left + 9, top), (72, 93, 103), opacity)
        if not powered:
            for index in range(stage):
                y = bottom + 54 + index * 15
                color = (99, 202, 187) if self.power_stage > index else (213, 143, 72)
                draw_rect(transform, (left + 12, y, right - 7, y + 6), color, opacity)

    def _draw_relay(self, index, bounds, transform, opacity):
        left, bottom, right, top = bounds
        draw_rect(transform, bounds, (30, 46, 56), opacity)
        draw_rect(transform, (left + 5, top - 6, right - 5, top), (83, 102, 109), opacity)
        color = ((98, 206, 187) if self.power_stage > index else
                 (232, 170, 87) if self.power_stage == index else (69, 78, 83))
        draw_rect(transform, (left + 26, bottom + 47, right - 26, bottom + 71), color, opacity)
        draw_rect(transform, (left + 15, bottom + 18, right - 15, bottom + 23), (63, 83, 94), opacity)

    def _draw_socket(self, image, lit, bounds, transform, opacity):
        draw_image(lit if self.reached_output else image, transform, bounds, opacity)

    def _draw_arc(self, bounds, transform, opacity):
        draw_image(self.arc_images[self.arc_phase], transform, bounds, opacity)

    @staticmethod
    def _draw(image, bounds, flip, transform, opacity):
        draw_image(image, transform, bounds, opacity, flip_x=flip)

    def render_items(self):
        return self.items
