"""Bounded, cooperative face animation model for the M6 renderers."""
import math

from .emotion import EMOTIONS, _clamp, canonical_emotion
from .timebase import add_ms, diff_ms


# eye opening, eye tilt, brow tilt, glow, tears, fire, mouth pose
_POSES = {
    "neutral": (0.88, 0.00, 0.00, 0.34, 0.00, 0.00, "closed"),
    "happy": (0.78, -0.05, 0.10, 0.62, 0.00, 0.00, "smile"),
    "sad": (0.62, 0.08, 0.15, 0.36, 0.00, 0.00, "frown"),
    "surprise": (1.00, 0.00, 0.00, 0.88, 0.00, 0.00, "open"),
    "disappointment": (0.55, 0.04, 0.16, 0.25, 0.00, 0.00, "frown"),
    "sorry": (0.60, 0.09, 0.18, 0.31, 0.00, 0.00, "frown"),
    "crying": (0.66, 0.03, 0.13, 0.45, 0.92, 0.00, "frown"),
    "angry": (0.59, -0.24, -0.28, 0.83, 0.00, 0.08, "tight"),
    "ego_fire": (0.72, -0.27, -0.32, 1.00, 0.00, 1.00, "open"),
}


class FaceAnimator:
    def __init__(
        self,
        blink_interval_ms=3200,
        blink_duration_ms=140,
        transition_duration_ms=320,
    ):
        self.blink_interval_ms = max(100, int(blink_interval_ms))
        self.blink_duration_ms = max(20, int(blink_duration_ms))
        self.transition_duration_ms = max(0, int(transition_duration_ms))
        self.expression = "neutral"
        self.intensity = 0.5
        self._next_blink_at = None
        self._blink_started_at = None
        self._eyes_closed = False
        self._pupil_x = 0
        self._pupil_y = 0
        self._transition_started_at = 0
        self._transition_from = _POSES["neutral"]
        self._current_pose = _POSES["neutral"]
        self._target_pose = _POSES["neutral"]
        self._mouth = "closed"

    def set_expression(self, expression, intensity=1.0, now_ms=0):
        expression = canonical_emotion(expression)
        if expression not in EMOTIONS:
            return False
        self._transition_from = self._current_pose
        self._target_pose = _POSES[expression]
        self._transition_started_at = int(now_ms)
        self.expression = expression
        self.intensity = _clamp(intensity, 0.0, 1.0)
        self._mouth = self._target_pose[6]
        if self.transition_duration_ms == 0:
            self._current_pose = self._target_pose
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

        elapsed = diff_ms(now_ms, self._transition_started_at)
        if elapsed < 0:
            elapsed = 0
        if self.transition_duration_ms == 0:
            progress = 1.0
        else:
            progress = _clamp(elapsed / float(self.transition_duration_ms), 0.0, 1.0)
        eased = progress * progress * (3.0 - (2.0 * progress))
        a = self._transition_from
        b = self._target_pose
        eye_open = a[0] + ((b[0] - a[0]) * eased)
        eye_tilt = a[1] + ((b[1] - a[1]) * eased)
        brow_tilt = a[2] + ((b[2] - a[2]) * eased)
        glow_base = a[3] + ((b[3] - a[3]) * eased)
        tear_base = a[4] + ((b[4] - a[4]) * eased)
        fire_base = a[5] + ((b[5] - a[5]) * eased)
        if progress >= 1.0:
            self._current_pose = self._target_pose

        phase = (now_ms % 6000) * (2.0 * math.pi / 6000.0)
        breathe = 0.5 + (0.5 * math.sin(phase))

        # Scale the expression back toward the neutral pose. This makes
        # intensity meaningful on the embedded display, not just in telemetry.
        strength = self.intensity
        neutral = _POSES["neutral"]
        eye_open = neutral[0] + ((eye_open - neutral[0]) * strength)
        eye_tilt = eye_tilt * strength
        brow_tilt = brow_tilt * strength
        glow_base = neutral[3] + ((glow_base - neutral[3]) * strength)
        tear_base = tear_base * strength
        fire_base = fire_base * strength

        glow = _clamp(glow_base * (0.91 + (0.09 * breathe)), 0.0, 1.0)
        tear = _clamp(tear_base * (0.82 + (0.18 * math.sin(phase * 0.73))), 0.0, 1.0)
        fire = _clamp(fire_base * (0.72 + (0.28 * breathe)), 0.0, 1.0)
        blink = 1.0 if self._eyes_closed else 0.0
        if self._eyes_closed:
            eye_open = 0.05
        gaze_x = _clamp((self._pupil_x / 8.0) + (math.sin(phase) * 0.035), -1.0, 1.0)
        gaze_y = _clamp((self._pupil_y / 5.0) + (math.sin(phase * 0.77) * 0.025), -1.0, 1.0)
        self._current_pose = (
            eye_open, eye_tilt, brow_tilt, glow_base, tear_base, fire_base, self._mouth
        )
        return {
            "expression": self.expression,
            "intensity": self.intensity,
            "eyes_closed": self._eyes_closed,
            "pupil_x": self._pupil_x,
            "pupil_y": self._pupil_y,
            "eye_open": _clamp(eye_open, 0.0, 1.0),
            "eye_tilt": _clamp(eye_tilt, -1.0, 1.0),
            "brow_tilt": _clamp(brow_tilt, -1.0, 1.0),
            "transition": progress,
            "transitioning": progress < 1.0,
            "blink": blink,
            "glow": glow,
            "tear": tear,
            "fire": fire,
            "gaze_x": _clamp(gaze_x, -1.0, 1.0),
            "gaze_y": _clamp(gaze_y, -1.0, 1.0),
            "idle_breathe": breathe,
            "mouth": self._mouth,\n            "mouth_open": 0.0,
        }
