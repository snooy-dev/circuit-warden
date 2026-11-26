import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import ATTACK_REACH, BODY_HEIGHT, GROUND_Y, HURT_SECONDS
from game import enemy as enemy_rules
from game.effects import SpriteEffect
from game.scene import GameplayLevel
from game.training_map import LOW_WALL
from game_framework import Collider, GameObject, ImageRef, SpriteClip, SpriteFrame
from game_framework.collision import overlaps


class CombatFixture(unittest.TestCase):
    def setUp(self):
        with patch.object(pico, 'renderer', object(), create=True):
            image = ImageRef(Path('synthetic'), SimpleNamespace(w=128, h=104))
            frame = SpriteFrame(image, (0, 0, 128, 104), (.5, 92 / 104))
        idle = SpriteClip((frame,), (.5,))
        attack = SpriteClip((frame,) * 7, (.05,) * 7, loop=False)
        clips = dict(idle=idle, run_left=idle, run_right=idle, attack=attack,
                     air_attack=attack, hurt=SpriteClip((frame,), (HURT_SECONDS,), loop=False))
        for direction in ('left', 'right'):
            for phase in ('start', 'rise', 'fall', 'land'):
                clips[f'jump_{phase}_{direction}'] = idle
        clips.update(prepare_idle_right=SpriteClip((frame,), (.1,), loop=False),
                     dash_right=SpriteClip((frame,), (.2,), loop=False),
                     dash_fx_right=attack)
        enemy_clips = {
            'idle': SpriteClip((frame,), (.6,)),
            'approach': SpriteClip((frame, frame), (.2, .2)),
            'windup': SpriteClip((frame, frame), (.15, .30), loop=False),
            'charge': SpriteClip((frame,), (.28,), loop=False),
            'recover': SpriteClip((frame, frame), (.30, .30), loop=False),
        }
        spark = SpriteClip((frame,), (.2,), loop=False)
        self.level = GameplayLevel(None)
        with patch('game.scene.load_clips', return_value=clips), patch(
                'game.scene.load_enemy_clips', return_value=enemy_clips), patch(
                'game.scene.ChargeArt'), patch('game.scene.LinkArt'), patch(
                'game.scene.load_combat_clips', return_value={'hit_spark': spark}):
            self.level.open()
        self.addCleanup(self.level.close)
        self.actor = self.level.player
        self.enemy = self.level.enemy
        self.actor.view_bounds = (-500, -300, 500, 300)
        self.enemy.x = 70

    def click(self):
        self.level.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=pico.SDL_BUTTON_LEFT))
        self.level.update(0)

