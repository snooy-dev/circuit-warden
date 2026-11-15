import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GROUND_Y
from game.scene import CharacterScene
from tests.integration import test_character_scene as fixtures


class ChargeSceneTests(unittest.TestCase):
    setUp = fixtures.CharacterSceneTests.setUp

    def open_scene(self):
        self.scene = CharacterScene()
        self.scene.enter(self.app)
        self.addCleanup(self.scene.exit)
        return self.scene

    def click(self, position):
        x, y = self.scene.transform.point(*position)
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                button=pico.SDL_BUTTON_LEFT, x=x, y=y))

    def test_selection_priority_overlap_reuse_and_inactive_fallback(self):
        scene = self.open_scene()
        actor = scene.character
        target = scene.level.charges[2]
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                          button=pico.SDL_BUTTON_LEFT, x=0, y=0))
        scene.update(0)
        self.assertEqual(actor.state, 'attack')
        self.click(target.position)
        self.assertEqual(actor.center, target.position)
        self.assertEqual(actor.jump_phase, 'fall')
        actor.update(.05)
        self.click(target.position)
        self.assertEqual(actor.center, target.position)
        self.assertIsNone(actor.buffered_action)
        overlap = scene.level.charges[0]
        overlap.position = (target.position[0] + 5, target.position[1])
        self.click(overlap.position)
        self.assertEqual(actor.center, overlap.position)
        actor.teleport((0, GROUND_Y + 83 / 2))
        far = scene.level.charges[-1]
        self.assertFalse(far.in_range(actor))
        self.click(far.position)
        scene.update(0)
        self.assertEqual(actor.state, 'attack')
        self.assertEqual(actor.x, 0)

    def test_resize_dpi_and_invalid_output_use_current_coordinates(self):
        scene = self.open_scene()
        target = scene.level.charges[2]
        for viewport, ratio in (((20, 10, 1280, 720), 1), ((0, 0, 1920, 1080), 2),
                                ((0, 0, 1024, 720), 1)):
            self.app.viewport = viewport
            scene.update(0)
            scene.character.teleport((0, GROUND_Y + 83 / 2))
            self.app.event_to_output.side_effect = lambda event: (event.x * ratio, event.y * ratio)
            x, y = scene.transform.point(*target.position)
            scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                button=pico.SDL_BUTTON_LEFT, x=x / ratio, y=y / ratio))
            self.assertEqual(scene.character.center, target.position)
        before = scene.character.center
        self.app.output_valid = False
        self.app.event_to_output.side_effect = lambda event: None
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                          button=pico.SDL_BUTTON_LEFT, x=100, y=100))
        self.assertEqual(scene.character.center, before)

    def test_real_art_shared_phase_draw_and_cleanup(self):
        scene = self.open_scene()
        charges = scene.level.charges
        art = charges[0].art
        self.assertEqual(tuple(len(art.frames[n]) for n in ('inactive', 'active', 'pulse')), (72, 72, 10))
        self.assertTrue(all(art is charge.art for charge in charges))
        self.assertFalse(any(art.frames['pulse'][0][3::4]))
        self.assertFalse(any(art.frames['pulse'][-1][3::4]))
        for dt in (.08, .06, .1, .2, .6):
            scene.update(dt)
            scene.draw()
        self.assertTrue(any(c.value == 1 for c in charges))
        self.assertTrue(any(c.value == 0 for c in charges))
        scene.exit()
        self.assertTrue(all(c.texture is None and c.level is None for c in charges))

    def test_initialization_failure_releases_partial_charge_resources(self):
        scene = CharacterScene()
        create = pico.SDL_CreateTexture
        textures = []
        def fail_second(renderer, format, access, width, height):
            if textures:
                return None
            texture = create(renderer, format, access, width, height)
            textures.append(texture)
            return texture
        with patch.object(pico, 'SDL_CreateTexture', side_effect=fail_second), \
                patch.object(pico, 'SDL_DestroyTexture', wraps=pico.SDL_DestroyTexture) as destroy:
            with self.assertRaisesRegex(RuntimeError, '전하 텍스처'):
                scene.enter(self.app)
            self.assertTrue(any(call.args == (textures[0],) for call in destroy.call_args_list))
        self.assertTrue(scene.images.closed)
        self.assertEqual(scene.level.objects, ())
