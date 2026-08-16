from pet.dispatcher import Dispatcher


class _Snapshot:
    def __init__(self, data):
        self.data = data

    def get(self, name):
        return self.data.get(name)


class _Window:
    def __init__(self):
        self.calls = []

    def play_sequence(self, info, on_done):
        self.calls.append(info.filename)
        self.on_done = on_done


class _Audio:
    def play(self, name):
        pass


class _Info:
    def __init__(self, name):
        self.filename = name
        self.x = 10
        self.y = 20
        self.icon = "ICON"


def test_on_delete_dispatches_sequence():
    info = _Info("foo.lnk")
    snap = _Snapshot({"foo.lnk": info})
    win = _Window()
    d = Dispatcher(snap, win, _Audio())
    d.on_delete("foo.lnk", "deleted")
    assert win.calls == ["foo.lnk"]


def test_on_delete_unknown_icon_skips():
    snap = _Snapshot({})
    win = _Window()
    d = Dispatcher(snap, win, _Audio())
    d.on_delete("missing.lnk", "deleted")
    assert win.calls == []


def test_queue_serializes_and_advances():
    i1, i2 = _Info("a.lnk"), _Info("b.lnk")
    snap = _Snapshot({"a.lnk": i1, "b.lnk": i2})
    win = _Window()
    d = Dispatcher(snap, win, _Audio())
    d.on_delete("a.lnk", "deleted")
    d.on_delete("b.lnk", "deleted")
    assert win.calls == ["a.lnk"]
    win.on_done()
    assert win.calls == ["a.lnk", "b.lnk"]


def test_stop_ignores_further_deletes():
    info = _Info("a.lnk")
    snap = _Snapshot({"a.lnk": info})
    win = _Window()
    d = Dispatcher(snap, win, _Audio())
    d.stop()
    d.on_delete("a.lnk", "deleted")
    assert win.calls == []
