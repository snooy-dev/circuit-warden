"""장면 전용 이미지와 시트 프레임. 원본 이미지는 저장소가 소유한다."""

from bisect import bisect_right
from dataclasses import dataclass, field
from itertools import accumulate
from math import isfinite, ulp
from pathlib import Path

import pico2d.pico2d as pico

from ._validation import _pair
from .drawing import _image_source, draw_image
from .transforms import UITransform, WorldTransform


class ImageRef:
    def __init__(self, path, image):
        self.path = path
        self.width, self.height = image.w, image.h
        self._image = image
        self._renderer = pico.renderer

    @property
    def closed(self):
        return self._image is None

    def _borrow(self):
        if self.closed or self._renderer is not pico.renderer:
            raise RuntimeError(f'닫혔거나 다른 렌더러의 이미지입니다: {self.path}')
        return self._image

    def close(self):
        image, self._image = self._image, None
        if image is not None:
            # traceback이 Image를 보유해도 소멸자가 같은 포인터를 다시 해제하지 않게 한다.
            texture, image.texture = image.texture, None
            if texture:
                pico.SDL_DestroyTexture(texture)


class ImageStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self._images = {}
        self._renderer = None
        self.closed = False

    def load(self, path):
        if self.closed or not getattr(pico, 'renderer', None):
            raise RuntimeError('열린 저장소와 활성 렌더러가 필요합니다.')
        if self._renderer is not None and self._renderer is not pico.renderer:
            raise RuntimeError('이미지 저장소는 다른 렌더러에서 재사용할 수 없습니다.')
        path = (self.root / path).resolve()
        if path not in self._images:
            try:
                if not path.is_file():
                    raise FileNotFoundError(path)
                image = pico.load_image(str(path))
            except OSError as error:
                raise OSError(f'이미지 로딩 실패: {path}') from error
            self._images[path] = ImageRef(path, image)
            self._renderer = pico.renderer
        self._images[path]._borrow()
        return self._images[path]

    def close(self):
        if self.closed:
            return
        self.closed = True
        images, self._images = self._images, {}
        errors = []
        for image in images.values():
            try:
                image.close()
            except BaseException as error:
                errors.append(error)
        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise BaseExceptionGroup('이미지 정리 실패', errors)


@dataclass(frozen=True)
class SpriteFrame:
    image: ImageRef
    rect: tuple
    pivot: tuple = (.5, .5)

    def __post_init__(self):
        if not isinstance(self.image, ImageRef):
            raise TypeError('ImageRef가 필요합니다.')
        rect = _image_source(self.image._borrow(), self.rect)
        pivot = _pair(self.pivot)
        if not all(0 <= value <= 1 for value in pivot):
            raise ValueError('pivot은 좌상단 기준 0~1 좌표입니다.')
        object.__setattr__(self, 'rect', rect)
        object.__setattr__(self, 'pivot', pivot)


@dataclass(frozen=True)
class SpriteClip:
    frames: tuple
    durations: tuple
    loop: bool = True
    _ends: tuple = field(init=False, repr=False)
    _epsilon: float = field(init=False, repr=False)

    def __post_init__(self):
        frames, durations = tuple(self.frames), tuple(self.durations)
        if not frames or len(frames) != len(durations):
            raise ValueError('비어 있지 않은 같은 길이의 프레임·시간 목록이 필요합니다.')
        if any(not isinstance(frame, SpriteFrame) for frame in frames) or type(self.loop) is not bool:
            raise TypeError('SpriteFrame 목록과 bool loop가 필요합니다.')
        if any(not isfinite(duration) or duration <= 0 for duration in durations):
            raise ValueError('프레임 지속 시간은 유한한 양수 초여야 합니다.')
        ends = tuple(accumulate(durations))
        if not isfinite(ends[-1]) or any(b <= a for a, b in zip((0, *ends), ends)):
            raise ValueError('클립 누적 시간은 유한하고 각 프레임을 구분할 수 있어야 합니다.')
        object.__setattr__(self, 'frames', frames)
        object.__setattr__(self, 'durations', durations)
        object.__setattr__(self, '_ends', ends)
        object.__setattr__(self, '_epsilon', min(8 * ulp(ends[-1]), min(durations) / 4))


class SpritePlayer:
    def __init__(self, clip):
        self.clip = None
        self.play(clip)

    def play(self, clip, restart=False):
        if not isinstance(clip, SpriteClip):
            raise TypeError('SpriteClip이 필요합니다.')
        if clip is not self.clip or restart:
            self.clip = clip
            self.elapsed = 0.0
            self.finished = False

    def update(self, dt):
        if not isfinite(dt) or dt < 0:
            raise ValueError('dt는 유한한 비음수 초여야 합니다.')
        if dt == 0 or self.finished:
            return
        total = self.clip._ends[-1]
        if self.clip.loop:
            dt %= total
        remaining = total - self.elapsed
        # 분할 갱신의 반올림 오차 때문에 정확한 종료 경계가 한 프레임 늦어지지 않게 한다.
        if dt >= remaining or remaining - dt <= self.clip._epsilon:
            self.elapsed = max(0.0, dt - remaining) % total if self.clip.loop else total
            self.finished = not self.clip.loop
        else:
            self.elapsed += dt

    @property
    def frame(self):
        ends = self.clip._ends
        index = bisect_right(ends, self.elapsed)
        if index < len(ends) and ends[index] - self.elapsed <= self.clip._epsilon:
            index += 1
        return self.clip.frames[min(index, len(ends) - 1)]


def draw_sprite(frame, transform, position, size, opacity=1, flip_x=False):
    if not isinstance(transform, (WorldTransform, UITransform)):
        raise TypeError('월드 또는 UI 변환이 필요합니다.')
    x, y = _pair(position)
    width, height = _pair(size)
    if min(width, height) <= 0:
        raise ValueError('스프라이트 표시 크기는 양수여야 합니다.')
    px, py = frame.pivot
    if flip_x:
        px = 1 - px
    bottom = y - (py if isinstance(transform, UITransform) else 1 - py) * height
    left = x - px * width
    draw_image(frame.image._borrow(), transform, (left, bottom, left + width, bottom + height),
               opacity, source=frame.rect, flip_x=flip_x)
