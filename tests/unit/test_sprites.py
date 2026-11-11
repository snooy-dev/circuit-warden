import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico
from game_framework import (ImageRef, ImageStore, SpriteClip, SpriteFrame, SpritePlayer,
                            UITransform, WorldTransform, draw_sprite)


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve()
        self.root = self.path.parent
        self.renderer = object()
        self.override = patch.object(pico, 'renderer', self.renderer, create=True)
        self.override.start()
        self.addCleanup(self.override.stop)
        self.raw = SimpleNamespace(texture=object(), w=128, h=64)
        self.loader = patch.object(pico, 'load_image', return_value=self.raw).start()
        self.destroy = patch.object(pico, 'SDL_DestroyTexture').start()
        self.addCleanup(patch.stopall)
        self.store = ImageStore(self.root)
        self.addCleanup(self.store.close)

    def test_alias_cache_close_and_external_frame(self):
        image = self.store.load(self.path.name)
        alias = self.root / '..' / self.root.name / self.path.name
        self.assertIs(image, self.store.load(alias))
        self.loader.assert_called_once_with(str(self.path))
        frame = SpriteFrame(image, (8, 4, 32, 16))
        texture = self.raw.texture
        self.store.close()
        self.store.close()
        self.assertIsNone(self.raw.texture)
        self.destroy.assert_called_once_with(texture)
        with self.assertRaises(RuntimeError):
            draw_sprite(frame, UITransform((0, 0, 100, 100), (100, 100)), (0, 0), (32, 16))
        with self.assertRaises(RuntimeError):
            self.store.load(self.path.name)

    def test_load_failure_not_cached_and_missing_path_is_reported(self):
        self.loader.side_effect = OSError('decode')
        with self.assertRaisesRegex(OSError, r'test_sprites\.py'):
            self.store.load(self.path.name)
        self.loader.side_effect = None
        self.store.load(self.path.name)
        self.assertEqual(self.loader.call_count, 2)
        with self.assertRaisesRegex(OSError, r'missing\.png'):
            self.store.load('missing.png')
        self.assertEqual(self.loader.call_count, 2)

    def test_no_renderer_and_different_session_rejected(self):
        with patch.object(pico, 'renderer', None):
            with self.assertRaises(RuntimeError):
                self.store.load(self.path.name)
        image = self.store.load(self.path.name)
        with patch.object(pico, 'renderer', object()):
            with self.assertRaises(RuntimeError):
                self.store.load(self.path.name)
            with self.assertRaises(RuntimeError):
                image._borrow()

    def test_closed_cached_image_is_not_returned_as_usable(self):
        image = self.store.load(self.path.name)
        image.close()
        with self.assertRaises(RuntimeError):
            self.store.load(self.path.name)
        self.loader.assert_called_once()

    def test_close_continues_after_failure_and_never_retries_texture(self):
        first = self.store.load(self.path.name)
        second_raw = SimpleNamespace(texture=object(), w=64, h=64)
        self.loader.return_value = second_raw
        second = self.store.load('__init__.py')
        self.destroy.side_effect = [ValueError('destroy'), None]
        with self.assertRaisesRegex(ValueError, 'destroy'):
            self.store.close()
        self.assertTrue(first.closed)
        self.assertTrue(second.closed)
        self.assertEqual(self.destroy.call_count, 2)
        self.store.close()
        self.assertEqual(self.destroy.call_count, 2)

    def test_frame_validation_and_pivot_bounds(self):
        image = self.store.load(self.path.name)
        for rect in ((-1, 0, 2, 2), (0, 0, 0, 2), (120, 0, 9, 2),
                     (0, 63, 2, 2), (0.5, 0, 2, 2), (True, 0, 2, 2)):
            with self.subTest(rect=rect), self.assertRaises(ValueError):
                SpriteFrame(image, rect)
        for pivot in ((-0.1, 0), (0, 1.1), (float('nan'), 0)):
            with self.assertRaises(ValueError):
                SpriteFrame(image, (0, 0, 2, 2), pivot)
        frame = SpriteFrame(image, (8, 4, 32, 16), (.25, .75))
        with patch('game_framework.sprites.draw_image') as draw:
            world = WorldTransform((20, 30, 100, 100), view_height=10)
            draw_sprite(frame, world, (10, 20), (8, 4))
            self.assertEqual(draw.call_args.args[2], (8, 19, 16, 23))
            ui = UITransform((20, 30, 100, 100), (100, 100))
            draw_sprite(frame, ui, (10, 20), (8, 4), flip_x=True)
            self.assertEqual(draw.call_args.args[2], (4, 17, 12, 21))
            self.assertEqual(draw.call_args.kwargs['source'], (8, 4, 32, 16))
            self.assertTrue(draw.call_args.kwargs['flip_x'])
        for size in ((0, 1), (1, -1), (1, float('inf'))):
            with self.assertRaises(ValueError):
                draw_sprite(frame, world, (0, 0), size)


