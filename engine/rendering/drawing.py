"""출력 픽셀 사각형을 그리는 SDL backend와 공유 상태 복원."""

from ctypes import byref, c_int, c_ubyte

import pico2d.pico2d as pico


def _sdl(result):
    if result < 0:
        raise RuntimeError(f'SDL 그리기 실패: {pico.SDL_GetError()!r}')


def draw_rect(rect, color, opacity):
    rect = pico.SDL_FRect(*rect)
    rgba, blend = [c_ubyte() for _ in range(4)], c_int()
    _sdl(pico.SDL_GetRenderDrawColor(pico.renderer, *[byref(c) for c in rgba]))
    _sdl(pico.SDL_GetRenderDrawBlendMode(pico.renderer, byref(blend)))
    try:
        _sdl(pico.SDL_SetRenderDrawBlendMode(pico.renderer, pico.SDL_BLENDMODE_BLEND))
        _sdl(pico.SDL_SetRenderDrawColor(pico.renderer, *color, int(opacity * 255)))
        _sdl(pico.SDL_RenderFillRectF(pico.renderer, rect))
    finally:
        try:
            _sdl(pico.SDL_SetRenderDrawColor(pico.renderer, *[c.value for c in rgba]))
        finally:
            _sdl(pico.SDL_SetRenderDrawBlendMode(pico.renderer, blend.value))


def draw_image(texture, rect, opacity, *, image=None, source=None, flip_x=False):
    rect = pico.SDL_FRect(*rect)
    access = c_int()
    _sdl(pico.SDL_QueryTexture(texture, None, byref(access), None, None))
    if access.value == pico.SDL_TEXTUREACCESS_TARGET:
        raise RuntimeError('렌더 타깃 이미지는 내용 복구 경로가 필요합니다.')
    alpha, blend = c_ubyte(), c_int()
    _sdl(pico.SDL_GetTextureAlphaMod(texture, byref(alpha)))
    _sdl(pico.SDL_GetTextureBlendMode(texture, byref(blend)))
    try:
        _sdl(pico.SDL_SetTextureBlendMode(texture, pico.SDL_BLENDMODE_BLEND))
        _sdl(pico.SDL_SetTextureAlphaMod(texture, int(opacity * 255)))
        if source is None:
            _sdl(pico.SDL_RenderCopyF(pico.renderer, texture, None, rect))
        else:
            left, top, width, height = source
            bottom = image.h - top - height
            x, y = rect.x + rect.w / 2, pico.canvas_height - rect.y - rect.h / 2
            # shortcut: Pico2D가 SDL 복사 반환값을 버림, native 실패 검출이 필요해지면 직접 SDL 경로로 확장.
            if flip_x:
                image.clip_composite_draw(left, bottom, width, height, 0, 'h', x, y, rect.w, rect.h)
            else:
                image.clip_draw(left, bottom, width, height, x, y, rect.w, rect.h)
    finally:
        try:
            _sdl(pico.SDL_SetTextureAlphaMod(texture, alpha.value))
        finally:
            _sdl(pico.SDL_SetTextureBlendMode(texture, blend.value))
