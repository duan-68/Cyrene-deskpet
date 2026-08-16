import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from . import config
from .audio import Audio
from .dispatcher import Dispatcher
from .file_watcher import FileWatcher
from .icon_snapshot import IconSnapshot
from .pet_window import PetWindow
from .tray import Tray


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    audio = Audio(config.SOUNDS_DIR, enabled=True)
    window = PetWindow(config.FRAMES_DIR, audio)
    snapshot = IconSnapshot(config.DESKTOP_PATH)
    dispatcher = Dispatcher(snapshot, window, audio)
    watcher = FileWatcher(config.DESKTOP_PATH, dispatcher.on_delete)

    snap_timer = QTimer()
    snap_timer.timeout.connect(snapshot.refresh)
    snap_timer.start(config.SNAPSHOT_INTERVAL_MS)
    snapshot.refresh()

    window.show_pet()

    def toggle_pause(checked):
        window.set_paused(checked)
        dispatcher.set_paused(checked)

    def toggle_audio(checked):
        audio.enabled = checked

    tray = Tray(app, config.PET_SRC,
                on_quit=app.quit,
                on_toggle_pause=toggle_pause,
                on_toggle_audio=toggle_audio)

    watcher.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
