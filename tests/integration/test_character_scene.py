import ctypes
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d.pico2d as pico

from game.scene import CharacterScene, DEFAULT_SIZE
from game.effects import SwordTrail
from game.mode import GameplayMode
from game_framework import GameObject


class CharacterSceneTests(unittest.TestCase):
    def setUp(self):
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, 800, 600, 32, pico.SDL_PIXELFORMAT_RGBA32)
        self.assertTrue(surface)
        self.addCleanup(pico.SDL_FreeSurface, surface)
        self.renderer = pico.SDL_CreateSoftwareRenderer(surface)
        self.assertTrue(self.renderer)
        self.addCleanup(pico.SDL_DestroyRenderer, self.renderer)
        self.enterContext(patch.object(pico, 'renderer', self.renderer, create=True))
        self.enterContext(patch.object(pico, 'canvas_height', 600, create=True))
        self.enterContext(patch.object(pico, 'window', None, create=True))
        self.enterContext(patch.object(pico, 'SDL_SetWindowTitle'))
        self.app = Mock(reset_generation=0, output_valid=True, viewport=(0, 0, 800, 600),
                        fullscreen=False, window_size=DEFAULT_SIZE)

    def pixels(self):
        sample = pico.SDL_Rect(340, 350, 120, 100)
        rgba = (ctypes.c_ubyte * (120 * 100 * 4))()
        self.assertEqual(pico.SDL_RenderReadPixels(self.renderer, sample,
                                                  pico.SDL_PIXELFORMAT_RGBA32, rgba, 120 * 4), 0)
        return bytes(rgba)

    def test_real_asset_draw_and_fresh_scene_lifetime(self):
        previous = None
        for _ in range(2):
            scene = CharacterScene()
            with self.subTest(scene=scene):
                scene.enter(self.app)
                try:
                    actor = scene.character
                    idle, left, right = (actor.clips[name] for name in ('idle', 'run_left', 'run_right'))
                    self.assertEqual(tuple(len(clip.frames) for clip in (idle, left, right)), (48, 16, 16))
                    self.assertEqual(idle.durations[:3], (.041, .042, .042))
                    self.assertEqual(left.durations, (.03,) * 16)
                    self.assertEqual(right.durations, (.03,) * 16)
                    self.assertEqual(idle.frames[-1].rect, (896, 520, 128, 104))
                    self.assertEqual(tuple(clip.frames[0].pivot for clip in (idle, left, right)),
                                     tuple((x / 128, 92 / 104) for x in (58, 63, 64)))
                    image = idle.frames[0].image
                    self.assertIsNot(image, previous)
                    self.assertTrue(all(frame.image is image for frame in idle.frames))
                    self.assertFalse(image.closed)
                    pico.SDL_SetRenderDrawColor(self.renderer, 20, 30, 40, 255)
                    pico.SDL_RenderClear(self.renderer)
                    before = self.pixels()
                    scene.draw()
                    self.assertNotEqual(self.pixels(), before)
                    attack = actor.clips['attack']
                    self.assertFalse(attack.loop)
                    self.assertEqual(attack.durations, (.05,) * 7)
                    self.assertEqual(attack.frames[-1].rect, (1152, 0, 192, 192))
                    refs = tuple(clip.frames[0].image for clip in actor.clips.values())
                finally:
                    scene.exit()
                self.assertTrue(all(ref.closed for ref in refs))
                self.assertEqual(scene.level.objects, ())
                self.assertIsNone(scene.engine)
                previous = image

    def test_invalid_asset_on_enter_releases_already_loaded_texture(self):
        scene = CharacterScene()
        load = scene.images.load
        loaded = []

        def fail_on_second(path):
            if loaded:
                raise OSError(f'cannot load {path}')
            image = load(path)
            loaded.append(image)
            return image

        with patch.object(scene.images, 'load', side_effect=fail_on_second):
            with self.assertRaisesRegex(OSError, r'run_left\.png'):
                scene.enter(self.app)
        self.assertTrue(loaded[0].closed)
        self.assertTrue(scene.images.closed)
        self.assertIsNone(scene.engine)
        self.assertEqual(scene.level.objects, ())

    def test_window_commands_and_resize_bounds(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_F6))
        self.app.set_display.assert_called_with(fullscreen=False, window_size=(1024, 720))
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_F11))
        self.app.set_display.assert_called_with(fullscreen=True)
        self.app.viewport = (0, 0, 180, 600)
        scene.character.x = 200
        scene.update(.1)
        self.assertEqual(scene.character.x, 0)

    def test_gameplay_mode_delivers_once_and_keeps_player_reference(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        actor = scene.character
        scene.level.spawn(GameObject())
        self.assertIs(scene.character, actor)
        self.assertIsInstance(scene.level.mode, GameplayMode)
        with patch.object(actor, 'control', wraps=actor.control) as control:
            scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
            control.assert_called_once()
        scene.update(.1)
        self.assertEqual(actor.x, 18)

    def test_malformed_pivot_reports_clip_and_closes_scene(self):
        scene = CharacterScene()
        metadata = json.loads((scene.images.root / 'animations.json').read_text(encoding='utf-8'))
        metadata['run_left']['pivot'][0] = True
        self.addCleanup(scene.exit)
        with patch('game.character.json.loads', return_value=metadata):
            with self.assertRaisesRegex(ValueError, r'animations\.json.*run_left.*pivot'):
                scene.enter(self.app)
        self.assertTrue(scene.images.closed)
        self.assertIsNone(scene.engine)
        self.assertEqual(scene.level.objects, ())

    def test_invalid_attack_loop_releases_loaded_images(self):
        for loop in ('false', 0, True):
            with self.subTest(loop=loop):
                scene = CharacterScene()
                metadata = json.loads((scene.images.root / 'animations.json').read_text(encoding='utf-8'))
                metadata['attack']['loop'] = loop
                with patch('game.character.json.loads', return_value=metadata):
                    with self.assertRaisesRegex(ValueError, r'animations\.json.*attack.*loop'):
                        scene.enter(self.app)
                self.assertTrue(scene.images.closed)
                self.assertIsNone(scene.engine)
                self.assertEqual(scene.level.objects, ())

    def test_sword_trails_keep_attack_position_and_expire_independently(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        actor = scene.character
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_a))
        scene.update(.1)
        click = SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT)
        scene.handle_event(click)
        scene.update(.1)
        first = next(obj for obj in scene.level.objects if isinstance(obj, SwordTrail))
        self.assertEqual(first.player.elapsed, 0)
        self.assertEqual(first.player.clip.durations, (.05,) * 14)
        position = first.position
        self.assertEqual(first.facing, -1)
        self.assertLess(scene.level.objects[0].render_items()[0].draw_order,
                        first.render_items()[0].draw_order)
        self.assertLess(first.render_items()[0].draw_order, actor.render_items()[0].draw_order)
        with patch('game.effects.draw_sprite') as draw:
            first._draw(scene.transform, 1)
            self.assertEqual(draw.call_args.args[2], position)
            self.assertTrue(draw.call_args.kwargs['flip_x'])
        scene.update(.35)
        self.assertNotEqual(actor.state, 'attack')
        self.assertIs(first.level, scene.level)
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYUP, key=pico.SDLK_a))
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
        scene.update(.01)
        self.assertGreater(actor.x, position[0])
        self.assertEqual((first.position, first.facing), (position, -1))
        scene.handle_event(click)
        scene.update(0)
        trails = [obj for obj in scene.level.objects if isinstance(obj, SwordTrail)]
        self.assertEqual(len(trails), 2)
        second = trails[-1]
        self.assertEqual(second.facing, 1)
        self.assertEqual(second.player.elapsed, 0)
        scene.update(.34)
        self.assertIsNone(first.level)
        self.assertIs(second.level, scene.level)
        image = second.player.frame.image
        scene.exit()
        self.assertIsNone(second.level)
        self.assertTrue(image.closed)
