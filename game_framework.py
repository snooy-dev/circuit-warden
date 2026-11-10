"""레벨·Canvas 소유와 월드·독립 UI 렌더링."""

from ctypes import byref, c_int, c_ubyte
from dataclasses import dataclass
from math import isfinite

import pico2d.pico2d as pico
from engine import Scene


class GameObject:
    def __init__(self):
        self._level = None
        self._id = None
        self._used = False

    @property
    def level(self):
        return self._level

    @property
    def id(self):
        return self._id

    def on_spawn(self):
        pass

    def on_destroy(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def render_items(self):
        return ()

    def destroy(self):
        if self._level is not None:
            self._level._destroy(self)


class GameMode:
    def __init__(self):
        self._level = None

    @property
    def level(self):
        return self._level

    def on_start(self):
        pass

    def on_event(self, event):
        pass

    def on_update(self, dt):
        pass

    def on_end(self):
        pass


class Level:
    def __init__(self, mode=None):
        if mode is None:
            mode = GameMode()
        if not isinstance(mode, GameMode):
            raise TypeError('GameMode 인스턴스가 필요합니다.')
        if mode.level is not None:
            raise RuntimeError('게임모드는 다른 레벨과 공유할 수 없습니다.')
        self._mode = mode
        mode._level = self
        self._objects = {}
        self._next_id = 1
        self._state = 'closed'
        self._dispatching = False
        self._cleaning = 0
        self._rendering = False

    @property
    def mode(self):
        return self._mode

    @property
    def objects(self):
        return tuple(self._objects.values())

    def get(self, object_id):
        return self._objects.get(object_id)

    def on_open(self):
        """레벨을 열 때마다 새 객체로 초기 배치를 구성한다."""

    def open(self):
        self._check_rendering()
        if self._state != 'closed' or self._dispatching or self._cleaning:
            raise RuntimeError('현재 단계에서는 레벨을 열 수 없습니다.')
        self._state = 'opening'
        try:
            self.on_open()
            if self._state != 'opening':
                raise RuntimeError('초기 배치 중 레벨이 닫혔습니다.')
            self.mode.on_start()
            if self._state != 'opening':
                raise RuntimeError('모드 시작 중 레벨이 닫혔습니다.')
            self._state = 'open'
        except BaseException as error:
            try:
                self.close()
            except BaseException as cleanup_error:
                raise BaseExceptionGroup('레벨 초기화와 정리 실패',
                                         [error, cleanup_error]) from None
            raise

    def spawn(self, obj):
        self._check_rendering()
        if not isinstance(obj, GameObject):
            raise TypeError('GameObject 인스턴스가 필요합니다.')
        if self._state not in ('opening', 'open') or self._cleaning:
            raise RuntimeError('현재 단계에서는 객체를 등록할 수 없습니다.')
        if obj._used:
            raise RuntimeError('한 번 등록한 객체는 다시 등록할 수 없습니다.')
        obj._used = True
        obj._level = self
        obj._id = self._next_id
        self._next_id += 1
        self._objects[obj.id] = obj
        try:
            obj.on_spawn()
        except BaseException as error:
            try:
                obj.destroy()
            except BaseException as cleanup_error:
                raise BaseExceptionGroup('객체 초기화와 정리 실패',
                                         [error, cleanup_error]) from None
            raise
        return obj

    def _destroy(self, obj):
        self._check_rendering()
        if obj.level is not self or self._objects.get(obj.id) is not obj:
            return
        del self._objects[obj.id]
        obj._level = None
        self._cleaning += 1
        try:
            obj.on_destroy()
        finally:
            self._cleaning -= 1

    def handle_event(self, event):
        self._dispatch('on_event', 'handle_event', event)

    def update(self, dt):
        self._dispatch('on_update', 'update', dt)

    def _dispatch(self, mode_method, object_method, value):
        self._check_rendering()
        if self._dispatching:
            raise RuntimeError('입력/업데이트 전달에 재진입할 수 없습니다.')
        if self._state != 'open':
            return
        snapshot = self.objects
        self._dispatching = True
        try:
            getattr(self.mode, mode_method)(value)
            for obj in snapshot:
                if obj.level is self:
                    getattr(obj, object_method)(value)
        finally:
            snapshot = ()
            self._dispatching = False

    def close(self):
        self._check_rendering()
        if self._state in ('closed', 'closing'):
            return
        self._state = 'closing'
        errors = []
        try:
            try:
                self.mode.on_end()
            except BaseException as error:
                errors.append(error)
            snapshot = self.objects
            try:
                for obj in snapshot:
                    try:
                        obj.destroy()
                    except BaseException as error:
                        errors.append(error)
            finally:
                snapshot = ()
        finally:
            self._state = 'closed'
        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise BaseExceptionGroup('레벨 정리 실패', errors)

    def _check_rendering(self):
        if self._rendering:
            raise RuntimeError('렌더링 중에는 레벨 수명·객체·전달을 변경할 수 없습니다.')


def _bounds(value):
    value = tuple(value)
    if (len(value) != 4 or not all(isfinite(v) for v in value) or
            value[0] > value[2] or value[1] > value[3]):
        raise ValueError('bounds는 유한한 (left, bottom, right, top)이어야 합니다.')
    return value


def _opacity(value):
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError('opacity는 유한한 0~1이어야 합니다.')
    return value


@dataclass(frozen=True)
class WorldTransform:
    """월드 y 위 방향과 출력 픽셀 y 아래 방향 사이의 직교 변환."""

    viewport: tuple
    center: tuple = (0, 0)
    view_height: float = 10

    def __post_init__(self):
        viewport, center = tuple(self.viewport), tuple(self.center)
        if (len(viewport) != 4 or not all(isfinite(v) for v in viewport) or
                min(viewport[2:]) < 0 or len(center) != 2 or
                not all(isfinite(v) for v in center) or
                not isfinite(self.view_height) or self.view_height <= 0):
            raise ValueError('카메라·viewport 값은 유한하고 시야는 양수여야 합니다.')
        object.__setattr__(self, 'viewport', viewport)
        object.__setattr__(self, 'center', center)

    @property
    def valid(self):
        return min(self.viewport[2:]) > 0

    @property
    def scale(self):
        return self.viewport[3] / self.view_height

    @property
    def bounds(self):
        if not self.valid:
            return None
        half_width = self.view_height * self.viewport[2] / self.viewport[3] / 2
        cx, cy = self.center
        return (cx - half_width, cy - self.view_height / 2,
                cx + half_width, cy + self.view_height / 2)

    def point(self, x, y):
        if not self.valid:
            return None
        vx, vy, vw, vh = self.viewport
        return (vx + vw / 2 + (x - self.center[0]) * self.scale,
                vy + vh / 2 - (y - self.center[1]) * self.scale)

    def inverse(self, x, y):
        if not self.valid:
            return None
        vx, vy, vw, vh = self.viewport
        return (self.center[0] + (x - vx - vw / 2) / self.scale,
                self.center[1] - (y - vy - vh / 2) / self.scale)

    def length(self, value):
        return value * self.scale


@dataclass(frozen=True)
class RenderItem:
    drawable: object
    draw_order: int = 0
    bounds: tuple | None = None
    visible: bool = True
    opacity: float = 1

    def __post_init__(self):
        if not callable(self.drawable) or type(self.draw_order) is not int:
            raise TypeError('drawable은 호출 가능하고 draw_order는 정수여야 합니다.')
        if self.bounds is not None:
            object.__setattr__(self, 'bounds', _bounds(self.bounds))
        _opacity(self.opacity)


def _intersects(bounds, view, padding=0):
    return not (bounds[2] < view[0] - padding or bounds[0] > view[2] + padding or
                bounds[3] < view[1] - padding or bounds[1] > view[3] + padding)



def _pair(value):
    value = tuple(value)
    if len(value) != 2 or not all(isfinite(v) for v in value):
        raise ValueError('유한한 좌표 두 개가 필요합니다.')
    return value


@dataclass(frozen=True)
class UITransform:
    """좌상단 UI 논리 좌표와 실제 출력 픽셀의 균등 변환."""

    viewport: tuple
    reference_size: tuple

    def __post_init__(self):
        viewport, reference = tuple(self.viewport), _pair(self.reference_size)
        if (len(viewport) != 4 or not all(isfinite(v) for v in viewport) or
                min(viewport[2:]) < 0 or min(reference) <= 0):
            raise ValueError('viewport는 유한한 비음수 크기, reference_size는 양수여야 합니다.')
        object.__setattr__(self, 'viewport', viewport)
        object.__setattr__(self, 'reference_size', reference)

    @property
    def valid(self):
        return min(self.viewport[2:]) > 0

    @property
    def scale(self):
        return min(self.viewport[2] / self.reference_size[0],
                   self.viewport[3] / self.reference_size[1])

    @property
    def logical_size(self):
        if not self.valid:
            return None
        return self.viewport[2] / self.scale, self.viewport[3] / self.scale

    @property
    def bounds(self):
        size = self.logical_size
        return None if size is None else (0, 0, *size)

    def point(self, x, y):
        if not self.valid:
            return None
        return self.viewport[0] + x * self.scale, self.viewport[1] + y * self.scale

    def inverse(self, x, y):
        if not self.valid:
            return None
        return (x - self.viewport[0]) / self.scale, (y - self.viewport[1]) / self.scale

    def length(self, value):
        return value * self.scale


class UIElement:
    def __init__(self, *, x=0, y=0, anchor=(0, 0), visible=True,
                 draw_order=0, bounds=None, opacity=1):
        self._canvas = self._parent = None
        self._children = []
        self._used = False
        self.x, self.y, self.anchor = x, y, _pair(anchor)
        self.visible, self.bounds, self.opacity = visible, bounds, opacity
        self.draw_order = draw_order
        self._validate()

    @property
    def canvas(self):
        return self._canvas

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        return tuple(self._children)

    @property
    def draw_order(self):
        return self._draw_order

    @draw_order.setter
    def draw_order(self, value):
        if self.canvas is not None:
            self.canvas._check_rendering()
        if type(value) is not int:
            raise TypeError('draw_order는 정수여야 합니다.')
        self._draw_order = value

    def _validate(self):
        _pair((self.x, self.y))
        anchor = _pair(self.anchor)
        if (not all(0 <= v <= 1 for v in anchor) or
                (self.parent is not None and anchor != (0, 0))):
            raise ValueError('anchor는 0~1 루트 기준점이며 자식은 (0,0)만 사용합니다.')
        if self.bounds is not None:
            _bounds(self.bounds)
        _opacity(self.opacity)

    def update(self, dt):
        pass

    def draw(self, origin, transform, opacity):
        """자기 그림만 그린다. 자식 방문은 Renderer가 담당한다."""

    def on_destroy(self):
        pass


def _ui_snapshot(roots):
    nodes, stack = [], list(reversed(roots))
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack.extend(reversed(node._children))
    return tuple(nodes)


class Canvas:
    def __init__(self, reference_size):
        self._reference_size = UITransform((0, 0, 0, 0), reference_size).reference_size
        self._roots = []
        self._closed = self._rendering = self._dispatching = False
        self._cleaning = 0

    @property
    def reference_size(self):
        return self._reference_size

    @property
    def roots(self):
        return tuple(self._roots)

    def transform(self, viewport):
        return UITransform(viewport, self.reference_size)

    def _check_rendering(self):
        if self._rendering:
            raise RuntimeError('렌더링 중에는 UI 트리·뎁스·전달을 변경할 수 없습니다.')

    def add(self, element, parent=None):
        self._check_rendering()
        if not isinstance(element, UIElement):
            raise TypeError('UIElement 인스턴스가 필요합니다.')
        if self._closed or self._cleaning or element._used:
            raise RuntimeError('새 노드만 열린 Canvas에 한 번 부착할 수 있습니다.')
        if parent is not None:
            if not isinstance(parent, UIElement) or parent.canvas is not self:
                raise RuntimeError('부모는 같은 Canvas에 부착되어 있어야 합니다.')
            if _pair(element.anchor) != (0, 0):
                raise ValueError('자식은 루트 anchor를 사용할 수 없습니다.')
        element._validate()
        element._used = True
        element._canvas, element._parent = self, parent
        (self._roots if parent is None else parent._children).append(element)
        return element

    def remove(self, element):
        self._check_rendering()
        if not isinstance(element, UIElement):
            raise TypeError('UIElement 인스턴스가 필요합니다.')
        if element.canvas is not self:
            return
        nodes = _ui_snapshot((element,))
        siblings = self._roots if element.parent is None else element.parent._children
        for index, sibling in enumerate(siblings):
            if sibling is element:
                del siblings[index]
                break
        self._clean(nodes)

    def _clean(self, nodes):
        for node in nodes:
            node._canvas = node._parent = None
            node._children.clear()
        errors = []
        self._cleaning += 1
        try:
            for node in reversed(nodes):
                try:
                    node.on_destroy()
                except BaseException as error:
                    errors.append(error)
        finally:
            self._cleaning -= 1
        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise BaseExceptionGroup('UI 정리 실패', errors)

    def update(self, dt):
        self._check_rendering()
        if self._dispatching:
            raise RuntimeError('UI 업데이트 전달에 재진입할 수 없습니다.')
        if self._closed:
            return
        snapshot = _ui_snapshot(self._roots)
        self._dispatching = True
        try:
            for element in snapshot:
                if element.canvas is self:
                    element.update(dt)
        finally:
            snapshot = ()
            self._dispatching = False

    def close(self):
        self._check_rendering()
        if self._closed:
            return
        self._closed = True
        nodes = _ui_snapshot(self._roots)
        self._roots.clear()
        self._clean(nodes)


class Renderer:
    def __init__(self):
        self.world_items = []
        self.ui_items = []
        self._drawing = False

    def draw(self, level, transform):
        if self._drawing or level._rendering or level._dispatching:
            raise RuntimeError('렌더링·전달에 재진입할 수 없습니다.')
        if not transform.valid or level._state != 'open':
            return
        self._drawing = level._rendering = True
        snapshot = level.objects
        try:
            for obj in snapshot:
                for item in obj.render_items():
                    if not isinstance(item, RenderItem):
                        raise TypeError('render_items는 RenderItem을 제공해야 합니다.')
                    if (item.visible and item.opacity > 0 and
                            (item.bounds is None or _intersects(
                                item.bounds, transform.bounds, 1 / transform.scale))):
                        self.world_items.append(item)
            self.world_items.sort(key=lambda item: item.draw_order)
            for item in self.world_items:
                item.drawable(transform, item.opacity)
        finally:
            self.world_items.clear()
            snapshot = ()
            self._drawing = level._rendering = False



    def draw_ui(self, canvas, transform):
        if self._drawing or canvas._rendering or canvas._dispatching:
            raise RuntimeError('렌더링·전달에 재진입할 수 없습니다.')
        if not transform.valid or canvas._closed:
            return
        self._drawing = canvas._rendering = True
        stack = []
        try:
            width, height = transform.logical_size
            for root in reversed(sorted(canvas.roots, key=lambda n: n.draw_order)):
                stack.append((root, (0, 0)))
            while stack:
                element, parent_origin = stack.pop()
                element._validate()
                if not element.visible:
                    continue
                x, y = parent_origin[0] + element.x, parent_origin[1] + element.y
                if element.parent is None:
                    x += element.anchor[0] * width
                    y += element.anchor[1] * height
                origin = (x, y)
                bounds = element.bounds
                if bounds is not None:
                    left, top, right, bottom = _bounds(bounds)
                    bounds = left + x, top + y, right + x, bottom + y
                if (element.opacity > 0 and (bounds is None or
                        _intersects(bounds, transform.bounds, 1 / transform.scale))):
                    self.ui_items.append((element, origin, element.opacity))
                for child in reversed(sorted(element.children, key=lambda n: n.draw_order)):
                    stack.append((child, origin))
            for element, origin, opacity in self.ui_items:
                element.draw(origin, transform, opacity)
        finally:
            stack.clear()
            self.ui_items.clear()
            self._drawing = canvas._rendering = False


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


class LevelScene(Scene):
    def __init__(self, level, *, camera_center=(0, 0), view_height=10):
        camera = WorldTransform((0, 0, 0, 0), camera_center, view_height)
        self.level = level
        self.camera_center, self.view_height = camera.center, camera.view_height
        self.renderer = Renderer()
        self.engine = None
        self._reset_generation = None

    @property
    def transform(self):
        viewport = self.engine.viewport if self.engine.output_valid else (0, 0, 0, 0)
        return WorldTransform(viewport, self.camera_center, self.view_height)

    def enter(self, engine):
        self.engine = engine
        self._reset_generation = engine.reset_generation
        self.level.open()

    def event_to_world(self, event):
        point = self.engine.event_to_output(event)
        return None if point is None else self.transform.inverse(*point)

    def handle_event(self, event):
        if event.type == pico.SDL_RENDER_DEVICE_RESET:
            raise RuntimeError('렌더 리셋으로 그리기 자원을 다시 만들어야 합니다.')
        if event.type == pico.SDL_RENDER_TARGETS_RESET:
            self._reset_generation += 1
        self.level.handle_event(event)

    def update(self, dt):
        self.level.update(dt)

    def draw(self):
        # shortcut: 장치/누락 리셋은 오류로 종료, 자원 로더 도입 때 재업로드로 확장한다.
        if self.engine.reset_generation != self._reset_generation:
            raise RuntimeError('렌더 리셋으로 그리기 자원을 다시 만들어야 합니다.')
        self.renderer.draw(self.level, self.transform)

    def exit(self):
        try:
            self.renderer.world_items.clear()
            self.level.close()
        finally:
            self.engine = None
