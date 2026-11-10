"""UI 트리의 소유·수명·업데이트."""

from ._validation import _bounds, _opacity, _pair
from .transforms import UITransform


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
            self._update_snapshot(dt, snapshot)
        finally:
            snapshot = ()
            self._dispatching = False

    def _update_snapshot(self, dt, snapshot):
        if self._closed:
            return
        for element in snapshot:
            if element.canvas is self:
                element.update(dt)

    def close(self):
        self._check_rendering()
        if self._closed:
            return
        self._closed = True
        nodes = _ui_snapshot(self._roots)
        self._roots.clear()
        self._clean(nodes)