class BasicEnemyTests(CombatFixture):
    def setUp(self):
        super().setUp()
        self.enemy.state, self.enemy.state_remaining = 'recover', 10

    def test_body_contact_rebounds_from_either_side_without_damage_or_crossing(self):
        for side, key in ((-1, pico.SDLK_d), (1, pico.SDLK_a)):
            with self.subTest(side=side):
                self.level.reset_combat()
                actor, enemy = self.level.player, self.level.enemy
                enemy.x, enemy.state, enemy.state_remaining = -side * 70, 'recover', 10
                actor.pressed.add(key)
                self.level.update(1)
                self.assertGreater(side * (actor.x - enemy.x), 66)
                self.assertEqual(actor.hp, 5)

    def test_rebound_persists_with_forward_input_then_gives_control_back(self):
        self.actor.pressed.add(pico.SDLK_d)
        self.level.update(.03)
        self.assertGreater(self.actor.pushback_remaining, 0)
        start_x = self.actor.x
        self.level.update(.06)
        self.assertLess(self.actor.x, start_x)
        self.level.update(.06)
        self.assertEqual(self.actor.pushback_remaining, 0)
        start_x = self.actor.x
        self.level.update(.03)
        self.assertGreater(self.actor.x, start_x)

    def test_falling_onto_enemy_ejects_and_lands_without_another_bounce(self):
        top = self.enemy.hurt_box[3]
        self.actor.x, self.actor.y = self.enemy.x, top + 4
        self.actor.velocity_y = -170
        self.actor._machine.jump()
        self.actor.jump_phase = 'fall'
        self.level.update(.05)
        self.assertNotEqual(self.actor.x, self.enemy.x)
        self.assertGreater(self.actor.y, top)
        self.assertGreater(self.actor.velocity_y, 0)
        self.assertEqual((self.actor.state, self.actor.jump_phase, self.actor.hp), ('jump', 'rise', 5))
        for _ in range(65):
            self.level.update(.01)
        self.assertTrue(self.actor.grounded)
        self.assertFalse(overlaps(self.actor.hurt_box, self.enemy.hurt_box))

    def test_falling_next_to_a_wall_ejects_to_the_open_side(self):
        wall = GameObject()
        wall.colliders = (Collider((0, GROUND_Y, 20, 0), 'terrain', blocks={'player'}),)
        self.level.spawn(wall)
        self.actor.x, self.actor.y = self.enemy.x - 4, self.enemy.hurt_box[3] + 4
        self.actor.velocity_y = -170
        self.actor._machine.jump()
        self.actor.jump_phase = 'fall'
        for _ in range(70):
            self.level.update(.01)
        self.assertTrue(self.actor.grounded)
        self.assertGreater(self.actor.hurt_box[0], self.enemy.hurt_box[2])
        self.assertEqual(self.actor.hp, 5)

    def test_enemy_body_blocks_teleport_but_can_be_passed_above(self):
        self.assertFalse(self.actor.teleport((self.enemy.x, self.actor.center[1])))
        self.actor.y = self.enemy.y + enemy_rules.BODY_HEIGHT + 1
        self.actor.pressed.add(pico.SDLK_d)
        with patch.object(self.actor, '_advance_vertical', side_effect=lambda dt: dt):
            self.level.update(.5)
        self.assertGreater(self.actor.x, self.enemy.x)
        self.assertEqual(self.actor.pushback_remaining, 0)

    def test_active_window_once_per_swing_and_removal(self):
        for hp in (2, 1, 0):
            self.click()
            self.level.update(.124)
            self.assertEqual(self.enemy.hp, hp + 1)
            self.level.update(.001)
            self.assertEqual(self.enemy.hp, hp)
            for _ in range(41):
                self.level.update(.01)
            self.assertEqual(self.enemy.hp, hp)
        self.assertIsNone(self.enemy.level)
        self.assertNotIn(self.enemy, self.level.objects)

    def test_sword_hit_pauses_simulation_and_keeps_accepting_input(self):
        self.click()
        self.level.update(.15)
        self.assertEqual(self.enemy.hp, 2)
        spark, = (obj for obj in self.level.objects if isinstance(obj, SpriteEffect))
        elapsed, recovery = self.actor.player.elapsed, self.enemy.state_remaining
        position = self.enemy.x

        self.level.update(.02)
        self.assertEqual((self.actor.player.elapsed, self.enemy.state_remaining, spark.player.elapsed),
                         (elapsed, recovery, 0))
        with patch('game.enemy.draw_sprite') as draw:
            self.enemy.render_items()[0].drawable(None, 1)
        self.assertEqual(draw.call_args.args[4], 1)
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_j))
        self.assertEqual(self.actor.buffered_action, 'attack')

        self.level.update(.03)
        self.assertAlmostEqual(self.actor.player.elapsed - elapsed, .004)
        self.assertEqual(self.enemy.state_remaining, recovery)
        self.assertAlmostEqual(spark.player.elapsed, .005)
        self.assertAlmostEqual(self.actor.buffer_remaining, .095)
        self.assertGreater(self.enemy.x, position)
        self.level.update(.07)
        self.assertAlmostEqual(self.enemy.x, position + 8)
        self.assertAlmostEqual(self.enemy.state_remaining, recovery - .01)
        self.assertEqual(self.enemy.hp, 2)

    def test_miss_does_not_pause_and_restart_clears_left_hit_feedback(self):
        self.actor.facing = -1
        self.click()
        self.level.update(.15)
        self.assertEqual((self.enemy.hp, self.enemy.x), (3, 70))
        elapsed = self.actor.player.elapsed
        self.level.update(.02)
        self.assertAlmostEqual(self.actor.player.elapsed - elapsed, .016)

        self.enemy.x = -70
        self.level.update(.02)
        self.assertEqual(self.enemy.hp, 2)
        self.level.update(.05)
        self.assertLess(self.enemy.x, -70)
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_r))
        self.level.update(.02)
        self.assertAlmostEqual(self.level.player.player.elapsed, .02)
        self.assertEqual(self.level.enemy.x, enemy_rules.SPAWN_X)

    def test_sword_recoil_stops_at_a_wall_and_suspends_a_charge(self):
        wall = GameObject()
        wall.colliders = (Collider((116, GROUND_Y, 117, 0), 'terrain', blocks={'enemy'}),)
        self.level.spawn(wall)
        self.click()
        self.level.update(.15)
        self.enemy.state, self.enemy.state_remaining, self.enemy.facing = 'charge', .2, -1

        self.level.update(.10)
        self.assertAlmostEqual(self.enemy.hurt_box[2], 116)
        self.assertAlmostEqual(self.enemy.state_remaining, .2)
        self.assertTrue(all(charge_id is None for _, _, _, charge_id in self.enemy.motion))

        self.level.update(.02)
        self.assertLess(self.enemy.hurt_box[2], 116)
        self.assertAlmostEqual(self.enemy.state_remaining, .19)

    def test_moving_ground_attack_stops_at_wall_without_reaching_beyond_it(self):
        wall = GameObject()
        wall.colliders = (Collider((30, GROUND_Y, 31, 0), 'terrain', blocks={'player'}),)
        self.level.spawn(wall)
        self.enemy.x = 6 + ATTACK_REACH + enemy_rules.HURT_HALF_WIDTH + 1
        self.click()
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
        self.level.update(.12)
        self.assertAlmostEqual(self.actor.x, 6)
        self.assertIsNone(self.actor.active_attack)
        self.assertEqual(self.enemy.hp, 3)
        self.level.update(.15)
        self.assertAlmostEqual(self.actor.x, 6)
        self.assertIsNotNone(self.actor.active_attack)
        self.assertEqual(self.actor.hurt_box[2], 30)
        self.assertEqual(self.enemy.hp, 3)

    def test_sword_hits_target_reached_only_during_active_horizontal_motion(self):
        for height in (0, 95):
            for facing, key, gap, expected_hp in (
                (1, pico.SDLK_d, 36, 2), (1, pico.SDLK_d, 70, 3),
                (-1, pico.SDLK_a, 36, 2), (-1, pico.SDLK_a, 70, 3),
            ):
                with self.subTest(height=height, facing=facing, gap=gap):
                    self.level.reset_combat()
                    actor, enemy = self.level.player, self.level.enemy
                    actor.y, enemy.y = GROUND_Y + height, GROUND_Y + min(height, 60)
                    enemy.x = facing * (ATTACK_REACH + enemy_rules.HURT_HALF_WIDTH + gap)
                    enemy.state, enemy.state_remaining = 'recover', 10
                    actor.facing = facing
                    self.click()
                    self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=key))
                    self.level.update(.13)
                    self.assertEqual(enemy.hp, 3)
                    self.level.update(.17)
                    self.assertGreater(facing * actor.x, gap)
                    self.assertEqual(enemy.hp, expected_hp)

    def test_direction_and_strict_contact_edges(self):
        for facing, x, y, expected in ((-1, -70, GROUND_Y, 2),
                                        (-1, 70, GROUND_Y, 3),
                                        (1, ATTACK_REACH + enemy_rules.HURT_HALF_WIDTH, GROUND_Y, 3),
                                        (1, 70, GROUND_Y + 70, 3)):
            with self.subTest(facing=facing, x=x, y=y):
                self.actor.x = 0
                self.actor.facing = facing
                self.enemy.x, self.enemy.y, self.enemy.hp = x, y, 3
                self.click()
                self.level.update(.15)
                self.assertEqual(self.enemy.hp, expected)
                self.level.update(.36)

    def test_split_long_update_keeps_active_attack_snapshot(self):
        self.click()
        self.level.update(.05)
        self.level.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=pico.SDL_BUTTON_LEFT))
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_a))
        self.level.update(.5)
        self.assertEqual(self.actor.facing, -1)
        self.assertEqual(self.enemy.hp, 2)
        self.level.update(.05)
        self.assertEqual(self.enemy.hp, 2)

    def test_inactive_attack_and_trail_cannot_hit(self):
        self.enemy.x = 220
        self.click()
        self.level.update(.286)
        self.enemy.x = 70
        self.level.update(.01)
        self.level.update(.3)
        self.assertEqual(self.enemy.hp, 3)



