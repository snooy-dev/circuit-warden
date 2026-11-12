"""플레이 레벨의 플레이어 입력 전달."""

from game_framework import GameMode


class GameplayMode(GameMode):
    def on_event(self, event):
        player = self.level.player
        if player.level is self.level:
            player.control(event)
