"""월드와 UI의 수집·정렬·렌더 패스."""

from dataclasses import dataclass

from ._validation import _bounds, _opacity


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


class Renderer:
    def __init__(self):
        self.world_items = []
        self.ui_items = []
        self._drawing = False

    def draw(self, level, transform, canvas=None):
        if canvas is None:
            return self._draw_world(level, transform)
        if (self._drawing or level._rendering or level._dispatching or
                canvas._rendering or canvas._dispatching):
            raise RuntimeError('렌더링·전달에 재진입할 수 없습니다.')
        ui_transform = canvas.transform(transform.viewport)
        try:
            # 다른 패스의 소유 API도 수집부터 그리기 끝까지 잠근다.
            canvas._rendering = True
            self._draw_world(level, transform)
            canvas._rendering = False
            level._rendering = True
            self.draw_ui(canvas, ui_transform)
        finally:
            self.world_items.clear()
            self.ui_items.clear()
            level._rendering = canvas._rendering = False

    def _draw_world(self, level, transform):
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
