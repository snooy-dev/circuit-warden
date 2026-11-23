import ctypes
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d.pico2d as pico

from game.scene import CharacterScene, DEFAULT_SIZE
from game.mode import GameplayMode
from game.character import GROUND_Y, SPEED
from game.training_map import LOW_WALL, PLATFORMS, WALLS, WORLD_BOUNDS
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
        self.app.event_to_output.side_effect = lambda event: (event.x, event.y)

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
                                     tuple((x / 128, 92 / 104) for x in (64, 63, 64)))
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
                    self.assertEqual(attack.durations, (.02,) * 17)
                    self.assertNotIn('sword_trail', actor.clips)
                    air_attack = actor.clips['air_attack']
                    self.assertFalse(air_attack.loop)
                    self.assertEqual(air_attack.durations, (.017, .016, .017) * 6)
                    for clip in (attack, air_attack):
                        for frame in clip.frames:
                            x, y, width, height = frame.rect
                            self.assertGreaterEqual(min(x, y), 0)
                            self.assertLessEqual(x + width, frame.image.width)
                            self.assertLessEqual(y + height, frame.image.height)
                            self.assertEqual(frame.pivot[0], .5)
                            self.assertGreater(frame.pivot[1], .5)
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
        scene.level.enemy.destroy()
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_F6))
        self.app.set_display.assert_called_with(fullscreen=False, window_size=(1024, 720))
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_F11))
        self.app.set_display.assert_called_with(fullscreen=True)
        self.app.viewport = (0, 0, 180, 600)
        scene.character.x = 200
        scene.update(.1)
        self.assertEqual(scene.character.x, 200)
        self.assertGreater(scene.camera_center[0], 0)
        self.assertLess(scene.camera_center[0], scene.character.x)
        self.app.viewport = (0, 0, 120, 600)
        scene.update(.1)
        self.assertEqual(scene.character.x, 200)

    def test_camera_lags_motion_freezes_at_walls_and_resets_with_player(self):
        for side, symbol, wall in ((-1, pico.SDLK_a, WALLS[0]), (1, pico.SDLK_d, WALLS[1])):
            with self.subTest(side=side):
                scene = CharacterScene()
                scene.enter(self.app)
                try:
                    actor = scene.character
                    scene.level.enemy.destroy()
                    scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=symbol))
                    scene.update(.1)
                    self.assertGreater(scene.camera_center[0] * side, 0)
                    self.assertLess(scene.camera_center[0] * side, actor.x * side)
                    self.assertEqual(scene.event_to_world(SimpleNamespace(x=400, y=300)),
                                     scene.camera_center)

                    wall_edge = wall[0] if side > 0 else wall[2]
                    actor.x = wall_edge - side * 40
                    scene.update(.15)
                    body_edge = actor.hurt_box[2] if side > 0 else actor.hurt_box[0]
                    self.assertAlmostEqual(body_edge, wall_edge)
                    stopped_center = scene.camera_center
                    for _ in range(8):
                        scene.update(.05)
                    self.assertEqual(scene.camera_center, stopped_center)
                    self.assertGreaterEqual(scene.transform.bounds[0], WORLD_BOUNDS[0])
                    self.assertLessEqual(scene.transform.bounds[2], WORLD_BOUNDS[2])

                    scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_r))
                    self.assertIsNot(scene.character, actor)
                    self.assertEqual((scene.character.x, scene.character.y), (0, GROUND_Y))
                    self.assertEqual(scene.camera_center, (0, 0))
                finally:
                    scene.exit()

    def test_jump_onto_training_platform_and_walk_off(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        scene.level.enemy.destroy()
        actor = scene.character
        left, _, _, top = next(platform for platform in PLATFORMS if platform[0] > 0)
        actor.x = left - 50
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_SPACE))
        for _ in range(33):
            scene.update(.01)
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
        for _ in range(46):
            scene.update(.01)
        self.assertGreater(actor.x, left)
        self.assertAlmostEqual(actor.y, top)
        self.assertTrue(actor.grounded)
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYUP, key=pico.SDLK_d))
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_a))
        for _ in range(85):
            scene.update(.01)
        self.assertLess(actor.x, left)
        self.assertAlmostEqual(actor.y, GROUND_Y)
        self.assertTrue(actor.grounded)

    def test_camera_freezes_at_low_wall_inside_world_bounds(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        scene.level.enemy.destroy()
        actor = scene.character
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
        for _ in range(52):
            scene.update(.1)
        self.assertAlmostEqual(actor.hurt_box[2], LOW_WALL[0])
        stopped_center = scene.camera_center
        self.assertLess(stopped_center[0], actor.x)
        self.assertLess(scene.transform.bounds[2], WORLD_BOUNDS[2])
        scene.update(.5)
        self.assertEqual(scene.camera_center, stopped_center)

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

    def test_dash_assets_preserve_frame_order_timing_and_pivots(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        clips = scene.character.clips
        for direction, pivot in (('left', 63), ('right', 64)):
            for phase, count, duration in (('prepare_idle', 6, .1), ('prepare_run', 6, .1),
                                            ('dash', 11, .2), ('recover_idle', 10, .167),
                                            ('recover_run', 10, .167)):
                clip = clips[f'{phase}_{direction}']
                self.assertFalse(clip.loop)
                self.assertEqual(len(clip.frames), count)
                self.assertAlmostEqual(sum(clip.durations), duration)
                self.assertEqual(clip.frames[0].pivot, (pivot / 128, 92 / 104))
            dash = clips[f'dash_{direction}']
            self.assertEqual(dash.frames[6].rect, (384, 104, 128, 104))
            self.assertEqual(dash.durations[5], .034)
            effect = clips[f'dash_fx_{direction}']
            self.assertEqual(len(effect.frames), 22)
            self.assertAlmostEqual(sum(effect.durations), .367)
            self.assertEqual(effect.frames[0].pivot,
                             ((287 if direction == 'left' else 96) / 384, 112 / 128))

    def test_invalid_dash_frame_indices_release_images(self):
        for indices in ([0], [True] * 11, [-1] * 11, [1000] * 11):
            scene = CharacterScene()
            metadata = json.loads((scene.images.root / 'animations.json').read_text(encoding='utf-8'))
            metadata['dash_right']['frameIndices'] = indices
            with patch('game.character.json.loads', return_value=metadata):
                with self.assertRaisesRegex(ValueError, r'animations\.json.*dash_right'):
                    scene.enter(self.app)
            self.assertTrue(scene.images.closed)
            self.assertEqual(scene.level.objects, ())

    def test_buffered_ground_attack_preserves_first_composite_frame_after_slow_frame(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        scene.level.enemy.destroy()
        actor = scene.character
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_LSHIFT))
        for dt in (.1, .1, .1, .0672):
            scene.update(dt)  # 대시 종료까지 99.8ms 남긴다.
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                            button=pico.SDL_BUTTON_LEFT, x=0, y=0))
        for _ in range(6):
            scene.update(.0166)
        scene.update(.08)

        self.assertEqual(actor.state, 'attack')
        self.assertIs(actor.player.clip, actor.clips['attack'])
        self.assertEqual(actor.player.elapsed, 0)
        self.assertIs(actor.player.frame, actor.clips['attack'].frames[0])
        scene.update(.05)
        self.assertEqual(actor.player.elapsed, .05)
        self.assertIs(actor.player.frame, actor.clips['attack'].frames[2])

    def test_ground_attack_draws_moving_composite_with_fixed_orientation_and_clears_on_exit(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        actor = scene.character
        objects = scene.level.objects
        click = SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT, x=0, y=0)
        attack = actor.clips['attack']
        for facing, key in ((-1, pico.SDLK_d), (1, pico.SDLK_a)):
            with self.subTest(facing=facing):
                actor.x, actor.facing = 0, facing
                scene.handle_event(click)
                scene.update(.1)
                scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=key))
                scene.update(.12)
                self.assertAlmostEqual(actor.x, -facing * SPEED * .12)
                position = actor.x, actor.y
                self.assertEqual(scene.level.objects, objects)
                with patch('game.character.draw_sprite') as draw:
                    actor.render_items()[0].drawable(scene.transform, 1)
                draw.assert_called_once_with(attack.frames[6], scene.transform, position,
                                             attack.frames[6].rect[2:], 1, flip_x=facing < 0)
                scene.handle_event(SimpleNamespace(type=pico.SDL_KEYUP, key=key))
                scene.update(.22)
                self.assertIs(actor.player.clip, actor.clips['idle'])
                self.assertEqual(scene.level.objects, objects)
