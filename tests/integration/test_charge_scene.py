import unittest
import weakref
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GROUND_Y
from game.scene import CharacterScene
from game.teleport_link import TeleportLink
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
        self.click((target.position[0] + 50, target.position[1]))
        scene.update(0)
        self.assertEqual(actor.state, 'attack')
        self.click((target.position[0] + 44, target.position[1]))
        self.assertEqual(actor.center, target.position)
        self.assertEqual(actor.jump_phase, 'rise')
        scene.update(0)
        scene.update(.1)
        self.click(target.position)
        self.assertEqual(actor.center, target.position)
        self.assertIsNone(actor.buffered_action)
        overlap = scene.level.charges[0]
        overlap.position = (target.position[0] + 70, target.position[1])
        scene.update(0)
        scene.update(.1)
        self.click((target.position[0] + 40, target.position[1]))
        self.assertEqual(actor.center, overlap.position)
        scene.update(0)
        scene.update(.1)
        actor.teleport((0, GROUND_Y + 83 / 2))
        far = scene.level.charges[-1]
        self.assertFalse(far.in_range(actor.center))
        self.click(far.position)
        scene.update(0)
        self.assertEqual(actor.state, 'attack')
        self.assertEqual(actor.x, 0)

    def test_resize_dpi_and_invalid_output_use_current_coordinates(self):
        scene = self.open_scene()
        target = scene.level.charges[2]
        for viewport, ratio in (((20, 10, 1280, 720), 1), ((0, 0, 1920, 1080), 2),
                                ((0, 0, 1024, 720), 1)):
            scene.update(0)
            scene.update(.1)
            self.app.viewport = viewport
            scene.update(0)
            scene.character.teleport((0, GROUND_Y + 83 / 2))
            self.app.event_to_output.side_effect = lambda event: (event.x * ratio, event.y * ratio)
            x, y = scene.transform.point(target.position[0] + 44, target.position[1])
            scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                button=pico.SDL_BUTTON_LEFT, x=x / ratio, y=y / ratio))
            self.assertEqual(scene.character.center, target.position)
        before = scene.character.center
        self.app.output_valid = False
        self.app.event_to_output.side_effect = lambda event: None
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                          button=pico.SDL_BUTTON_LEFT, x=100, y=100))
        self.assertEqual(scene.character.center, before)

    def test_link_endpoints_same_position_and_rapid_chain_lifetime(self):
        scene = self.open_scene()
        actor = scene.character
        start = actor.center
        first_target, second_target = scene.level.charges[2], scene.level.charges[3]
        self.click(first_target.position)
        first = next(o for o in scene.level.objects if isinstance(o, TeleportLink))
        self.assertEqual((first.start, first.end), (start, first_target.position))
        self.click(second_target.position)
        self.assertEqual(actor.center, first_target.position)
        self.assertIs(scene.level.mode.pending_charge, second_target)
        self.assertEqual(sum(isinstance(o, TeleportLink) for o in scene.level.objects), 1)
        scene.update(.05)
        scene.draw()
        self.assertEqual(first._uploaded_frame, 0)
        scene.update(.099)
        second_start = actor.center
        self.assertIs(scene.level.mode.teleport_link, first)
        scene.update(.001)
        second = [o for o in scene.level.objects if isinstance(o, TeleportLink)][-1]
        self.assertEqual(second.end, second_target.position)
        self.assertGreater(second.start[1], second_start[1])
        self.assertEqual(actor.center, second_target.position)
        self.assertIsNone(actor.buffered_action)
        self.assertIsNone(scene.level.mode.pending_charge)
        scene.update(0)
        scene.update(.03)
        self.assertIsNone(first.level)
        self.assertIs(second.level, scene.level)
        scene.exit()
        self.assertIsNone(second.texture)

    def test_destination_activation_and_last_valid_buffer(self):
        scene = self.open_scene()
        actor = scene.character
        first, second, last = scene.level.charges[2:5]
        self.assertFalse(last.in_range(actor.center))
        self.click(first.position)
        self.assertTrue(last.active)
        self.assertEqual(scene.level.mode.activation_origin, first.position)
        self.click((second.position[0] + 44, second.position[1]))
        self.click((last.position[0] - 44, last.position[1]))
        self.assertEqual(actor.center, first.position)
        scene.update(0)
        # 실제 중심이 범위를 벗어나도 진행 중 활성 기준은 도착점이다.
        actor.y -= 40
        self.assertFalse(last.in_range(actor.center))
        scene.update(.1)
        self.assertEqual(actor.center, last.position)
        self.assertIsNone(scene.level.mode.pending_charge)

    def test_buffered_link_expires_on_time_without_draw(self):
        scene = self.open_scene()
        self.click(scene.level.charges[2].position)
        self.click(scene.level.charges[3].position)
        scene.update(0)
        scene.update(.1)
        second = scene.level.mode.teleport_link
        self.assertIsNotNone(second)
        scene.update(.099)
        self.assertIs(second.level, scene.level)
        scene.update(.001)
        self.assertIsNone(second.level)
        self.assertIsNone(scene.level.mode.teleport_link)

    def test_buffer_clears_on_focus_invalid_output_or_invalid_destination(self):
        for reason in ('focus', 'output', 'destination', 'destroyed'):
            with self.subTest(reason=reason):
                scene = self.open_scene()
                first, target = scene.level.charges[2:4]
                self.click(first.position)
                self.click(target.position)
                scene.update(0)
                if reason == 'focus':
                    scene.handle_event(SimpleNamespace(type=pico.SDL_WINDOWEVENT,
                                                        event=pico.SDL_WINDOWEVENT_FOCUS_LOST))
                elif reason == 'output':
                    self.app.output_valid = False
                elif reason == 'destination':
                    target.position = (1000, 0)
                else:
                    target.destroy()
                scene.update(.1)
                self.assertEqual(scene.character.x, first.position[0])
                self.assertIsNone(scene.level.mode.pending_charge)
                scene.exit()
                self.app.output_valid = True

    def test_real_art_shared_phase_draw_and_cleanup(self):
        scene = self.open_scene()
        charges = scene.level.charges
        art = charges[0].art
        self.assertEqual(tuple(len(art.frames[n]) for n in ('inactive', 'active', 'pulse')), (72, 72, 10))
        self.assertTrue(all(art is charge.art for charge in charges))
        self.assertFalse(any(art.frames['pulse'][0][3::4]))
        self.assertFalse(any(art.frames['pulse'][-1][3::4]))
        for index in range(40):
            art.frame(index / 60, .5)
        self.assertLessEqual(len(art._composites), 16)
        self.assertLessEqual(len(art._pixels), 16)
        self.assertIs(art.frame(.7, .5), art.frame(.7, .5))
        for dt in (.08, .06, .1, .2, .6):
            scene.update(dt)
            scene.draw()
        self.assertTrue(any(c.value == 1 for c in charges))
        self.assertTrue(any(c.value == 0 for c in charges))
        scene.exit()
        self.assertTrue(all(c.texture is None and c.level is None for c in charges))
        ref = weakref.ref(art)
        del art
        self.assertIsNone(ref())

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
