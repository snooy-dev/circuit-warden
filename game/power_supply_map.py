"""파워서플라이 맵의 배치·충돌·렌더링."""

import json
from functools import partial
from math import hypot
from pathlib import Path

import pico2d.pico2d as pico

from engine.rendering.drawing import _sdl
from game_framework import Collider, GameObject, RenderItem, draw_image


MAP_FILE = Path(__file__).resolve().parents[1] / 'assets/levels/power-supply/map.json'
DRAW_ORDER = {'rear': -4, 'structure': -2, 'front': 4}


class PowerSupplyMap(GameObject):
    def __init__(self, images):
        super().__init__()
        data = json.loads(MAP_FILE.read_text(encoding='utf-8'))
        world = data['world']
        self.half_width, self.half_height = world['width'] / 2, world['height'] / 2
        self.bounds = self._rect(0, 0, world['width'], world['height'])
        self.colliders = tuple(
            Collider(self._rect(*rect), 'terrain', blocks={'player', 'enemy'})
            for rect in data['collision']['rects'])
        spawns = {entry['id']: self._point(entry['x'], entry['feet_y']) for entry in data['spawns']}
        self.player_start, self.enemy_start = spawns['start'], spawns['metal-dust']
        player_spawn = next(entry for entry in data['spawns'] if entry['id'] == 'start')
        self.power_entry = self._point(*player_spawn['entry_origin'])
        self.charge_sites = tuple(tuple(self._point(*point) for point in anchor['variants'])
                                  for anchor in data['anchors'].values())
        output = next(item for item in data['interactions'] if item['id'] == 'output')
        self.output = self._point(output['x'], output['y'])
        self.output_reach = output['reach']
        self.reached_output = False

        def load(file):
            image = images.load(MAP_FILE.parent / file)._borrow()
            _sdl(pico.SDL_SetTextureScaleMode(image.texture, pico.SDL_ScaleModeNearest))
            return image

        background = data['layers'][0]
        self.parallax = background['parallax_x']
        self.background = load(background['runtime_image'])
        self.background_height = background['runtime_height']
        rotor = background['rotor']
        self.rotor = load(data['props'][rotor['prop']]['image'])
        self.rotor_center = rotor['center_px']
        self.rotor_diameter = rotor['diameter_px']
        self.rotor_speed = rotor['degrees_per_second']
        self.rotor_angle = 0.0
        self.items = [RenderItem(self._draw_background, draw_order=-5)]
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
            else:
                draw = partial(self._draw, image, bounds, flip)
            self.items.append(RenderItem(draw, DRAW_ORDER[obj['layer']], bounds))

    def _point(self, x, y):
        return x - self.half_width, self.half_height - y

    def _rect(self, x, y, w, h):
        left, top = self._point(x, y)
        return left, top - h, left + w, top

    def update(self, dt):
        self.rotor_angle = (self.rotor_angle + self.rotor_speed * dt) % 360

    def check_output(self, player):
        if self.reached_output or not player.hp or not player.grounded:
            return False
        x, y = player.center
        self.reached_output = hypot(x - self.output[0], y - self.output[1]) <= self.output_reach
        return self.reached_output

    def _draw_background(self, transform, opacity):
        left, _, right, _ = transform.bounds
        scale = max(self.background_height / self.background.h, (right - left) / self.background.w)
        half_width = self.background.w * scale / 2
        half_height = self.background.h * scale / 2
        camera_x, camera_y = transform.center
        center = min(max(camera_x * (1 - self.parallax), right - half_width), left + half_width)
        bounds = center - half_width, camera_y - half_height, center + half_width, camera_y + half_height
        draw_image(self.background, transform, bounds, opacity)
        rotor_x = bounds[0] + self.rotor_center[0] * scale
        rotor_y = bounds[3] - self.rotor_center[1] * scale
        radius = self.rotor_diameter * scale / 2
        rotor_bounds = rotor_x - radius, rotor_y - radius, rotor_x + radius, rotor_y + radius
        draw_image(self.rotor, transform, rotor_bounds, opacity, angle=self.rotor_angle)

    def _draw_socket(self, image, lit, bounds, transform, opacity):
        draw_image(lit if self.reached_output else image, transform, bounds, opacity)

    @staticmethod
    def _draw(image, bounds, flip, transform, opacity):
        draw_image(image, transform, bounds, opacity, flip_x=flip)

    def render_items(self):
        return self.items
