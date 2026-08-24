from pet.icon_snapshot import IconSnapshot


def test_snapshot_returns_none_when_missing():
    s = IconSnapshot.__new__(IconSnapshot)
    s._snapshot = {}
    assert s.get("x.lnk") is None


def test_snapshot_returns_cached_info():
    s = IconSnapshot.__new__(IconSnapshot)

    class I:
        filename = "x.lnk"
        x = 1
        y = 2
        icon = "I"

    s._snapshot = {"x.lnk": I()}
    got = s.get("x.lnk")
    assert got.x == 1 and got.y == 2
