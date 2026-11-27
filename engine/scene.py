"""엔진 장면 콜백 계약."""

class Scene:
    def enter(self, engine: 'Engine') -> None:
        pass

    def handle_event(self, event) -> None:
        pass

    def handle_escape(self) -> bool:
        """True를 반환하면 장면이 Escape를 처리한 것으로 본다."""
        return False

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        pass

    def exit(self) -> None:
        pass
