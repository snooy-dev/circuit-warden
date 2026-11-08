"""게임 에셋 없이 실행 기반을 확인하는 검사 화면."""

import pico2d.pico2d as pico

from engine import Engine, HEIGHT, Scene, WIDTH


class CheckScene(Scene):
    def __init__(self, alternate=False):
        self.alternate = alternate
        self.x = 20.0
        self.pointer = (WIDTH // 2, HEIGHT // 2)

    def enter(self, engine):
        self.engine = engine

    def handle_event(self, event):
        if event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_SPACE:
            self.engine.change_scene(CheckScene(not self.alternate))
        elif event.type == pico.SDL_MOUSEMOTION:
            self.pointer = (event.x, HEIGHT - 1 - event.y)

    def update(self, dt):
        self.x = (self.x + 160 * dt) % (WIDTH - 40)

    def draw(self):
        color = (220, 110, 35) if self.alternate else (40, 100, 210)
        left = WIDTH - 180 if self.alternate else 60
        pico.draw_rectangle(left, HEIGHT - 180, left + 120, HEIGHT - 60,
                            *color, filled=True)
        pico.draw_rectangle(self.x, 60, self.x + 40, 100, *color, filled=True)
        x, y = self.pointer
        pico.draw_rectangle(x - 8, y - 8, x + 8, y + 8, 20, 20, 20)


if __name__ == '__main__':
    print('엔진 검사: Space = 장면 전환 / 마우스 = 표시 이동 / Escape = 종료', flush=True)
    Engine().run(CheckScene())
