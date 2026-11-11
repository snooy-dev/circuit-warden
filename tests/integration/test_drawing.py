import ctypes
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico
from game_framework import ImageRef, UITransform, WorldTransform, draw_image, draw_rect


class DrawingStateTests(unittest.TestCase):
    """실제 SDL 소프트웨어 렌더러로 합성 결과와 상태 복원을 검사한다."""

    def setUp(self):
        self.surface = pico.SDL_CreateRGBSurfaceWithFormat(0, 20, 20, 32, pico.SDL_PIXELFORMAT_RGBA32)
        self.assertTrue(self.surface)
        self.addCleanup(pico.SDL_FreeSurface, self.surface)
        self.backend = pico.SDL_CreateSoftwareRenderer(self.surface)
        self.assertTrue(self.backend)
        self.addCleanup(pico.SDL_DestroyRenderer, self.backend)
        self.override = patch.object(pico, 'renderer', self.backend, create=True)
        self.override.start()
        self.addCleanup(self.override.stop)
        self.transform = WorldTransform((0, 0, 20, 20), view_height=20)
        pico.SDL_SetRenderDrawColor(self.backend, 0, 0, 0, 255)
        pico.SDL_RenderClear(self.backend)

    def pixel(self, x=10, y=10):
        pixel = (ctypes.c_ubyte * 4)()
        rect = pico.SDL_Rect(x, y, 1, 1)
        self.assertEqual(pico.SDL_RenderReadPixels(self.backend, rect, pico.SDL_PIXELFORMAT_RGBA32,
                                                pixel, 4), 0)
        return tuple(pixel)

    def state(self):
        rgba = [ctypes.c_ubyte() for _ in range(4)]
        blend = ctypes.c_int()
        pico.SDL_GetRenderDrawColor(self.backend, *[ctypes.byref(c) for c in rgba])
        pico.SDL_GetRenderDrawBlendMode(self.backend, ctypes.byref(blend))
        return tuple(c.value for c in rgba), blend.value

    def texture_state(self, texture):
        alpha, blend = ctypes.c_ubyte(), ctypes.c_int()
        pico.SDL_GetTextureAlphaMod(texture, ctypes.byref(alpha))
        pico.SDL_GetTextureBlendMode(texture, ctypes.byref(blend))
        return alpha.value, blend.value

    def image(self):
        source = pico.SDL_CreateRGBSurfaceWithFormat(0, 2, 2, 32, pico.SDL_PIXELFORMAT_RGBA32)
        try:
            for (x, y), color in zip(((0, 0), (1, 0), (0, 1), (1, 1)),
                                     ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0))):
                rect = pico.SDL_Rect(x, y, 1, 1)
                pico.SDL_FillRect(source, rect, pico.SDL_MapRGBA(source.contents.format, *color, 255))
            texture = pico.SDL_CreateTextureFromSurface(self.backend, source)
        finally:
            pico.SDL_FreeSurface(source)
        image = pico.Image(texture)
        ref = ImageRef(Path('synthetic'), image)
        self.addCleanup(ref.close)
        return image, ref

    def test_clip_source_rows_flip_viewport_and_state_restoration(self):
        image, _ = self.image()
        ui = UITransform((2, 3, 16, 16), (16, 16))
        pico.SDL_SetTextureAlphaMod(image.texture, 190)
        pico.SDL_SetTextureBlendMode(image.texture, pico.SDL_BLENDMODE_ADD)
        initial = self.texture_state(image.texture)
        with patch.object(pico, 'canvas_height', 20, create=True):
            draw_image(image, ui, (2, 3, 10, 7), source=(0, 1, 2, 1))
            self.assertEqual(self.pixel(5, 7)[:3], (0, 0, 255))
            self.assertEqual(self.pixel(10, 7)[:3], (255, 255, 0))
            draw_image(image, ui, (2, 3, 10, 7), source=(0, 0, 2, 1), flip_x=True)
            self.assertEqual(self.pixel(5, 7)[:3], (0, 255, 0))
            self.assertEqual(self.pixel(10, 7)[:3], (255, 0, 0))
            self.assertEqual(self.pixel(3, 7)[:3], (0, 0, 0))
            draw_image(image, ui, (2, 3, 10, 7), flip_x=True)
            self.assertEqual(self.pixel(5, 6)[:3], (0, 255, 0))
            self.assertEqual(self.pixel(5, 9)[:3], (255, 255, 0))
            for method, flip in (('clip_draw', False), ('clip_composite_draw', True)):
                with patch.object(image, method, side_effect=ValueError('clip')):
                    with self.assertRaisesRegex(ValueError, 'clip'):
                        draw_image(image, ui, (2, 3, 10, 7), .5, source=(0, 0, 2, 1), flip_x=flip)
                self.assertEqual(self.texture_state(image.texture), initial)
            with patch.object(image, 'clip_draw') as draw:
                draw_image(image, UITransform((0, 0, 0, 0), (20, 20)),
                           (0, 0, 2, 2), source=(0, 0, 2, 2))
                draw.assert_not_called()
            with self.assertRaises(ValueError):
                draw_image(image, ui, (0, 0, 2, 2), source=(0, 0, 3, 1))
        self.assertEqual(self.texture_state(image.texture), initial)

    def test_detached_texture_survives_traceback_and_null_destructor(self):
        image, ref = self.image()
        caught = None
        try:
            image.clip_draw('invalid', 0, 1, 1, 0, 0)
        except TypeError as error:
            caught = error
        self.assertIsNotNone(caught)
        destroy = pico.SDL_DestroyTexture
        with patch.object(pico, 'SDL_DestroyTexture', wraps=destroy) as calls:
            ref.close()
            ref.close()
            self.assertEqual(sum(bool(call.args[0]) for call in calls.call_args_list), 1)
            self.assertIsNone(image.texture)
            image.__del__()
            self.assertEqual(sum(bool(call.args[0]) for call in calls.call_args_list), 1)

    def test_source_over_order_and_shape_state_restore_even_on_failure(self):
        pico.SDL_SetRenderDrawColor(self.backend, 7, 8, 9, 10)
        pico.SDL_SetRenderDrawBlendMode(self.backend, pico.SDL_BLENDMODE_ADD)
        initial = self.state()
        draw_rect(self.transform, (-10, -10, 10, 10), (255, 0, 0), 1)
        draw_rect(self.transform, (-10, -10, 10, 10), (0, 0, 255), .5)
        red, green, blue, _ = self.pixel()
        self.assertLessEqual(abs(red - 128), 1)
        self.assertEqual(green, 0)
        self.assertLessEqual(abs(blue - 127), 1)
        self.assertEqual(self.state(), initial)
        with patch.object(pico, 'SDL_RenderFillRectF', return_value=-1):
            with self.assertRaises(RuntimeError):
                draw_rect(self.transform, (-10, -10, 10, 10), (0, 255, 0), .2)
        self.assertEqual(self.state(), initial)
        draw_rect(self.transform, (-10, -10, 10, 10), (255, 0, 0), 1)
        self.assertEqual(self.pixel()[:3], (255, 0, 0))
        for setter in ('SDL_SetRenderDrawBlendMode', 'SDL_SetRenderDrawColor'):
            original, calls = getattr(pico, setter), []
            def fail_first(*args):
                calls.append(None)
                return -1 if len(calls) == 1 else original(*args)
            with patch.object(pico, setter, side_effect=fail_first):
                with self.assertRaises(RuntimeError):
                    draw_rect(self.transform, (-1, -1, 1, 1), (0, 255, 0), .2)
            self.assertEqual(self.state(), initial)

    def test_shared_texture_alpha_restore_pixel_alpha_and_failure(self):
        source = pico.SDL_CreateRGBSurfaceWithFormat(0, 1, 1, 32, pico.SDL_PIXELFORMAT_RGBA32)
        self.assertTrue(source)
        try:
            pico.SDL_FillRect(source, None, pico.SDL_MapRGBA(source.contents.format, 255, 0, 0, 128))
            texture = pico.SDL_CreateTextureFromSurface(self.backend, source)
        finally:
            pico.SDL_FreeSurface(source)
        self.assertTrue(texture)
        self.addCleanup(pico.SDL_DestroyTexture, texture)
        image = SimpleNamespace(texture=texture)
        pico.SDL_SetTextureAlphaMod(texture, 190)
        pico.SDL_SetTextureBlendMode(texture, pico.SDL_BLENDMODE_ADD)
        initial = self.texture_state(texture)
        draw_image(image, self.transform, (-10, -10, 10, 10), .5)
        self.assertLessEqual(abs(self.pixel()[0] - 64), 2)
        self.assertEqual(self.texture_state(texture), initial)

        draw_rect(self.transform, (-10, -10, 10, 10), (0, 0, 0), 1)
        draw_image(image, self.transform, (-10, -10, 10, 10), 1)
        self.assertLessEqual(abs(self.pixel()[0] - 128), 1)
        self.assertEqual(self.texture_state(texture), initial)
        with patch.object(pico, 'SDL_RenderCopyF', return_value=-1):
            with self.assertRaises(RuntimeError):
                draw_image(image, self.transform, (-10, -10, 10, 10), .2)
        self.assertEqual(self.texture_state(texture), initial)
        for setter in ('SDL_SetTextureBlendMode', 'SDL_SetTextureAlphaMod'):
            original, calls = getattr(pico, setter), []
            def fail_first(*args):
                calls.append(None)
                return -1 if len(calls) == 1 else original(*args)
            with patch.object(pico, setter, side_effect=fail_first):
                with self.assertRaises(RuntimeError):
                    draw_image(image, self.transform, (-1, -1, 1, 1), .2)
            self.assertEqual(self.texture_state(texture), initial)

    def test_target_texture_has_explicit_unsupported_error(self):
        texture = pico.SDL_CreateTexture(self.backend, pico.SDL_PIXELFORMAT_RGBA8888,
                                         pico.SDL_TEXTUREACCESS_TARGET, 2, 2)
        self.assertTrue(texture)
        self.addCleanup(pico.SDL_DestroyTexture, texture)
        with self.assertRaisesRegex(RuntimeError, '렌더 타깃'):
            draw_image(SimpleNamespace(texture=texture), self.transform, (-1, -1, 1, 1))


if __name__ == '__main__':
    unittest.main()
