"""전투 훈련장 지형과 표시."""

from game_framework import Collider, GameObject, RenderItem, draw_rect

from .character import GROUND_Y


WORLD_BOUNDS = (-1920, -360, 1920, 360)
LEFT, BOTTOM, RIGHT, TOP = WORLD_BOUNDS
GROUND = (LEFT, BOTTOM, RIGHT, GROUND_Y)
WALLS = ((LEFT, GROUND_Y, LEFT + 32, TOP), (RIGHT - 32, GROUND_Y, RIGHT, TOP))
LOW_WALL = (940, GROUND_Y, 972, -124)
PLATFORMS = (
    (-1480, -92, -1200, -76),
    (-1120, 6, -880, 22),
    (-760, -92, -500, -76),
    (460, -92, 720, -76),
    (800, 6, 1040, 22),
    (1140, -92, 1430, -76),
)


class TrainingMap(GameObject):
    colliders = (Collider(GROUND, 'terrain', blocks={'player'}),
                 *(Collider(bounds, 'terrain', blocks={'player', 'enemy'})
                   for bounds in (*WALLS, LOW_WALL)),
                 *(Collider(bounds, 'terrain', blocks={'player'}) for bounds in PLATFORMS))

    def render_items(self):
        return (RenderItem(self._draw, draw_order=-2),)

    def _draw(self, transform, opacity):
        draw_rect(transform, GROUND, (55, 62, 77), opacity)
        draw_rect(transform, (LEFT, GROUND_Y - 6, RIGHT, GROUND_Y), (99, 110, 131), opacity)
        for x in range(LEFT + 80, RIGHT, 160):
            draw_rect(transform, (x, GROUND_Y - 35, x + 3, GROUND_Y - 6),
                      (75, 84, 103), opacity)
        for bounds in (*WALLS, LOW_WALL):
            draw_rect(transform, bounds, (75, 84, 103), opacity)
        left, _, right, top = LOW_WALL
        draw_rect(transform, (left, top - 4, right, top), (126, 109, 85), opacity)
        for left, bottom, right, top in PLATFORMS:
            draw_rect(transform, (left, bottom, right, top), (75, 84, 103), opacity)
            draw_rect(transform, (left, top - 4, right, top), (118, 133, 155), opacity)
