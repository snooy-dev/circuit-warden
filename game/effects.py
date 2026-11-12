"""공격 위치에 남아 단발 재생 후 사라지는 베기 효과."""

from game_framework import GameObject, RenderItem, SpritePlayer, draw_sprite


class SwordTrail(GameObject):
    def __init__(self, clip, position, facing, scale):
        super().__init__()
        self.player = SpritePlayer(clip)
        self.position = position
        self.facing = facing
        self.scale = scale

    def update(self, dt):
        self.player.update(dt)
        if self.player.finished:
            self.destroy()

    def _draw(self, transform, opacity):
        frame = self.player.frame
        width, height = frame.rect[2:]
        draw_sprite(frame, transform, self.position,
                    (width * self.scale, height * self.scale), opacity, flip_x=self.facing < 0)

    def render_items(self):
        return (RenderItem(self._draw, draw_order=-1),)
