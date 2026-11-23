import json
import unittest
import weakref
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.charge import ASSETS
from game.character import GROUND_Y
from game.scene import CAST_COOLDOWN, ENVIRONMENT_RECHARGE, CharacterScene
from game.teleport_link import TeleportLink
from tests.integration import test_character_scene as fixtures


class ChargeSceneTests(unittest.TestCase):
    setUp = fixtures.CharacterSceneTests.setUp

    def open_scene(self):
        self.scene = CharacterScene()
        self.scene.enter(self.app)
        self.addCleanup(self.scene.exit)
        return self.scene

    def click(self, position, button=pico.SDL_BUTTON_LEFT):
        x, y = self.scene.transform.point(*position)
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                button=button, x=x, y=y))

    def key(self, key, kind=pico.SDL_KEYDOWN):
        self.scene.handle_event(SimpleNamespace(type=kind, key=key))

    def test_skill_cast_preserves_air_action_and_is_spent_once(self):
        scene = self.open_scene()
        actor, level = scene.character, scene.level
        level.enemy.destroy()
        self.key(pico.SDLK_SPACE)
        scene.update(.18)
        self.assertFalse(actor.grounded)
        before = actor.center, actor.state
        aim = (-100, -25)
        level.mode.cursor_to_world = lambda: aim

        self.key(pico.SDLK_e)
        charge = level.skill_charge
        self.assertEqual((charge.position, charge.active), (aim, True))
        self.assertIs(charge.art, level.charges[0].art)
        self.assertEqual((actor.center, actor.state), before)

        self.click((0, 0), pico.SDL_BUTTON_RIGHT)
        self.assertEqual(actor.center, aim)
        self.assertTrue(charge.spent)
        self.assertIsNone(charge.level)
        self.assertNotIn(charge, level.charges)
        aim = (75, -10)
        scene.update(CAST_COOLDOWN - .001)
        self.key(pico.SDLK_e, pico.SDL_KEYUP)
        self.key(pico.SDLK_e)
        self.assertIsNone(level.skill_charge)
        scene.update(.001)
        self.key(pico.SDLK_e)
        self.assertIsNone(level.skill_charge, '키 반복은 재사용 대기가 끝나도 새 입력이 아니다.')
        self.key(pico.SDLK_e, pico.SDL_KEYUP)
        self.key(pico.SDLK_e)
        second = level.skill_charge
        self.assertEqual(second.position, aim)

        aim = (65, 75)
        scene.update(CAST_COOLDOWN)
        self.key(pico.SDLK_e, pico.SDL_KEYUP)
        self.key(pico.SDLK_e)
        self.assertIs(level.skill_charge, second)
        self.key(pico.SDLK_r)
        self.assertIsNone(second.level)
        self.assertIsNone(level.skill_charge)
        self.key(pico.SDLK_e, pico.SDL_KEYUP)
        self.key(pico.SDLK_e)
        self.assertEqual(level.skill_charge.position, aim)

    def test_skill_rejects_unusable_aim_without_charging_cooldown(self):
        scene = self.open_scene()
        actor, level = scene.character, scene.level
        for aim in (None, actor.center, (0, 205), (50, -220),
                    level.charges[2].position, (level.enemy.x, actor.center[1])):
            with self.subTest(aim=aim):
                level.mode.cursor_to_world = lambda: aim
                self.key(pico.SDLK_e)
                self.key(pico.SDLK_e, pico.SDL_KEYUP)
                self.assertIsNone(level.skill_charge)

        low, high = (-100, -20), (100, -20)
        level.mode.cursor_to_world = lambda: low
        self.app.output_valid = False
        self.key(pico.SDLK_e)
        self.key(pico.SDLK_e, pico.SDL_KEYUP)
        self.assertIsNone(level.skill_charge)
        self.app.output_valid = True
        level.mode.cursor_to_world = lambda: high
        self.key(pico.SDLK_e)
        self.assertEqual(level.skill_charge.position, high)

    def test_skill_cursor_uses_current_window_to_output_mapping(self):
        scene = self.open_scene()
        self.app.viewport = (20, 10, 1280, 720)
        aim = (-100, -25)
        x, y = scene.transform.point(*aim)
        self.app.window_to_output.side_effect = lambda wx, wy: (wx * 2, wy * 2)

        def mouse_state(wx, wy):
            wx._obj.value, wy._obj.value = round(x / 2), round(y / 2)

        with (patch.object(pico, 'SDL_GetWindowFlags', return_value=0) as flags,
              patch.object(pico, 'SDL_GetMouseState', side_effect=mouse_state)):
            self.key(pico.SDLK_e)
            self.assertIsNone(scene.level.skill_charge)
            self.key(pico.SDLK_e, pico.SDL_KEYUP)
            flags.return_value = pico.SDL_WINDOW_MOUSE_FOCUS
            self.key(pico.SDLK_e)
            for actual, expected in zip(scene.level.skill_charge.position, aim):
                self.assertAlmostEqual(actual, expected, delta=1)

    def test_environment_replaces_consumed_charge_after_delay_even_after_enemy_defeat(self):
        scene = self.open_scene()
        level = scene.level
        level.enemy.destroy()
        charge = level.charges[2]
        self.click(charge.position)
        scene.update(0)
        scene.update(ENVIRONMENT_RECHARGE - .001)
        self.assertIs(level.charges[2], charge)
        self.assertTrue(charge.spent)
        self.assertEqual(charge.render_items(), ())

        scene.update(.001)
        fresh = level.charges[2]
        self.assertIsNone(charge.level)
        self.assertNotEqual(fresh.position, charge.position)
        self.assertIs(fresh.art, level.charge_art)
        self.assertTrue(fresh.render_items())
        self.assertFalse(fresh.spent)
        self.click(fresh.position)
        self.assertEqual(scene.character.center, fresh.position)
        self.assertTrue(fresh.spent)

    def test_environment_retries_a_blocked_site_without_reusing_spent_object(self):
        scene = self.open_scene()
        actor, level = scene.character, scene.level
        charge = level.charges[2]
        self.click(charge.position)
        actor.teleport((-200, GROUND_Y + 83 / 2))
        level.enemy.x, level.enemy.state, level.enemy.state_remaining = 146, 'recover', 10
        scene.update(ENVIRONMENT_RECHARGE)
        self.assertIs(level.charges[2], charge)
        self.assertTrue(charge.spent)
        level.enemy.destroy()
        scene.update(.01)
        self.assertIsNot(level.charges[2], charge)
        self.assertFalse(level.charges[2].spent)

    def test_right_click_nearest_ignores_cursor_and_filters_invalid_targets(self):
        scene = self.open_scene()
        actor = scene.character
        x, y = actor.center
        invalid, first, tied, inactive, destroyed = scene.level.charges
        invalid.position = (x, y - 1)
        first.position = (x - 100, y)
        tied.position = (x + 100, y)
        inactive.position = (x + 1000, y)
        destroyed.position = (x, y)
        destroyed.destroy()
        self.click(tied.position, pico.SDL_BUTTON_RIGHT)
        self.assertEqual(actor.center, first.position)
        self.assertEqual(actor.jump_phase, None)
        self.assertIsNone(actor.buffered_action)
        self.assertEqual(scene.level.mode.teleport_link.end, first.position)

    def test_right_click_without_target_or_valid_output_does_nothing(self):
        scene = self.open_scene()
        actor = scene.character
        before = actor.center, actor.state
        original = [charge.position for charge in scene.level.charges]
        for charge in scene.level.charges:
            charge.position = (1000, 0)
        self.click((0, 0), pico.SDL_BUTTON_RIGHT)
        scene.update(0)
        self.assertEqual((actor.center, actor.state), before)
        self.assertIsNone(actor.buffered_action)
        self.assertIsNone(scene.level.mode.teleport_link)
        for charge, position in zip(scene.level.charges, original):
            charge.position = position
        self.app.output_valid = False
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                          button=pico.SDL_BUTTON_RIGHT, x=0, y=0))
        self.assertEqual((actor.center, actor.state), before)
        self.assertIsNone(scene.level.mode.pending_charge)

    def test_right_click_shares_last_valid_buffer_and_destination_origin(self):
        scene = self.open_scene()
        scene.level.enemy.destroy()
        actor = scene.character
        first, nearest, last = scene.level.charges[2:5]
        self.click(first.position)
        link = scene.level.mode.teleport_link
        origin = first.position
        nearest.position = (origin[0] + 40, origin[1])
        last.position = (origin[0] + 80, origin[1])
        self.click(last.position)
        actor.x = last.position[0]
        self.click(last.position, pico.SDL_BUTTON_RIGHT)
        self.assertIs(scene.level.mode.pending_charge, nearest)
        self.assertTrue(first.spent)
        self.assertIs(scene.level.mode.teleport_link, link)
        self.click(last.position)
        self.assertIs(scene.level.mode.pending_charge, last)
        self.click((0, 0), pico.SDL_BUTTON_RIGHT)
        scene.update(0)
        scene.update(.1)
        self.assertEqual(actor.center, nearest.position)
        self.assertTrue(nearest.spent)
        self.assertIsNone(scene.level.mode.pending_charge)
        self.assertIsNone(actor.buffered_action)

    def test_spent_charge_stays_excluded_after_landing_and_r_restores_it(self):
        scene = self.open_scene()
        actor = scene.character
        first, second = scene.level.charges[2:4]
        for charge in scene.level.charges:
            charge.position = (1000, 0)
        first.position, second.position = (100, 0), (160, 0)
        self.click(first.position)
        self.click((0, 0), pico.SDL_BUTTON_RIGHT)
        self.assertTrue(first.spent)
        self.assertFalse(first.active)
        self.assertEqual(first.render_items(), ())
        self.assertFalse(second.spent)
        self.assertIs(scene.level.mode.pending_charge, second)
        scene.update(0)
        scene.update(.1)
        self.assertTrue(second.spent)
        self.assertEqual(actor.center, second.position)
        for _ in range(80):
            scene.update(.01)
            if actor.grounded:
                break
        self.assertTrue(actor.grounded)
        before = actor.center
        self.click((0, 0), pico.SDL_BUTTON_RIGHT)
        self.assertEqual(actor.center, before)
        self.assertIsNone(scene.level.mode.teleport_link)
        self.click(first.position)
        self.assertEqual(actor.buffered_action, 'attack')
        self.assertEqual(actor.center, before)

        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_r))
        self.assertIsNone(first.level)
        self.assertIsNone(second.level)
        fresh = scene.level.charges[2]
        self.assertFalse(fresh.spent)
        self.assertTrue(fresh.render_items())
        self.click(fresh.position)
        self.assertEqual(scene.character.center, fresh.position)
        self.assertTrue(fresh.spent)

    def test_right_click_same_position_does_not_create_link(self):
        scene = self.open_scene()
        target = scene.level.charges[2]
        scene.character.teleport(target.position)
        velocity = scene.character.velocity_y
        self.click((0, 0), pico.SDL_BUTTON_RIGHT)
        self.assertEqual(scene.character.center, target.position)
        self.assertEqual(scene.character.velocity_y, velocity)
        self.assertFalse(target.spent)
        self.assertIsNone(scene.level.mode.teleport_link)

    def test_selection_priority_overlap_and_inactive_fallback(self):
        scene = self.open_scene()
        scene.level.enemy.destroy()
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
        for viewport, ratio in (((20, 10, 1280, 720), 1), ((0, 0, 1920, 1080), 2),
                                ((0, 0, 1024, 720), 1)):
            scene.level.reset_combat()
            target = scene.level.charges[2]
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
        self.assertEqual(first.frame_index, 0)
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
        self.assertIsNone(second._frames)

    def test_destination_activation_and_last_valid_buffer(self):
        scene = self.open_scene()
        actor = scene.character
        first, second, last = scene.level.charges[2:5]
        first.position = 140, -50
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
        for reason in ('focus', 'output', 'destination', 'blocked', 'destroyed'):
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
                elif reason == 'blocked':
                    target.position = (scene.level.enemy.x, GROUND_Y + 83 / 2)
                else:
                    target.destroy()
                scene.update(.1)
                self.assertEqual(scene.character.x, first.position[0])
                self.assertFalse(target.spent)
                self.assertIsNone(scene.level.mode.pending_charge)
                scene.exit()
                self.app.output_valid = True

    def test_real_art_shared_phase_draw_and_cleanup(self):
        scene = self.open_scene()
        charges = scene.level.charges
        art = charges[0].art
        self.assertEqual((len(art.frames), len(art.frames[0])), (33, 72))
        self.assertTrue(all(art is charge.art for charge in charges))
        self.assertIs(art.frame(.7, .5), art.frame(.7, .5))
        self.assertIs(art.frame(.7, 0), art.frames[0][16])
        self.assertIs(art.frame(.7, 1), art.frames[-1][16])
        with patch.object(pico, 'SDL_UpdateTexture', side_effect=AssertionError('전하 업로드')):
            for dt in (.08, .06, .1, .2, .6):
                scene.update(dt)
                scene.draw()
        self.assertTrue(any(c.value == 1 for c in charges))
        self.assertTrue(any(c.value == 0 for c in charges))
        images = [row[0].image for row in art.frames]
        scene.exit()
        self.assertTrue(all(c.art is None and c.level is None for c in charges))
        self.assertTrue(all(image.closed for image in images))
        ref = weakref.ref(art)
        del art
        self.assertIsNone(ref())

    def test_baked_stable_frames_preserve_approved_pixels(self):
        from ctypes import string_at

        def rgba(path):
            source = pico.IMG_Load(str(path).encode('utf-8'))
            self.assertTrue(source)
            try:
                converted = pico.SDL_ConvertSurfaceFormat(source, pico.SDL_PIXELFORMAT_RGBA32, 0)
                self.assertTrue(converted)
                try:
                    surface = converted.contents
                    return surface.w, surface.h, b''.join(
                        string_at(surface.pixels + y * surface.pitch, surface.w * 4)
                        for y in range(surface.h))
                finally:
                    pico.SDL_FreeSurface(converted)
            finally:
                pico.SDL_FreeSurface(source)

        meta = json.loads((ASSETS / 'charge.json').read_text(encoding='utf-8'))
        left, top, right, bottom = meta['crop']
        width, height = meta['size']
        for step, name in ((0, 'inactive'), (32, 'active')):
            sw, _, original = rgba(ASSETS.parent / f'{name}.png')
            bw, _, baked = rgba(ASSETS / f'charge-{step:02}.png')
            for index in range(72):
                for row in range(height):
                    src = ((index // 9 * 80 + top + row) * sw + index % 9 * 80 + left) * 4
                    dst = ((index // 9 * height + row) * bw + index % 9 * width) * 4
                    self.assertEqual(baked[dst:dst + width * 4], original[src:src + width * 4])

    def test_initialization_failure_releases_partial_charge_resources(self):
        scene = CharacterScene()
        load = scene.images.load
        loaded = []

        def fail_second(path):
            if Path(path).name == 'charge-01.png':
                raise OSError('전하 PNG 로딩 실패')
            image = load(path)
            loaded.append(image)
            return image

        with patch.object(scene.images, 'load', side_effect=fail_second):
            with self.assertRaisesRegex(OSError, '전하 PNG'):
                scene.enter(self.app)
        self.assertTrue(loaded)
        self.assertTrue(all(image.closed for image in loaded))
        self.assertTrue(scene.images.closed)
        self.assertEqual(scene.level.objects, ())

    def test_link_filter_failure_releases_all_preloaded_images(self):
        scene = CharacterScene()
        load = scene.images.load
        loaded = []

        def record(path):
            image = load(path)
            loaded.append(image)
            return image

        original = pico.SDL_SetTextureScaleMode

        def fail_link(texture, mode):
            if loaded[-1].path.name.startswith('link-'):
                return -1
            return original(texture, mode)

        with (patch.object(scene.images, 'load', side_effect=record),
              patch.object(pico, 'SDL_SetTextureScaleMode', side_effect=fail_link)):
            with self.assertRaises(RuntimeError):
                scene.enter(self.app)
        self.assertTrue(all(image.closed for image in loaded))
        self.assertTrue(scene.images.closed)
        self.assertIsNone(scene.level.link_art)
