"""Speech-to-mouth synchronization driven by a normalized local audio amplitude."""
from .emotion import _clamp


class SpeechSynchronizer:
    """Small amplitude envelope follower; no audio buffers or allocations retained."""

    def __init__(self, open_threshold=0.12, smoothing=0.45):
        self.open_threshold = _clamp(open_threshold, 0.01, 1.0)
        self.smoothing = _clamp(smoothing, 0.05, 1.0)
        self.active = False
        self.last_level = 0.0
        self.smoothed_level = 0.0
        self.last_update_ms = 0
        self.mouth = "closed"

    def begin_speech(self, now_ms, intensity=1.0):
        self.active = True
        self.last_update_ms = int(now_ms)
        self.last_level = _clamp(intensity, 0.0, 1.0)
        self.smoothed_level = self.last_level
        self.mouth = "open" if self.smoothed_level >= self.open_threshold else "closed"

    def update(self, now_ms, amplitude):
        self.last_update_ms = int(now_ms)
        self.last_level = _clamp(amplitude, 0.0, 1.0)
        self.smoothed_level += (self.last_level - self.smoothed_level) * self.smoothing
        if not self.active or self.smoothed_level < self.open_threshold:
            self.mouth = "closed"
        else:
            self.mouth = "open"
        return self.mouth

    def end_speech(self):
        self.active = False
        self.last_level = 0.0
        self.smoothed_level = 0.0
        self.mouth = "closed"
