"""원본 SDL 이벤트를 보존하는 Pico2D 입력 수집."""

from ctypes import byref

import pico2d.pico2d as pico


def poll_events():
    """Pico2D 형식의 입력과 원본 창/렌더 이벤트를 함께 보존한다."""
    raw = pico.SDL_Event()
    events = []
    while pico.SDL_PollEvent(byref(raw)):
        event = pico.Event(raw.type)
        if raw.type in (pico.SDL_KEYDOWN, pico.SDL_KEYUP):
            if raw.key.repeat:
                continue
            event.key = raw.key.keysym.sym
        elif raw.type == pico.SDL_MOUSEMOTION:
            event.x, event.y = raw.motion.x, raw.motion.y
        elif raw.type in (pico.SDL_MOUSEBUTTONDOWN, pico.SDL_MOUSEBUTTONUP):
            event.button = raw.button.button
            event.x, event.y = raw.button.x, raw.button.y
        elif raw.type == pico.SDL_MOUSEWHEEL:
            event.x, event.y = raw.wheel.x, raw.wheel.y
            event.direction = raw.wheel.direction
        elif raw.type == pico.SDL_WINDOWEVENT:
            event.event = raw.window.event
            event.data1, event.data2 = raw.window.data1, raw.window.data2
        elif raw.type not in (pico.SDL_QUIT, pico.SDL_RENDER_TARGETS_RESET,
                              pico.SDL_RENDER_DEVICE_RESET):
            continue
        events.append(event)
    return events
