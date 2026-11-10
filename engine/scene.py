"""엔진 장면 콜백 계약."""

class Scene:
    def enter(self, engine: 'Engine') -> None:
        pass

    def handle_event(self, event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        pass

    def exit(self) -> None:
        pass
