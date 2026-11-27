"""별도 아래 베기의 입력, 피해 반동 및 지형 차단."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.downstrike import BOUNCE_SPEED
from game.effects import SpriteEffect
from game.enemy import Enemy
from game.scene import CharacterScene
from game_framework import Collider, GameObject
from . import test_character_scene
from .test_power_supply_enemies import PowerSupplyFixture


class DownstrikeTests(unittest.TestCase):
    setUp = test_character_scene.CharacterSceneTests.setUp

    def open_scene(self, height):
        self.scene = CharacterScene()
        self.scene.enter(self.app)
        self.addCleanup(self.scene.exit)
        self.scene.update(0)
        enemy = self.scene.level.enemy
        enemy.state, enemy.state_remaining = 'recover', 2
        actor = self.scene.character
        actor.x, actor.y = enemy.x, height
        actor.velocity_y = -100
        return actor, enemy

    def press_downstrike(self, mouse=False):
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_s))
        if mouse:
            self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                    button=pico.SDL_BUTTON_LEFT, x=0, y=0))
        else:
            self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_j))

    def test_late_listed_enemy_is_hit_first_and_dash_is_restored(self):
        actor, low = self.open_scene(-5)
        high = self.scene.level.spawn(Enemy(low.clips, position=(low.x, low.y + 33)))
        self.scene.level.enemies.append(high)
        high.state, high.state_remaining = 'recover', 2
        actor.air_dash_used = True
        actor.facing = -1
        self.press_downstrike()
        self.scene.update(.02)
        self.assertEqual((actor.state, high.hp, low.hp), ('downstrike', 3, 3))
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
        self.scene.update(.03)
        self.assertEqual((actor.state, actor.jump_phase, actor.velocity_y), ('jump', 'rise', BOUNCE_SPEED))
        self.assertEqual(actor.facing, 1)
        with patch('game.character.draw_sprite') as draw:
            actor._draw(self.scene.transform, 1)
            self.assertIs(draw.call_args.args[0], actor.clips['downstrike'].frames[1])
            self.assertTrue(draw.call_args.kwargs['flip_x'])
        self.assertFalse(actor.air_dash_used)
        self.assertEqual((actor.hp, high.hp, low.hp), (actor.MAX_HP, 2, 3))
        self.assertTrue(any(isinstance(obj, SpriteEffect) for obj in self.scene.level.objects))
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_LSHIFT))
        self.scene.update(.06)
        self.assertEqual(actor.state, 'dash')
        self.assertTrue(actor.air_dash_used)

    def test_platform_blocks_blade_and_landing_does_not_bounce(self):
        actor, enemy = self.open_scene(-18)
        shelf = GameObject()
        shelf.colliders = (Collider((enemy.x - 50, -65, enemy.x + 50, -60),
                                    'terrain', blocks={'player'}),)
        self.scene.level.spawn(shelf)
        self.press_downstrike(mouse=True)
        self.scene.update(.09)
        self.assertEqual(actor.state, 'downstrike')
        self.scene.update(.14)
        self.assertTrue(actor.grounded)
        self.assertEqual((actor.y, actor.velocity_y, enemy.hp), (-60, 0, 3))
        self.assertFalse(any(isinstance(obj, SpriteEffect) for obj in self.scene.level.objects))

    def test_empty_space_falls_and_teleport_clears_the_strike(self):
        actor, enemy = self.open_scene(-18)
        actor.x -= 130
        actor.air_dash_used = True
        self.press_downstrike()
        self.scene.update(.16)
        self.assertEqual((actor.state, enemy.hp), ('downstrike', 3))
        self.assertLess(actor.velocity_y, 0)
        self.assertTrue(actor.air_dash_used)
        self.assertTrue(actor.teleport((actor.x - 40, 0)))
        self.assertEqual(actor.state, 'jump')
        self.assertIsNone(actor.active_attack)

    def test_down_held_on_ground_still_uses_ground_attack(self):
        actor, enemy = self.open_scene(-18)
        actor.x, actor.y, actor.velocity_y = 0, enemy.y, 0
        self.press_downstrike()
        self.scene.update(0)
        self.assertEqual(actor.state, 'attack')
        self.assertFalse(actor.airborne_swing)

    def test_active_charge_keeps_priority_over_downstrike_click(self):
        actor, _ = self.open_scene(-18)
        charge = self.scene.level.charges[0]
        charge.position = actor.x + 52, 30
        x, y = self.scene.transform.point(*charge.position)
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_s))
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                button=pico.SDL_BUTTON_LEFT, x=x, y=y))
        self.assertTrue(charge.spent)
        self.assertEqual(actor.center, charge.position)
        self.assertIsNone(actor.buffered_action)


class PowerSupplyDownstrikeTests(PowerSupplyFixture):
    def test_strike_bounces_from_the_boss_without_defeating_it(self):
        actor, boss = self.scene.character, self.level.boss
        actor.x, actor.y = boss.x, boss.hurt_box[3] + 70
        actor.velocity_y = -65
        for symbol in (pico.SDLK_s, pico.SDLK_j):
            self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=symbol))
        self.scene.update(.09)
        self.assertEqual((boss.hp, actor.hp), (boss.MAX_HP - 1, actor.MAX_HP))
        self.assertEqual(actor.velocity_y, BOUNCE_SPEED)
        self.assertFalse(self.level.layout.boss_defeated)
        self.scene.update(.06)
        with patch('game.character.draw_sprite') as draw:
            actor._draw(self.scene.transform, 1)
            self.assertIn(draw.call_args.args[0], actor.clips['rebound'].frames)
