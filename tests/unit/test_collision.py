import unittest

from game_framework import Collider, CollisionResponse, GameObject, Level


class Box(GameObject):
    def __init__(self, position, *colliders):
        super().__init__()
        self.position = position
        self.colliders = colliders

    @property
    def collision_position(self):
        return self.position


class CollisionTests(unittest.TestCase):
    def setUp(self):
        self.level = Level()
        self.level.open()
        self.addCleanup(self.level.close)
        self.body = Collider((0, 0, 2, 2), 'actor', blocks={'wall', 'sensor'})
        self.actor = self.level.spawn(Box((0, 0), self.body))

    def test_sweep_stops_at_nearest_thin_wall_and_allows_sliding_or_separation(self):
        wall = Collider((0, 0, .1, 3), 'wall', blocks={'actor'})
        self.level.spawn(Box((12, 0), wall))
        near = self.level.spawn(Box((5, 0), wall))
        def sweep(motion):
            return self.level.blocking_contact(self.actor, self.body, motion)

        self.assertEqual(sweep((100, 0)), .03)
        self.assertEqual(sweep((3, 0)), 1)
        self.actor.position = (3, 0)
        self.assertEqual(sweep((1, 0)), 0)
        self.assertIsNone(sweep((0, 1)))
        self.assertIsNone(sweep((-1, 0)))
        near.destroy()
        self.assertEqual(sweep((100, 0)), .07)

    def test_overlap_uses_live_owner_position_and_both_layer_responses(self):
        sensor = Collider((0, 0, 2, 2), 'sensor', overlaps={'actor'})
        ignored = Collider((0, 0, 2, 2), 'sensor')
        other = self.level.spawn(Box((2, 0), sensor, ignored))
        self.assertEqual(self.body.response_to(sensor), CollisionResponse.OVERLAP)
        self.assertEqual(self.body.response_to(ignored), CollisionResponse.IGNORE)
        self.assertEqual(self.level.collision_overlaps(self.actor, self.body), ())
        other.position = (1, 0)
        self.assertEqual(self.level.collision_overlaps(self.actor, self.body), ((other, sensor),))
        self.assertIsNone(self.level.blocking_contact(self.actor, self.body, (100, 0)))

    def test_swept_overlap_respects_active_window_and_rejects_edge_only_contact(self):
        sensor = Collider((0, 0, 2, 2), 'sensor', overlaps={'actor'})
        self.assertEqual(self.body.overlap_contact(sensor, (0, 0), (5, 0), (0, 1), (10, 0)), .3)
        self.assertIsNone(self.body.overlap_contact(sensor, (0, 0), (5, 0), (0, 1), (10, 0), (0, .3)))
        self.assertIsNone(self.body.overlap_contact(sensor, (0, 0), (5, 2), (0, 1), (10, 0)))
