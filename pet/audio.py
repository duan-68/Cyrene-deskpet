import winsound
from pathlib import Path


class Audio:
    def __init__(self, sounds_dir, enabled=True):
        self._dir = Path(sounds_dir)
        self._enabled = enabled

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    def play(self, name):
        if not self._enabled:
            return
        path = self._dir / f"{name}.wav"
        if path.exists():
            winsound.PlaySound(
                str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
