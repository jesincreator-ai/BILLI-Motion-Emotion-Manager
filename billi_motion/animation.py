"""Compact face animation state; rendering is delegated to a display adapter."""
from .emotion import EMOTIONS, _clamp
from .timebase import add_ms, diff_ms


class FaceAnimator:
    def __init__(self, blink_interval_ms=3200, blink_duration_ms=140):
        self.blink_interval_ms = max(100, int(blink_interval_ms))
        self.blink_duration_ms = max(20, int(blink_duration_ms))
        self.expression = "neutral"
        self.intensity = 0.5
        self._next_blink_at = None
        self._blink_started_at = None
        self._eyes_closed = False
        self._pupil_x = 0
        self._pupil_y = 0

    def set_expression(self, expression, intensity=1.0):
        if expression not in EMOTIONS:
            return False
        self.expression = expression
        self.intensity = _clamp(intensity, 0.0, 1.0)
        return True

    def look(self, x=0, y=0):
        self._pupil_x = int(max(-8, min(8, x)))
        self._pupil_y = int(max(-5, min(5, y)))

    def tick(self, now_ms):
        now_ms = int(now_ms)
        if self._next_blink_at is None:
            self._next_blink_at = add_ms(now_ms, self.blink_interval_ms)
        if not self._eyes_closed and diff_ms(now_ms, self._next_blink_at) >= 0:
            self._eyes_closed = True
            self._blink_started_at = now_ms
        if self._eyes_closed and diff_ms(now_ms, self._blink_started_at) >= self.blink_duration_ms:
            self._eyes_closed = False
            self._blink_started_at = None
            self._next_blink_at = add_ms(now_ms, self.blink_interval_ms)
        mouth = "closed"
        if self.expression in ("happy", "surprised"):
            mouth = "smile" if self.expression == "happy" else "open"
        elif self.expression == "sad":
            mouth = "frown"
        elif self.expression == "angry":
            mouth = "tight"
        return {
            "expression": self.expression,
            "intensity": self.intensity,
            "eyes_closed": self._eyes_closed,
            "pupil_x": self._pupil_x,
            "pupil_y": self._pupil_y,
            "mouth": mouth,
        }
