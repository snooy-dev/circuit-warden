import ctypes
import hashlib
import json
import unittest
from unittest.mock import patch

import pico2d.pico2d as pico

from game.teleport_link import ASSETS, LinkArt, TeleportLink
from game_framework import ImageStore, Level, Renderer, WorldTransform


class TeleportLinkTests(unittest.TestCase):
    def setUp(self):
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, 400, 400, 32, pico.SDL_PIXELFORMAT_RGBA32)
        self.assertTrue(surface)
        self.addCleanup(pico.SDL_FreeSurface, surface)
        self.backend = pico.SDL_CreateSoftwareRenderer(surface)
        self.assertTrue(self.backend)
        self.addCleanup(pico.SDL_DestroyRenderer, self.backend)
        self.enterContext(patch.object(pico, 'renderer', self.backend, create=True))
        self.enterContext(patch.object(pico, 'canvas_height', 400, create=True))
        self.images = ImageStore(ASSETS)
        self.addCleanup(self.images.close)
        self.art = LinkArt(self.images)
        self.level = Level()
        self.level.open()
        self.addCleanup(self.level.close)
        self.transform = WorldTransform((0, 0, 400, 400), view_height=400)

    def test_rotated_endpoints_and_playback_without_upload_or_loading(self):
        for end in ((150, 0), (-150, 0), (0, 150), (0, -150), (106, 106),
                    (-106, 106), (-106, -106), (106, -106), (1, 0), (1.49, 0), (1.5, 0), (5.99, 0), (6, 0), (7.99, 0), (8, 0), (4, 3), (12, 0)):
            with self.subTest(end=end):
                pico.SDL_SetRenderDrawColor(self.backend, 0, 0, 0, 255)
                pico.SDL_RenderClear(self.backend)
                with (patch.object(pico, 'SDL_UpdateTexture', side_effect=AssertionError('업로드')),
                      patch.object(pico, 'IMG_LoadTexture', side_effect=AssertionError('로딩'))):
                    link = self.level.spawn(TeleportLink((0, 0), end, self.art))
                    Renderer().draw(self.level, self.transform)
                self.assertEqual(link.frame_index, 0)
                for point in ((0, 0), end):
                    x, y = map(round, self.transform.point(*point))
                    pixels = (ctypes.c_ubyte * 36)()
                    self.assertEqual(pico.SDL_RenderReadPixels(self.backend, pico.SDL_Rect(x-1, y-1, 3, 3),
                                                              pico.SDL_PIXELFORMAT_RGBA32, pixels, 12), 0)
                    self.assertTrue(any(min(pixels[i:i+3]) >= 240 for i in range(0, 36, 4)))
                link.destroy()
                self.assertIsNone(link._frames)

    def test_fresh_frame_lifetime_and_shared_image_ownership(self):
        start, end = [-30, -10], [30, 20]
        first = self.level.spawn(TeleportLink(start, end, self.art))
        start[0] = end[0] = 0
        self.assertEqual((first.start, first.end), ((-30, -10), (30, 20)))
        image = first._frames[0].image
        self.level.update(.08)
        self.assertEqual(first.frame_index, 0)
        self.level.update(.03)
        self.assertEqual(first.frame_index, 3)
        second = self.level.spawn(TeleportLink(first.end, first.start, self.art))
        self.assertIs(second._frames[0].image, image)
        self.level.update(.07)
        self.assertEqual(self.level.objects, (second,))
        self.assertIsNone(first._frames)
        self.assertFalse(image.closed)
        self.level.close()
        self.assertIsNone(second._frames)
        self.images.close()
        self.assertTrue(image.closed)

    def test_empty_short_and_invalid_coordinates(self):
        for end in ((0, 0), (.5, 0)):
            link = self.level.spawn(TeleportLink((0, 0), end, self.art))
            with patch('game.teleport_link.draw_image') as draw:
                Renderer().draw(self.level, self.transform)
                draw.assert_not_called()
            self.level.update(.1)
            self.assertIsNone(link.level)
        with self.assertRaises(ValueError):
            TeleportLink((float('nan'), 0), (1, 1), self.art)
        with self.assertRaises(ValueError):
            TeleportLink((0, 0), (float('inf'), 1), self.art)

    def test_baked_horizontal_samples_preserve_original_rgba(self):
        meta = json.loads((ASSETS / 'link.json').read_text(encoding='utf-8'))
        samples = {(48, 0): '4c7acb9c879b6354a468e756d946ae0f9a8172f6a15e700905bfe8f227491c78',
                   (320, 11): 'f89b7576fe763e84fb45b57326b6ca91750b9fae816e227e7f3653072edd855d'}
        for (length, frame), expected in samples.items():
            entry = next(item for item in meta['sheets'] if item['length'] == length)
            source = pico.IMG_Load(str(ASSETS / entry['file']).encode('utf-8'))
            self.assertTrue(source)
            converted = None
            try:
                converted = pico.SDL_ConvertSurfaceFormat(source, pico.SDL_PIXELFORMAT_RGBA32, 0)
                self.assertTrue(converted)
                surface = converted.contents
                w, h = entry['size']
                px, py = entry['pad']
                rgba = bytearray((length + 128) * 128 * 4)
                for y in range(h):
                    address = surface.pixels + (frame // 4 * h + y) * surface.pitch + frame % 4 * w * 4
                    start = ((64 - py + y) * (length + 128) + 64 - px) * 4
                    rgba[start:start+w*4] = ctypes.string_at(address, w*4)
                self.assertEqual(hashlib.sha256(rgba).hexdigest(), expected)
            finally:
                if converted:
                    pico.SDL_FreeSurface(converted)
                pico.SDL_FreeSurface(source)
