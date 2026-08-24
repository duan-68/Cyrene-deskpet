import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def is_recycle_bin(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return "$Recycle.Bin" in parts


class DesktopDeleteHandler(FileSystemEventHandler):
    def __init__(self, on_delete):
        self._on_delete = on_delete

    def _handle(self, src_path, mode):
        # 监控所有文件类型（不只是 .lnk）
        self._on_delete(os.path.basename(src_path), mode)

    def on_deleted(self, event):
        if not event.is_directory:
            self._handle(event.src_path, "deleted")

    def on_moved(self, event):
        if not event.is_directory and is_recycle_bin(event.dest_path):
            self._handle(event.src_path, "moved")


class FileWatcher:
    def __init__(self, directory: Path, on_delete):
        self._observer = Observer()
        self._observer.schedule(
            DesktopDeleteHandler(on_delete), str(directory), recursive=False)

    def start(self):
        self._observer.start()

    def stop(self):
        self._observer.stop()
        self._observer.join(timeout=5)
