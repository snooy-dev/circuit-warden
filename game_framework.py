"""창과 독립적인 레벨 소유·객체 수명·규칙 전달."""


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
