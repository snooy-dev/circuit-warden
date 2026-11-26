"""전원 구역의 조작 인계와 전하 활성 안내."""

from types import SimpleNamespace

import pico2d.pico2d as pico

from game.scene import DEFAULT_SIZE
from game.story_intro import PowerOpening
from .test_power_supply_enemies import PowerSupplyFixture


class PowerSupplyFlowTests(PowerSupplyFixture):
    def test_cutscene_skip_accepts_following_movement_before_update(self):
        for shortcut in ('escape', 'click'):
            with self.subTest(shortcut=shortcut):
                scene = self.scene
                self.level.reset_combat()
                scene.opening = PowerOpening(self.level, DEFAULT_SIZE)
                if shortcut == 'escape':
                    self.assertTrue(scene.handle_escape())
                else:
                    transform = scene.opening.canvas.transform(scene.engine.viewport)
                    scene.engine.event_to_output.return_value = transform.point(
                        transform.bounds[2] - 80, transform.bounds[3] - 26)
                    for kind in (pico.SDL_MOUSEBUTTONDOWN, pico.SDL_MOUSEBUTTONUP):
                        scene.handle_event(SimpleNamespace(type=kind, button=pico.SDL_BUTTON_LEFT))
                self.assertIsNone(scene.opening)
                start = scene.character.x
                scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
                scene.update(.1)
                self.assertGreater(scene.character.x, start)

    def test_charge_activation_requires_open_path_and_visible_destination(self):
        scene = self.scene
        actor, layout = scene.character, self.level.layout
        charge = self.level.charges[0]
        actor.x, actor.y = layout._point(1593, 1016)
        actor.view_bounds = layout.rooms['relay-tower']
        charge.position = layout._point(1844, 1072)
        self.assertTrue(charge.in_range(actor.center))
        self.assertTrue(layout.blocks_teleport(actor, *charge.position))
        charge.update(0)
        self.assertFalse(charge.active)

        actor.x, actor.y = -1326, -574
        charge.position = -1326, -584
        actor.view_bounds = (-1966, -579, -686, 141)
        self.assertTrue(charge.in_range(actor.center))
        self.assertFalse(layout.blocks_teleport(actor, *charge.position))
        self.assertTrue(actor.can_place_center(charge.position))
        charge.update(0)
        self.assertFalse(charge.active)
        left, _, right, top = actor.view_bounds
        actor.view_bounds = left, -650, right, top
        charge.update(0)
        self.assertTrue(charge.active)
