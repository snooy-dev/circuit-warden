"""실제 적 PNG와 기존 공격 시트의 전투 연결·수명 검사."""

import ctypes
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d.pico2d as pico

from game.effects import SpriteEffect
from game.scene import CharacterScene, DEFAULT_SIZE
from game.teleport_link import DURATION, TeleportLink


class BasicEnemySceneTests(unittest.TestCase):
    def setUp(self):
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, 800, 600, 32, pico.SDL_PIXELFORMAT_RGBA32)
        self.assertTrue(surface)
        self.addCleanup(pico.SDL_FreeSurface, surface)
        renderer = pico.SDL_CreateSoftwareRenderer(surface)
        self.assertTrue(renderer)
        self.addCleanup(pico.SDL_DestroyRenderer, renderer)
        self.enterContext(patch.object(pico, 'renderer', renderer, create=True))
        self.enterContext(patch.object(pico, 'canvas_height', 600, create=True))
        self.enterContext(patch.object(pico, 'window', None, create=True))
        self.enterContext(patch.object(pico, 'SDL_SetWindowTitle'))
        self.app = Mock(reset_generation=0, output_valid=True, viewport=(0, 0, 800, 600),
                        fullscreen=False, window_size=DEFAULT_SIZE)
        self.app.event_to_output.return_value = None

    def pixels(self):
        pixels = (ctypes.c_ubyte * (800 * 600 * 4))()
        self.assertEqual(pico.SDL_RenderReadPixels(pico.renderer, None,
                                                  pico.SDL_PIXELFORMAT_RGBA32, pixels, 800 * 4), 0)
        return bytes(pixels)

    def test_real_sprite_draws_both_directions_and_releases_texture(self):
        previous = None
        for facing in (-1, 1):
            scene = CharacterScene()
            scene.enter(self.app)
            try:
                enemy = scene.level.enemy
                image = enemy.frame.image
                self.assertIsNot(image, previous)
                self.assertEqual(enemy.frame.rect, (0, 0, 160, 112))
                self.assertEqual(enemy.frame.pivot, (80 / 160, 100 / 112))
                enemy.facing = facing
                scene.update(0)
                pico.SDL_SetRenderDrawColor(pico.renderer, 20, 30, 40, 255)
                pico.SDL_RenderClear(pico.renderer)
                with patch.object(enemy, 'render_items', return_value=()):
                    scene.draw()
                without_enemy = self.pixels()
                scene.draw()
                self.assertNotEqual(self.pixels(), without_enemy)
                self.assertEqual(sum(obj is enemy for obj in scene.level.objects), 1)
            finally:
                scene.exit()
            self.assertTrue(image.closed)
            self.assertEqual(scene.level.objects, ())
            previous = image

    def test_real_attack_sheet_hits_three_times_in_both_directions(self):
        for facing in (-1, 1):
            scene = CharacterScene()
            scene.enter(self.app)
            try:
                actor, enemy = scene.character, scene.level.enemy
                actor.x = enemy.x - facing * 70
                actor.facing = facing
                enemy.state = 'recover'
                enemy.state_remaining = 10.0
                scene.update(0)
                for hp in (2, 1, 0):
                    scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                       button=pico.SDL_BUTTON_LEFT))
                    scene.update(0)
                    scene.update(.15)
                    self.assertEqual(enemy.hp, hp)
                    scene.update(.02)
                    self.assertEqual(enemy.hp, hp)
                    scene.update(.37)
                self.assertIsNone(enemy.level)
                self.assertNotIn(enemy, scene.level.objects)
            finally:
                scene.exit()

    def test_air_attack_misses_at_apex_but_hits_once_on_descent(self):
        for facing in (-1, 1):
            for flight, expected in ((.35, 3), (.57, 2)):
                with self.subTest(facing=facing, flight=flight):
                    scene = CharacterScene()
                    scene.enter(self.app)
                    try:
                        actor, enemy = scene.character, scene.level.enemy
                        actor.facing = facing
                        enemy.x, enemy.state, enemy.state_remaining = facing * 70, 'recover', 10
                        scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_SPACE))
                        jump_start = actor.clips['jump_start_left' if facing < 0 else 'jump_start_right']
                        scene.update(sum(jump_start.durations))
                        scene.update(flight)
                        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                           button=pico.SDL_BUTTON_LEFT))
                        scene.update(0)
                        self.assertIs(actor.player.clip, actor.clips['air_attack'])
                        scene.update(.11)
                        self.assertEqual(enemy.hp, 3)
                        scene.update(.04)
                        self.assertFalse(actor.grounded)
                        self.assertEqual(enemy.hp, expected)
                        scene.update(.04)
                        self.assertEqual(enemy.hp, expected)
                        scene.update(.5)
                        self.assertEqual(enemy.hp, expected)
                    finally:
                        scene.exit()

    def test_restart_during_attack_or_dash_clears_animation_and_keeps_textures(self):
        for action in ('attack', 'dash'):
            with self.subTest(action=action):
                scene = CharacterScene()
                scene.enter(self.app)
                try:
                    scene.update(0)
                    actor, enemy = scene.character, scene.level.enemy
                    image = enemy.frame.image
                    event = (SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT)
                             if action == 'attack' else
                             SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_LSHIFT))
                    scene.handle_event(event)
                    scene.update(0)
                    scene.update(.11)
                    self.assertEqual(actor.state, action)
                    motion_image = actor.player.frame.image
                    actor.take_hit()
                    enemy.take_hit()
                    charges = tuple(scene.level.charges)
                    scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_r, repeat=0))
                    scene.update(0)
                    self.assertTrue(all(obj.level is None for obj in (actor, enemy)))
                    self.assertTrue(all(charge.level is None for charge in charges))
                    self.assertTrue(all(charge.level is scene.level for charge in scene.level.charges))
                    self.assertEqual((scene.character.hp, scene.level.enemy.hp), (5, 3))
                    self.assertEqual(scene.character.invulnerability_remaining, 0)
                    self.assertIs(scene.character.clips, actor.clips)
                    self.assertIs(scene.character.player.frame, actor.clips['idle'].frames[0])
                    self.assertIsNone(scene.character.active_attack)
                    self.assertIs(scene.level.enemy.frame.image, image)
                    self.assertIs(scene.level.enemy.clips, enemy.clips)
                    self.assertIs(scene.level.enemy.frame, enemy.clips['idle'].frames[0])
                    self.assertEqual(scene.level.enemy.animation.elapsed, 0)
                    self.assertFalse(image.closed)
                    self.assertFalse(motion_image.closed)
                    scene.draw()
                finally:
                    scene.exit()
                self.assertTrue(image.closed)
                self.assertTrue(motion_image.closed)

    def test_teleport_cancels_active_sword_without_resetting_health(self):
        scene = CharacterScene()
        scene.enter(self.app)
        try:
            actor, enemy = scene.character, scene.level.enemy
            enemy.x, enemy.state, enemy.state_remaining = 70, 'recover', 10
            actor._queue_action('attack')
            scene.update(0)
            scene.update(.15)
            self.assertIsNotNone(actor.active_attack)
            self.assertEqual(enemy.hp, 2)
            actor.hp, actor.invulnerability_remaining = 4, .4
            attack_id = actor.attack_id
            charge = scene.level.charges[0]
            charge.position = (-140, actor.center[1])
            self.app.event_to_output.return_value = scene.transform.point(*charge.position)
            scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=pico.SDL_BUTTON_LEFT))
            self.assertEqual(actor.center, charge.position)
            self.assertIsNone(actor.active_attack)
            self.assertIs(actor.player.clip, actor.clips['idle'])
            self.assertEqual((actor.hp, actor.invulnerability_remaining, actor.attack_id),
                             (4, .4, attack_id))
            scene.update(.05)
            self.assertEqual(enemy.hp, 2)
        finally:
            scene.exit()

    def test_queued_teleport_runs_after_combat_and_cannot_rescue_dead_player(self):
        for lethal, dt in ((False, .1), (True, .1), (True, .02)):
            with self.subTest(lethal=lethal, dt=dt):
                scene = CharacterScene()
                scene.enter(self.app)
                try:
                    actor, enemy, mode = scene.character, scene.level.enemy, scene.level.mode
                    actor.x, actor.hp = (0, 1) if lethal else (-140, 5)
                    before = actor.center
                    charge = scene.level.charges[0]
                    charge.position = (140, before[1])
                    mode.teleport_link = scene.level.spawn(TeleportLink(
                        (before[0]-20, before[1]), before, scene.level.link_art))
                    mode.teleport_link.update(0)
                    mode.pending_charge = charge
                    enemy.x, enemy.facing = (60, -1) if lethal else (0, 1)
                    enemy.state, enemy.state_remaining = 'charge', .28
                    scene.update(dt)
                    self.assertIsNone(mode.pending_charge)
                    self.assertEqual(actor.hp, 0 if lethal else 5)
                    if lethal:
                        self.assertFalse(charge.spent)
                        self.assertLessEqual(actor.hurt_box[2], enemy.hurt_box[0])
                        stopped = actor.center
                        self.assertIsNone(mode.teleport_link)
                        self.assertFalse(any(isinstance(obj, TeleportLink) for obj in scene.level.objects))
                        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                           button=pico.SDL_BUTTON_RIGHT))
                        self.assertEqual(actor.center, stopped)
                    else:
                        self.assertEqual(actor.center, charge.position)
                        self.assertTrue(charge.spent)
                finally:
                    scene.exit()

    def test_restart_clears_teleport_state_and_reuses_charge_art(self):
        scene = CharacterScene()
        scene.enter(self.app)
        try:
            mode = scene.level.mode
            charges = tuple(scene.level.charges)
            art, link_art = charges[0].art, scene.level.link_art
            mode._teleport(charges[2], scene.character.center)
            link = mode.teleport_link
            self.assertIsNotNone(link)
            self.assertTrue(charges[2].spent)
            mode.pending_charge = charges[1]
            scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_r))
            self.assertIsNone(link.level)
            self.assertFalse(any(isinstance(obj, TeleportLink) for obj in scene.level.objects))
            self.assertEqual((mode.pending_charge, mode.teleport_link), (None, None))
            current = tuple(scene.level.charges)
            self.assertTrue(all(old.level is None and old.position != new.position
                                for old, new in zip(charges, current, strict=True)))
            self.assertTrue(all(not c.spent for c in current))
            self.assertEqual(scene.character.teleport_guard_remaining, 0)
            self.assertIs(current[0].art, art)
            self.assertIs(scene.level.link_art, link_art)
            self.assertTrue(all(c.active == c.in_range(scene.character.center) for c in current))
            current[0].position = (301, scene.character.center[1])
            current[0].active = False
            scene.character.pressed.add(pico.SDLK_d)
            scene.update(.02)
            self.assertTrue(current[0].active)
        finally:
            scene.exit()

    def test_low_charge_enables_an_air_hit_and_immediate_cancel_to_next_charge(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        actor, enemy = scene.character, scene.level.enemy
        entry, escape = scene.level.charges[2:4]
        click = SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT)
        self.app.event_to_output.return_value = scene.transform.point(*entry.position)
        scene.handle_event(click)
        self.assertEqual(actor.center, entry.position)
        self.assertEqual(actor.teleport_guard_remaining, DURATION)

        attack = SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_j)
        scene.handle_event(attack)
        scene.update(0)
        self.assertIs(actor.player.clip, actor.clips['air_attack'])
        scene.handle_event(attack)
        self.assertIsNone(actor.buffered_action)
        scene.update(.15)
        self.assertEqual((actor.state, enemy.hp), ('attack', 2))
        self.assertFalse(actor.grounded)
        hit_spark, = (obj for obj in scene.level.objects if isinstance(obj, SpriteEffect))
        self.assertIs(hit_spark.player.clip, scene.level.combat_clips['hit_spark'])
        self.assertLessEqual(hit_spark.position[1], enemy.hurt_box[3])
        self.assertEqual(hit_spark.player.elapsed, 0)

        self.app.event_to_output.return_value = scene.transform.point(*escape.position)
        scene.handle_event(click)
        self.assertEqual(actor.center, escape.position)
        self.assertIsNone(actor.active_attack)
        self.assertEqual(actor.state, 'jump')
        self.assertTrue(entry.spent and escape.spent)
        scene.update(.1)
        self.assertEqual(enemy.hp, 2)
        scene.update(.15)
        self.assertIsNone(hit_spark.level)
