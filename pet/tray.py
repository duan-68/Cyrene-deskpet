from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction


class Tray:
    def __init__(self, app, icon_path, on_quit, on_toggle_pause, on_toggle_audio):
        self._tray = QSystemTrayIcon(QIcon(str(icon_path)), app)
        menu = QMenu()

        self._pause_action = QAction("暂停监控", menu)
        self._pause_action.setCheckable(True)
        self._pause_action.triggered.connect(
            lambda checked: on_toggle_pause(checked))
        menu.addAction(self._pause_action)

        self._audio_action = QAction("音效", menu)
        self._audio_action.setCheckable(True)
        self._audio_action.setChecked(True)
        self._audio_action.triggered.connect(
            lambda checked: on_toggle_audio(checked))
        menu.addAction(self._audio_action)

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(on_quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.setToolTip("桌宠")
        self._tray.show()

    def set_paused(self, paused):
        self._pause_action.setChecked(paused)

    def set_audio(self, enabled):
        self._audio_action.setChecked(enabled)

    def notify(self, msg):
        self._tray.showMessage("桌宠", msg)