class EnemyChargeTests(CombatFixture):
    def start_charge(self):
        self.level.update(enemy_rules.IDLE_SECONDS)
        self.level.update(.01)
        self.assertEqual(self.enemy.state, 'windup')
        self.level.update(self.enemy.state_remaining)
        self.assertEqual(self.enemy.state, 'charge')

    def test_approach_then_locks_charge_direction_during_windup(self):
        self.enemy.x = 220
        self.level.update(enemy_rules.IDLE_SECONDS + .1)
        self.assertEqual(self.enemy.state, 'approach')
        self.assertLess(self.enemy.x, 220)
        self.level.update(1.4)
        self.assertEqual((self.enemy.state, self.enemy.facing), ('windup', -1))
        self.assertAlmostEqual(self.enemy.x, enemy_rules.WINDUP_RANGE)
        self.assertEqual(self.actor.hp, 5)
        self.actor.x = 150
        self.level.update(self.enemy.state_remaining + .1)
        self.assertEqual((self.enemy.state, self.enemy.facing), ('charge', -1))
        self.assertLess(self.enemy.x, enemy_rules.WINDUP_RANGE)
        self.assertEqual(self.actor.hp, 5)

    def test_swept_charge_hits_once_and_leaves_recovery(self):
        self.start_charge()
        self.level.update(.14)
        self.assertEqual(self.actor.hp, 4)
        self.assertAlmostEqual(self.actor.invulnerability_remaining, .75 - (.14 - 4 / 350))
        self.actor.invulnerability_remaining = 0
        self.level.update(.16)
        self.assertEqual((self.enemy.state, self.actor.hp), ('recover', 4))

    def test_enemy_charge_stops_at_training_low_wall(self):
        left, _, right, _ = LOW_WALL
        for facing, edge in ((1, left), (-1, right)):
            with self.subTest(facing=facing):
                self.enemy.x = edge - facing * (enemy_rules.HURT_HALF_WIDTH + 20)
                self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS
                self.enemy.facing = facing
                self.level.update(enemy_rules.CHARGE_SECONDS)
                self.assertAlmostEqual(self.enemy.x + facing * enemy_rules.HURT_HALF_WIDTH, edge)
                self.assertEqual(self.enemy.state, 'recover')

    def test_ground_damage_interrupts_attack_and_has_a_distinct_recovery(self):
        self.start_charge()
        self.click()
        self.level.update(.04)
        self.assertEqual((self.actor.state, self.actor.hp), ('hurt', 4))
        self.assertIs(self.actor.player.clip, self.actor.clips['hurt'])
        self.assertLess(self.actor.x, 0)
        self.assertGreater(self.actor.y, GROUND_Y)
        self.assertIsNone(self.actor.active_attack)
        self.actor.update(HURT_SECONDS)
        self.assertEqual((self.actor.state, self.actor.hurt_remaining), ('jump', 0))
        self.actor.update(.24)
        self.assertTrue(self.actor.grounded)

    def test_charge_knocks_the_player_clear_with_movement_held(self):
        for side, key in ((-1, pico.SDLK_d), (1, pico.SDLK_a)):
            with self.subTest(side=side):
                self.level.reset_combat()
                self.actor, self.enemy = self.level.player, self.level.enemy
                self.enemy.x = -side * 70
                self.start_charge()
                self.actor.pressed.add(key)
                self.level.update(.05)
                self.assertEqual((self.actor.state, self.actor.hp), ('hurt', 4))
                self.assertGreater(side * self.actor.x, BODY_HEIGHT / 2)
                self.level.update(.06)
                self.assertEqual(self.actor.state, 'hurt')
                self.assertGreater(side * self.actor.x, BODY_HEIGHT)
                self.assertGreater(self.actor.y - GROUND_Y, BODY_HEIGHT / 5)
                self.assertGreater(side * (self.actor.x - self.enemy.x), 90)

    def test_air_damage_replaces_fall_with_recoil_before_resuming_air_control(self):
        self.start_charge()
        self.actor.y = self.enemy.hurt_box[3] - 9
        self.actor.velocity_y = -130
        self.actor._machine.jump()
        self.actor.jump_phase = 'fall'
        self.level.update(.03)
        self.assertEqual((self.actor.state, self.actor.hp), ('hurt', 4))
        self.assertGreater(self.actor.velocity_y, 0)
        self.assertLess(self.actor.x, 0)
        self.level.update(.05)
        self.assertGreater(-self.actor.x, BODY_HEIGHT)
        self.assertGreater(self.actor.y - (self.enemy.hurt_box[3] - 9), BODY_HEIGHT / 4)
        self.actor.update(HURT_SECONDS)
        self.assertEqual(self.actor.state, 'jump')
        self.assertFalse(self.actor.grounded)
        self.actor._queue_action('attack')
        self.actor.update(0)
        self.assertEqual(self.actor.state, 'attack')
        self.assertGreater(self.actor.invulnerability_remaining, 0)
        attack_x = self.actor.x
        self.actor.update(.02)
        self.assertAlmostEqual(self.actor.x, attack_x)

    def test_air_damage_keeps_moving_sideways_through_apex_and_until_landing(self):
        self.start_charge()
        self.actor.y = self.enemy.hurt_box[3] - 9
        self.actor.velocity_y, self.actor.jump_phase = -130, 'fall'
        self.actor._machine.jump()
        self.level.update(.16)
        self.assertEqual((self.actor.state, self.actor.hp), ('jump', 4))
        rise_x = self.actor.x
        self.assertGreater(self.actor.velocity_y, 0)
        self.level.update(.12)
        self.assertLess(self.actor.velocity_y, 0)
        fall_x, fall_y = self.actor.x, self.actor.y
        self.assertLess(fall_x, rise_x - 15)
        self.level.update(.13)
        self.assertLess(self.actor.y, fall_y)
        low_x = self.actor.x
        self.assertLess(low_x, fall_x - 15)
        self.level.update(.20)
        self.assertTrue(self.actor.grounded)
        landed_x = self.actor.x
        self.assertLess(landed_x, low_x - 15)
        self.level.update(.1)
        self.assertAlmostEqual(self.actor.x, landed_x)

    def test_falling_onto_a_charging_enemy_ejects_once_with_damage(self):
        self.start_charge()
        self.actor.x, self.actor.y = self.enemy.x, self.enemy.hurt_box[3] + 4
        self.actor.velocity_y = -170
        self.actor._machine.jump()
        self.actor.jump_phase = 'fall'
        self.level.update(.05)
        self.assertEqual((self.actor.state, self.actor.hp), ('hurt', 4))
        self.assertGreater(self.actor.x, self.enemy.x)
        for _ in range(65):
            self.level.update(.01)
        self.assertTrue(self.actor.grounded)
        self.assertFalse(overlaps(self.actor.hurt_box, self.enemy.hurt_box))
        self.assertEqual(self.actor.hp, 4)

    def test_dash_movement_does_not_prevent_charge_damage(self):
        self.start_charge()
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_LSHIFT))
        self.level.update(.14)
        self.assertEqual((self.actor.state, self.actor.dash_phase), ('jump', None))
        self.assertEqual(self.actor.hp, 4)
        effects = [obj.player.clip for obj in self.level.objects if isinstance(obj, SpriteEffect)]
        self.assertEqual(effects, [self.level.combat_clips['hit_spark']])

    def test_protected_player_at_wall_clips_the_charging_enemy(self):
        wall = GameObject()
        wall.colliders = (Collider((-25, GROUND_Y, -24, 0), 'terrain', blocks={'player'}),)
        self.level.spawn(wall)
        self.start_charge()
        self.actor.invulnerability_remaining = .75
        for _ in range(3):
            self.level.update(.09)
            self.assertAlmostEqual(self.actor.x, 0)
            self.assertAlmostEqual(self.enemy.hurt_box[0], self.actor.hurt_box[2])
            self.assertEqual(self.actor.hp, 5)

    def test_damage_at_wall_lifts_without_crossing_the_wall(self):
        wall = GameObject()
        wall.colliders = (Collider((-25, GROUND_Y, -24, 0), 'terrain', blocks={'player'}),)
        self.level.spawn(wall)
        self.start_charge()
        for _ in range(6):
            self.level.update(.02)
            self.assertAlmostEqual(self.actor.hurt_box[0], -24)
        self.assertEqual(self.actor.hp, 4)
        self.assertGreater(self.actor.y - GROUND_Y, BODY_HEIGHT / 5)
        self.assertAlmostEqual(self.enemy.hurt_box[0], self.actor.hurt_box[2])

    def test_long_update_reaches_charge_but_height_can_avoid_it(self):
        for airborne, expected_hp in ((True, 5), (False, 4)):
            with self.subTest(airborne=airborne):
                self.level.reset_combat()
                self.actor, self.enemy = self.level.player, self.level.enemy
                self.enemy.x = 70
                if airborne:
                    self.actor.y += 79
                with patch.object(self.actor, 'update'):
                    self.level.update(enemy_rules.IDLE_SECONDS + enemy_rules.WINDUP_SECONDS
                                      + enemy_rules.CHARGE_SECONDS + .05)
                self.assertEqual((self.enemy.state, self.actor.hp), ('recover', expected_hp))
                self.assertIs(self.enemy.animation.clip, self.enemy.clips['recover'])
                self.assertAlmostEqual(self.enemy.animation.elapsed, .05)

    def test_animation_starts_new_clip_at_exact_state_boundary(self):
        self.start_charge()
        self.assertIs(self.enemy.animation.clip, self.enemy.clips['charge'])
        self.assertEqual(self.enemy.animation.elapsed, 0)
        self.level.update(enemy_rules.CHARGE_SECONDS)
        self.assertIs(self.enemy.animation.clip, self.enemy.clips['recover'])
        self.assertEqual(self.enemy.animation.elapsed, 0)
        self.level.update(.05)
        self.assertAlmostEqual(self.enemy.animation.elapsed, .05)

    def test_player_protection_expires_and_dead_player_can_reset(self):
        self.click()
        self.actor.take_hit()
        self.actor.take_hit()
        self.assertEqual(self.actor.hp, 4)
        self.actor.update(.75)
        self.actor.take_hit()
        self.assertEqual(self.actor.hp, 3)
        for _ in range(4):
            self.actor.invulnerability_remaining = 0
            self.actor.take_hit()
        self.assertEqual(self.actor.hp, 0)
        stopped = self.actor.x
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
        self.level.update(3)
        self.assertEqual((self.enemy.state, self.actor.x, self.actor.pressed), ('idle', stopped, set()))

        reset = SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_r)
        self.level.handle_event(reset)
        player, enemy = self.level.player, self.level.enemy
        self.assertEqual((player.hp, player.x, enemy.hp, enemy.x), (5, 0, 3, 220))
        self.assertIsNone(self.actor.level)
        self.assertIsNone(self.enemy.level)
        self.assertEqual(len(self.level.objects), 8)
        self.assertIs(enemy.clips, self.enemy.clips)
        self.assertIs(enemy.animation.clip, enemy.clips['idle'])
        self.assertEqual(enemy.animation.elapsed, 0)
        self.level.handle_event(reset)
        self.assertIs(self.level.player, player)
        self.assertIs(self.level.enemy, enemy)

    def test_sword_hits_enemy_leaving_during_active_window(self):
        self.start_mid_swing()
        self.enemy.x, self.enemy.facing = 110, 1
        self.level.update(.1)
        self.assertEqual(self.enemy.hp, 2)

    def test_buffer_split_preserves_contact_in_first_substep(self):
        self.enemy.x = 220
        self.enemy.state, self.enemy.state_remaining = 'recover', 10
        self.click()
        self.level.update(.04)
        self.level.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=pico.SDL_BUTTON_LEFT))
        self.level.update(.07)
        self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS
        self.enemy.x, self.enemy.facing = 110, 1
        self.level.update(.1)
        self.assertEqual(self.enemy.hp, 2)

    def test_enemy_entering_at_sword_window_end_is_not_hit(self):
        self.start_mid_swing()
        end_of_window = .25 - .15
        self.enemy.x = ATTACK_REACH + enemy_rules.HURT_HALF_WIDTH + enemy_rules.CHARGE_SPEED * end_of_window
        self.enemy.facing = -1
        self.level.update(.15)
        self.assertEqual(self.enemy.hp, 3)

    def test_enemy_entering_after_sword_active_window_is_not_hit(self):
        self.start_mid_swing()
        self.enemy.x, self.enemy.facing = 180, -1
        self.level.update(.15)
        self.assertEqual(self.enemy.hp, 3)

    def start_mid_swing(self):
        self.enemy.x = 220
        self.enemy.state, self.enemy.state_remaining = 'recover', 10
        self.click()
        self.level.update(.15)
        self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS

    def test_charge_contact_ending_before_protection_expires_is_not_hit(self):
        self.actor.invulnerability_remaining = .05
        self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS
        self.enemy.x, self.enemy.facing = -65, -1
        self.level.update(.1)
        self.assertEqual(self.actor.hp, 5)

    def test_teleport_guard_only_prevents_damage_before_contact_deadline(self):
        for gap, expected_hp in ((34, 5), (36, 4)):
            with self.subTest(gap=gap):
                self.level.reset_combat()
                actor, enemy = self.level.player, self.level.enemy
                actor.teleport_guard_remaining = .1
                enemy.x, enemy.facing = 66 + gap, -1
                enemy.state, enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS
                self.level.update(.11)
                self.assertEqual(actor.hp, expected_hp)
                self.assertEqual(actor.teleport_guard_remaining, 0)
                self.assertGreater(actor.pushback_remaining, 0)

    def test_charge_can_hit_warden_before_the_warden_moves_away(self):
        self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS
        self.enemy.x, self.enemy.facing = 0, 1
        self.actor.x = 20
        with patch.object(self.actor, 'update', side_effect=lambda dt: setattr(self.actor, 'x', 103)):
            self.level.update(.1)
        self.assertEqual(self.actor.hp, 4)

    def test_lethal_sword_hit_prevents_same_frame_charge_damage(self):
        self.start_charge()
        self.enemy.hp = 1
        self.click()
        self.level.update(.15)
        self.assertIsNone(self.enemy.level)
        self.assertEqual(self.actor.hp, 5)
