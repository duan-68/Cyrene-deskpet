from collections import deque
from dataclasses import dataclass


@dataclass
class ActionRequest:
    filename: str
    icon_info: object


class Dispatcher:
    def __init__(self, snapshot, window, audio, max_queue=10):
        self._snapshot = snapshot
        self._window = window
        self._audio = audio
        self._queue = deque(maxlen=max_queue)
        self._current = None
        self._running = True

    def on_delete(self, filename, mode):
        if not self._running:
            return
        info = self._snapshot.get(filename)
        if info is None:
            return
        self._queue.append(ActionRequest(filename, info))
        self._maybe_start_next()

    def _maybe_start_next(self):
        if self._current is not None or not self._queue:
            return
        self._current = self._queue.popleft()
        self._window.play_sequence(self._current.icon_info, self._on_done)

    def _on_done(self):
        self._current = None
        self._maybe_start_next()

    def stop(self):
        self._running = False
        self._queue.clear()
