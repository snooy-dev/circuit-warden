import ctypes
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d.pico2d as pico

from game.scene import CharacterScene, DEFAULT_SIZE
from game.mode import GameplayMode
from game.character import GROUND_Y, SPEED, WARDEN_ART
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
                    self.assertEqual(tuple(len(clip.frames) for clip in (idle, left, right)), (16, 8, 8))
                    self.assertAlmostEqual(sum(idle.durations), 1.23)
                    self.assertEqual(left.durations, (.062, .048, .060, .065) * 2)
                    self.assertEqual(right.durations, left.durations)
                    self.assertEqual(idle.frames[-1].rect, (1792, 224, 256, 224))
                    self.assertEqual(tuple(clip.frames[0].pivot for clip in (idle, left, right)),
                                     ((.5, 136 / 224),) * 3)
                    self.assertIs(left.frames[0].image, right.frames[0].image)
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
                    self.assertAlmostEqual(sum(attack.durations), .34)
                    self.assertNotIn('sword_trail', actor.clips)
                    air_attack = actor.clips['air_attack']
                    self.assertFalse(air_attack.loop)
                    self.assertAlmostEqual(sum(air_attack.durations), .30)
                    for clip in (attack, air_attack):
                        self.assertEqual(len(clip.frames), 5)
                        for frame in clip.frames:
                            x, y, width, height = frame.rect
                            self.assertGreaterEqual(min(x, y), 0)
                            self.assertLessEqual(x + width, frame.image.width)
                            self.assertLessEqual(y + height, frame.image.height)
                            self.assertEqual(frame.pivot, (.5, 136 / 224))
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
            with self.assertRaisesRegex(OSError, r'walk\.png'):
                scene.enter(self.app)
        self.assertTrue(loaded[0].closed)
        self.assertTrue(scene.images.closed)
        self.assertIsNone(scene.engine)
        self.assertEqual(scene.level.objects, ())

    def test_ground_movement_draws_walk_run_start_and_run_at_the_same_speed(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        scene.level.enemy.destroy()
        actor = scene.character
        scene.update(0)
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_a))
        with patch('game.character.draw_sprite') as draw:
            for step, name in ((.01, 'walk'), (.23, 'run-start'), (.19, 'run')):
                scene.update(step)
                actor._draw(scene.transform, 1)
                self.assertIn(draw.call_args.args[0], actor.clips[name].frames)
                self.assertTrue(draw.call_args.kwargs['flip_x'])
        self.assertAlmostEqual(actor.x, -SPEED * .43)

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
        left, _, right, top = next(platform for platform in PLATFORMS if platform[0] > 0)
        actor.x = left - 50
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
        for _ in range(150):
            scene.update(.01)
        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYUP, key=pico.SDLK_d))
        self.assertGreater(actor.x, right - actor.body.bounds[0])
        self.assertAlmostEqual(actor.y, GROUND_Y)
        self.assertTrue(actor.grounded)

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
        self.assertEqual(actor.x, SPEED * .1)

    def test_malformed_pivot_reports_manifest_and_closes_scene(self):
        scene = CharacterScene()
        metadata = json.loads((WARDEN_ART / 'animations.json').read_text(encoding='utf-8'))
        metadata['pivot'][0] = True
        self.addCleanup(scene.exit)
        with patch('game.character.json.loads', return_value=metadata):
            with self.assertRaisesRegex(ValueError, r'animations\.json.*pivot'):
                scene.enter(self.app)
        self.assertTrue(scene.images.closed)
        self.assertIsNone(scene.engine)
        self.assertEqual(scene.level.objects, ())

    def test_invalid_attack_loop_releases_loaded_images(self):
        for loop in ('false', 0, True):
            with self.subTest(loop=loop):
                scene = CharacterScene()
                metadata = json.loads((WARDEN_ART / 'animations.json').read_text(encoding='utf-8'))
                metadata['clips']['ground-attack']['loop'] = loop
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
        for direction in ('left', 'right'):
            for phase, count, duration in (('prepare_idle', 2, .1), ('prepare_run', 2, .1),
                                            ('dash', 5, .2), ('recover_idle', 5, .167),
                                            ('recover_run', 5, .167)):
                clip = clips[f'{phase}_{direction}']
                self.assertFalse(clip.loop)
                self.assertEqual(len(clip.frames), count)
                self.assertAlmostEqual(sum(clip.durations), duration)
                self.assertEqual(clip.frames[0].pivot, (.5, 136 / 224))
            dash = clips[f'dash_{direction}']
            self.assertEqual(dash.frames[0].rect, (512, 0, 256, 224))
            self.assertEqual(dash.frames[-1].rect, (1536, 0, 256, 224))

    def test_invalid_dash_frame_layout_releases_images(self):
        for columns in (False, 0, -1, 1):
            scene = CharacterScene()
            metadata = json.loads((WARDEN_ART / 'animations.json').read_text(encoding='utf-8'))
            metadata['clips']['ground-dash']['columns'] = columns
            with patch('game.character.json.loads', return_value=metadata):
                with self.assertRaisesRegex(ValueError, r'animations\.json.*ground-dash'):
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
        self.assertAlmostEqual(actor.player.elapsed, .04)
        self.assertIs(actor.player.frame, actor.clips['attack'].frames[1])

    def test_ground_attack_moves_then_runs_in_latest_direction(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        scene.level.enemy.destroy()
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
                scene.update(.18)
                self.assertAlmostEqual(actor.x, -facing * SPEED * .18)
                position = actor.x, actor.y
                self.assertEqual(scene.level.objects, objects)
                with patch('game.character.draw_sprite') as draw:
                    actor.render_items()[0].drawable(scene.transform, 1)
                draw.assert_called_once_with(attack.frames[2], scene.transform, position,
                                             attack.frames[2].rect[2:], 1, flip_x=facing < 0)
                scene.update(.244)
                self.assertAlmostEqual(actor.x, -facing * SPEED * .424)
                self.assertEqual(actor.state, 'attack')
                scene.update(.002)
                self.assertAlmostEqual(actor.x, -facing * SPEED * .426)
                self.assertEqual((actor.state, actor.facing), ('run', -facing))
                scene.handle_event(SimpleNamespace(type=pico.SDL_KEYUP, key=key))
                scene.update(0)
                self.assertIs(actor.player.clip, actor.clips['idle'])
                self.assertEqual(scene.level.objects, objects)
