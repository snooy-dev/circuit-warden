import unittest
from types import SimpleNamespace

import pico2d.pico2d as pico

from game_framework import Button, ButtonInput, Canvas, UIElement


class ButtonInputTests(unittest.TestCase):
    def setUp(self):
        self.canvas = Canvas((200, 100))
        self.transform = self.canvas.transform((20, 40, 400, 200))
        self.input = ButtonInput(self.canvas)
        self.calls = []

    def pointer(self, kind, point):
        event = SimpleNamespace(type=kind, button=pico.SDL_BUTTON_LEFT)
        self.input.handle_event(event, self.transform, self.transform.point(*point))

    def key(self, key):
        self.input.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=key), self.transform)

    def test_click_uses_draw_order_and_matching_press(self):
        root = self.canvas.add(UIElement(anchor=(.5, .5)))
        self.canvas.add(Button('rear', lambda: self.calls.append('rear'),
                               width=50, height=20), root)
        front = self.canvas.add(Button('front', lambda: self.calls.append('front'),
                                      width=50, height=20, draw_order=1), root)
        inside, outside = (110, 55), (20, 30)
        self.pointer(pico.SDL_MOUSEBUTTONUP, inside)
        self.pointer(pico.SDL_MOUSEBUTTONDOWN, inside)
        self.pointer(pico.SDL_MOUSEBUTTONUP, outside)
        self.assertEqual(self.calls, [])
        self.pointer(pico.SDL_MOUSEBUTTONDOWN, inside)
        self.pointer(pico.SDL_MOUSEBUTTONUP, inside)
        self.assertEqual(self.calls, ['front'])
        self.assertTrue(front.focused)

    def test_focus_moves_between_visible_panels_and_cancels_held_click(self):
        menu = self.canvas.add(UIElement())
        settings = self.canvas.add(UIElement(visible=False))
        start = self.canvas.add(Button('Start', lambda: self.calls.append('start'),
                                      width=50, height=20), menu)
        back = self.canvas.add(Button('Back', lambda: self.calls.append('back'),
                                     width=50, height=20), settings)
        self.input.focus(start)
        self.pointer(pico.SDL_MOUSEBUTTONDOWN, (10, 10))
        menu.visible, settings.visible = False, True
        self.pointer(pico.SDL_MOUSEBUTTONUP, (10, 10))
        self.assertEqual(self.calls, [])
        self.key(pico.SDLK_TAB)
        self.key(pico.SDLK_RETURN)
        self.assertEqual(self.calls, ['back'])
        self.assertTrue(back.focused)
        self.assertFalse(start.focused)
