import math
import time
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget, QApplication

from . import config


def _load_frames(d, prefix, count):
    out = []
    for i in range(1, count + 1):
        p = Path(d) / f"{prefix}_{i:02d}.png"
        if p.exists():
            out.append(QPixmap(str(p)))
    return out


class PetWindow(QWidget):
    def __init__(self, frames_dir, audio):
        super().__init__()
        self._audio = audio
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._screen = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(self._screen)

        self._idle = _load_frames(frames_dir, "idle", 4) or [QPixmap()]
        self._move = _load_frames(frames_dir, "move", 4) or self._idle
        self._act = _load_frames(frames_dir, "act", 2) or self._idle

        self._paused = False
        self._pet_pos = QPoint(
            self._screen.width() // 2, self._screen.height() - 250)
        self._frames = self._idle
        self._frame_idx = 0

        self._stage = "idle"
        self._stage_start = 0.0
        self._on_done = None
        self._start_pos = QPoint()
        self._target_pos = QPoint()
        self._trash_pos = QPoint(60, 60)
        self._icon_pm = None
        self._icon_pos = QPoint()
        self._icon_scale = 1.0
        self._icon_opacity = 1.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // config.ANIMATION_FPS)

    def show_pet(self):
        self.show()

    def set_paused(self, paused):
        self._paused = paused

    def _win_pt(self, x, y):
        return QPoint(x - self._screen.x(), y - self._screen.y())

    def play_sequence(self, icon_info, on_done):
        self._on_done = on_done
        self._icon_pm = icon_info.icon.pixmap(
            config.ICON_SIZE, config.ICON_SIZE)
        self._icon_pos = self._win_pt(icon_info.x, icon_info.y)
        self._icon_scale = 1.0
        self._icon_opacity = 1.0
        self._start_pos = QPoint(self._pet_pos)
        self._target_pos = QPoint(
            self._icon_pos.x() - 80, self._icon_pos.y() - 60)
        self._trash_pos = self._find_trash_pos()
        self._stage = "moving"
        self._stage_start = time.monotonic()
        self._frames = self._move

    def _find_trash_pos(self):
        # 回收站默认在桌面左上角，用固定近似位置
        return QPoint(60, 60)

    def _tick(self):
        if self._paused:
            return
        self._frame_idx += 1
        now = time.monotonic()
        if self._stage == "moving":
            self._advance_moving(now)
        elif self._stage == "throwing":
            self._advance_throwing(now)
        elif self._stage == "kicking":
            self._advance_kicking(now)
        self.update()

    def _progress(self, now, duration):
        return min(1.0, (now - self._stage_start) * 1000 / duration)

    def _advance_moving(self, now):
        t = self._progress(now, config.MOVE_DURATION_MS)
        e = t * t * (3 - 2 * t)
        self._pet_pos = QPoint(
            round(self._start_pos.x()
                  + (self._target_pos.x() - self._start_pos.x()) * e),
            round(self._start_pos.y()
                  + (self._target_pos.y() - self._start_pos.y()) * e))
        if t >= 1.0:
            self._audio.play("move")
            self._stage = "throwing"
            self._stage_start = now
            self._frames = self._act

    def _advance_throwing(self, now):
        t = self._progress(now, config.THROW_DURATION_MS)
        sx, sy = self._icon_pos.x(), self._icon_pos.y()
        tx, ty = self._trash_pos.x(), self._trash_pos.y()
        cx = sx + (tx - sx) * t
        cy = sy + (ty - sy) * t - math.sin(t * math.pi) * 120
        self._icon_pos = QPoint(round(cx), round(cy))
        self._icon_scale = 1.0 - 0.6 * t
        self._icon_opacity = 1.0 - t
        if t >= 1.0:
            self._audio.play("throw")
            self._stage = "kicking"
            self._stage_start = now

    def _advance_kicking(self, now):
        t = self._progress(now, config.KICK_DURATION_MS)
        vx = self._screen.width() + 200
        vy = self._trash_pos.y() - 400 * t
        self._icon_pos = QPoint(round(self._trash_pos.x() + vx * t), round(vy))
        self._icon_opacity = 1.0 - t
        if t >= 1.0:
            self._audio.play("kick")
            self._finish()

    def _finish(self):
        self._stage = "idle"
        self._frames = self._idle
        self._icon_pm = None
        cb = self._on_done
        self._on_done = None
        if cb:
            cb()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        pm = self._frames[self._frame_idx % len(self._frames)]
        painter.drawPixmap(self._pet_pos, pm)
        if self._icon_pm and self._icon_pos:
            painter.setOpacity(self._icon_opacity)
            w = round(self._icon_pm.width() * self._icon_scale)
            h = round(self._icon_pm.height() * self._icon_scale)
            painter.drawPixmap(
                QRect(self._icon_pos.x(), self._icon_pos.y(),
                      max(1, w), max(1, h)),
                self._icon_pm)
            painter.setOpacity(1.0)
