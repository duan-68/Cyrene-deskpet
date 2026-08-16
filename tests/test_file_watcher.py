from pet.file_watcher import DesktopDeleteHandler, is_recycle_bin


class _Event:
    def __init__(self, src, dest=None, is_dir=False):
        self.src_path = src
        self.dest_path = dest or ""
        self.is_directory = is_dir


def test_is_recycle_bin():
    assert is_recycle_bin("C:\\$Recycle.Bin\\S-1-5-18\\x.lnk")
    assert not is_recycle_bin("C:\\Users\\a\\Desktop\\x.lnk")


def test_handler_fires_on_deleted_lnk():
    seen = []
    h = DesktopDeleteHandler(lambda f, m: seen.append((f, m)))
    h.on_deleted(_Event("C:\\Users\\a\\Desktop\\foo.lnk"))
    assert seen == [("foo.lnk", "deleted")]


def test_handler_ignores_non_lnk_and_directory():
    seen = []
    h = DesktopDeleteHandler(lambda f, m: seen.append((f, m)))
    h.on_deleted(_Event("C:\\Users\\a\\Desktop\\a.txt"))
    h.on_deleted(_Event("C:\\Users\\a\\Desktop\\x.lnk", is_dir=True))
    assert seen == []


def test_handler_fires_on_moved_to_recycle_bin():
    seen = []
    h = DesktopDeleteHandler(lambda f, m: seen.append((f, m)))
    h.on_moved(_Event("C:\\Users\\a\\Desktop\\foo.lnk",
                      "C:\\$Recycle.Bin\\S-1-5-18\\foo.lnk"))
    assert seen == [("foo.lnk", "moved")]


def test_handler_ignores_moved_not_to_recycle():
    seen = []
    h = DesktopDeleteHandler(lambda f, m: seen.append((f, m)))
    h.on_moved(_Event("C:\\Users\\a\\Desktop\\foo.lnk",
                      "C:\\Users\\a\\Desktop\\foo2.lnk"))
    assert seen == []
