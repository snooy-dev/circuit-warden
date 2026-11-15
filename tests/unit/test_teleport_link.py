import ctypes
import hashlib
import unittest
from unittest.mock import patch

import pico2d.pico2d as pico

from game.teleport_link import TeleportLink, render_link_frame
from game_framework import Level, Renderer, WorldTransform


class TeleportLinkTests(unittest.TestCase):
    def test_v4_reference_rgba_samples(self):
        # 승인 link.js와 Pixelfx의 투명 RGBA 합성 출력.
        samples = {
            (48, 0, 0): '4c7acb9c879b6354a468e756d946ae0f9a8172f6a15e700905bfe8f227491c78',
            (0, -160, 2): '1898945cdfcbe175436338c0bf97178a2ff25ae1652dbf73740c1efa85d82af5',
            (240, -104, 5): '6c762957d73488ac78b2a4aea484fd1acbb73f7d64efdca14a74c4a634834006',
            (-240, 80, 8): '54e49c08defa493e0750972cc391a424690a687f043d892dd55d66fb039128b9',
            (48, 0, 6): '30e9c231900b87caf7b9404c800fd569092ece58a11440108d0e3b3c94b465d3',
            (320, 0, 11): 'f89b7576fe763e84fb45b57326b6ca91750b9fae816e227e7f3653072edd855d',
        }
        for (dx, dy, frame), digest in samples.items():
            with self.subTest(dx=dx, dy=dy, frame=frame):
                rgba = render_link_frame(dx, dy, 7, frame)
                self.assertEqual(hashlib.sha256(rgba).hexdigest(), digest)
        self.assertFalse(any(render_link_frame(48, 0, 7, 12)))
        self.assertFalse(any(render_link_frame(0, 0, 7, 0)))

    def test_world_endpoints_stream_to_sdl_and_expire_independently(self):
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, 100, 100, 32, pico.SDL_PIXELFORMAT_RGBA32)
        self.assertTrue(surface)
        self.addCleanup(pico.SDL_FreeSurface, surface)
        backend = pico.SDL_CreateSoftwareRenderer(surface)
        self.assertTrue(backend)
        self.addCleanup(pico.SDL_DestroyRenderer, backend)
        self.enterContext(patch.object(pico, 'renderer', backend, create=True))

        level = Level()
        level.open()
        self.addCleanup(level.close)
        start, end = [-30, -10], [30, 20]
        first = level.spawn(TeleportLink(start, end))
        start[0] = end[0] = 0
        self.assertEqual((first.start, first.end), ((-30, -10), (30, 20)))
        self.assertEqual(first.render_items()[0].draw_order, -1)
        pico.SDL_SetRenderDrawColor(backend, 0, 0, 0, 255)
        pico.SDL_RenderClear(backend)
        Renderer().draw(level, WorldTransform((0, 0, 100, 100), view_height=100))
        for x, y in ((20, 60), (80, 30)):
            with self.subTest(x=x, y=y):
                pixel = (ctypes.c_ubyte * 4)()
                self.assertEqual(pico.SDL_RenderReadPixels(backend, pico.SDL_Rect(x, y, 1, 1),
                                                        pico.SDL_PIXELFORMAT_RGBA32, pixel, 4), 0)
                self.assertEqual(tuple(pixel), (255, 255, 255, 255))

        level.update(0)
        level.update(0.03)
        second = level.spawn(TeleportLink(first.end, first.start))
        level.update(0)
        level.update(0.07)
        self.assertEqual(level.objects, (second,))
        self.assertIsNone(first.texture)
        self.assertTrue(second.texture)
        level.close()
        self.assertIsNone(second.texture)

    def test_spawn_failure_releases_allocated_texture(self):
        level = Level()
        level.open()
        self.addCleanup(level.close)
        link = TeleportLink((0, 0), (30, 30))
        with (
            patch.object(pico, 'renderer', object(), create=True),
            patch.object(pico, 'SDL_CreateTexture', return_value=1),
            patch.object(pico, 'SDL_SetTextureScaleMode', return_value=-1),
            patch.object(pico, 'SDL_DestroyTexture') as destroy,
        ):
            with self.assertRaisesRegex(RuntimeError, '필터 설정 실패'):
                level.spawn(link)
            destroy.assert_called_once_with(1)
        self.assertIsNone(link.texture)
        self.assertEqual(level.objects, ())
