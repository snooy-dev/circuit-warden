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
        elif event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_F11:
            self.engine.set_display(fullscreen=not self.engine.fullscreen)
        elif event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_F6:
            size = (1024, 720) if self.engine.window_size == (800, 600) else (800, 600)
            self.engine.set_display(fullscreen=False, window_size=size)
        elif event.type == pico.SDL_MOUSEMOTION:
            point = self.engine.event_to_output(event)
            if point is not None:
                self.pointer = (point[0], self.engine.output_size[1] - 1 - point[1])

    def update(self, dt):
        self.x = (self.x + 160 * dt) % max(1, self.engine.output_size[0] - 40)

    def draw(self):
        color = (220, 110, 35) if self.alternate else (40, 100, 210)
        width, height = self.engine.output_size
        left = width - 180 if self.alternate else 60
        pico.draw_rectangle(left, height - 180, left + 120, height - 60,
                            *color, filled=True)
        pico.draw_rectangle(self.x, 60, self.x + 40, 100, *color, filled=True)
        x, y = self.pointer
        pico.draw_rectangle(x - 8, y - 8, x + 8, y + 8, 20, 20, 20)


def main():
    print('엔진 검사: Space = 장면 전환 / F6 = 창 크기 / F11 = 전체화면 / 마우스 = 표시 이동 / Escape = 종료', flush=True)
    Engine().run(CheckScene())


if __name__ == '__main__':
    main()
