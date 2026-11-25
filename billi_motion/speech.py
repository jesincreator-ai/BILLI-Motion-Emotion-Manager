"""Speech-to-mouth synchronization driven by a local audio amplitude sample."""
from .emotion import _clamp


class SpeechSynchronizer:
    def __init__(self, open_threshold=0.18):
        self.open_threshold = _clamp(open_threshold, 0.01, 1.0)
        self.active = False
        self.last_level = 0.0
        self.last_update_ms = 0
        self.mouth = "closed"

    def begin_speech(self, now_ms, intensity=1.0):
        self.active = True
        self.last_update_ms = int(now_ms)
        self.last_level = _clamp(intensity, 0.0, 1.0)

    def update(self, now_ms, amplitude):
        self.last_update_ms = int(now_ms)
        self.last_level = _clamp(amplitude, 0.0, 1.0)
        self.mouth = "open" if self.active and self.last_level >= self.open_threshold else "closed"
        return self.mouth

    def end_speech(self):
        self.active = False
        self.last_level = 0.0
        self.mouth = "closed"
