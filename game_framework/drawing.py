"""Pico2D/SDL 그리기와 공유 상태 복원."""

from ctypes import byref, c_int, c_ubyte

import pico2d.pico2d as pico

from ._validation import _bounds, _opacity


def _sdl(result):
    if result < 0:
        raise RuntimeError(f'SDL 그리기 실패: {pico.SDL_GetError()!r}')


def _output_rect(transform, bounds):
    left, bottom, right, top = _bounds(bounds)
    x1, y1 = transform.point(left, top)
    x2, y2 = transform.point(right, bottom)
    return pico.SDL_FRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))


def draw_rect(transform, bounds, color, opacity=1):
    """불투명도와 renderer 상태를 격리한 채 채운 사각형을 그린다."""
    _opacity(opacity)
    if len(color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in color):
        raise ValueError('색상은 0~255 RGB 정수 세 개여야 합니다.')
    if not transform.valid:
        return
    rect = _output_rect(transform, bounds)
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


def draw_image(image, transform, bounds, opacity=1):
    """Pico2D Image의 공유 텍스처를 출력 좌표에 그린다. 자원 소유는 호출자다."""
    _opacity(opacity)
    if not transform.valid:
        return
    rect = _output_rect(transform, bounds)
    access = c_int()
    _sdl(pico.SDL_QueryTexture(image.texture, None, byref(access), None, None))
    if access.value == pico.SDL_TEXTUREACCESS_TARGET:
        raise RuntimeError('렌더 타깃 이미지는 내용 복구 경로가 필요합니다.')
    alpha, blend = c_ubyte(), c_int()
    _sdl(pico.SDL_GetTextureAlphaMod(image.texture, byref(alpha)))
    _sdl(pico.SDL_GetTextureBlendMode(image.texture, byref(blend)))
    try:
        _sdl(pico.SDL_SetTextureBlendMode(image.texture, pico.SDL_BLENDMODE_BLEND))
        _sdl(pico.SDL_SetTextureAlphaMod(image.texture, int(opacity * 255)))
        _sdl(pico.SDL_RenderCopyF(pico.renderer, image.texture, None, rect))
    finally:
        try:
            _sdl(pico.SDL_SetTextureAlphaMod(image.texture, alpha.value))
        finally:
            _sdl(pico.SDL_SetTextureBlendMode(image.texture, blend.value))