class PlaybackTests(unittest.TestCase):
    def setUp(self):
        self.Clip, self.Player = SpriteClip, SpritePlayer
        with patch.object(pico, 'renderer', object(), create=True):
            image = ImageRef(Path('synthetic'), SimpleNamespace(w=3, h=1, texture=object()))
            self.frames = tuple(SpriteFrame(image, (i, 0, 1, 1)) for i in range(3))

    def test_variable_durations_boundaries_and_partition_invariance(self):
        clip = self.Clip(self.frames, (.041, .042, .042))
        a, b = self.Player(clip), self.Player(clip)
        a.update(.04)
        self.assertIs(a.frame, self.frames[0])
        a.update(.001)
        self.assertIs(a.frame, self.frames[1])
        a.update(.042)
        b.update(.083)
        self.assertIs(a.frame, self.frames[2])
        self.assertIs(a.frame, b.frame)
        a.update(.042)
        self.assertIs(a.frame, self.frames[0])
        self.assertFalse(a.finished)
        for _ in range(1000):
            a.update(.001)
        self.assertIs(a.frame, self.frames[0])

    def test_single_frame_one_shot_holds_and_independent_players(self):
        clip = self.Clip(self.frames, (.1, .2, .3), loop=False)
        a, b = self.Player(clip), self.Player(clip)
        a.update(1000)
        self.assertTrue(a.finished)
        self.assertIs(a.frame, self.frames[-1])
        a.update(1)
        self.assertIs(a.frame, self.frames[-1])
        self.assertFalse(b.finished)
        self.assertIs(b.frame, self.frames[0])
        single = self.Player(self.Clip(self.frames[:1], (.03,), loop=False))
        single.update(.029)
        self.assertFalse(single.finished)
        single.update(.001)
        self.assertTrue(single.finished)

    def test_same_clip_restart_and_different_clip(self):
        clip = self.Clip(self.frames, (.1, .2, .3))
        player = self.Player(clip)
        player.update(.2)
        player.play(clip)
        self.assertIs(player.frame, self.frames[1])
        player.play(clip, restart=True)
        self.assertIs(player.frame, self.frames[0])
        player.update(.3)
        player.play(self.Clip(self.frames, (.1, .2, .3)))
        self.assertIs(player.frame, self.frames[0])

    def test_large_dt_preserves_phase_and_short_frame_is_not_skipped(self):
        player = self.Player(self.Clip(self.frames, (.125, .125, .25)))
        player.update(.125)
        player.update(1e16)
        self.assertIs(player.frame, self.frames[1])
        player = self.Player(self.Clip(self.frames, (1., 1e-13, 1.)))
        player.update(1.)
        self.assertIs(player.frame, self.frames[1])

    def test_invalid_clip_and_dt_and_large_loop_delta(self):
        for durations in ((), (.1,), (.1, 0, .1), (.1, -.1, .1),
                          (.1, float('nan'), .1), (.1, float('inf'), .1),
                          (1e308, 1e308, 1e308)):
            with self.subTest(durations=durations), self.assertRaises(ValueError):
                self.Clip(self.frames, durations)
        with self.assertRaises(ValueError):
            self.Clip((), ())
        with self.assertRaises(TypeError):
            self.Clip((None,), (.1,))
        player = self.Player(self.Clip(self.frames, (.125, .125, .25)))
        for dt in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                player.update(dt)
        player.update(1000000.25)
        self.assertIs(player.frame, self.frames[2])
        player.update(0)
        self.assertIs(player.frame, self.frames[2])
        self.assertFalse(player.finished)


if __name__ == '__main__':
    unittest.main()
