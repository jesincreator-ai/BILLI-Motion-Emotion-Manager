"""Reference-style robot-eye animation presets with cooperative timing.

The shape presets and lid timing are adapted for BILLI from the MIT-licensed
ESP32 Robot Eyes project. This module remains MicroPython-friendly and does
not import Arduino, LovyanGFX, or desktop-only libraries.
"""
import math

from .emotion import EMOTIONS, _clamp, canonical_emotion
from .timebase import add_ms, diff_ms


# eye_open, eye_tilt, brow_tilt, glow, tear, fire, mouth,
# upper_lid, lower_lid, lid_tilt, eye_scale, pupil_scale
# Lid geometry matches the six reference mood presets.
_POSES = {
    "neutral": (0.88, 0.00, 0.00, 0.34, 0.00, 0.00, "closed",
                0.00, 0.00, 0.00, 1.00, 1.00),
    "happy": (0.78, 0.00, 0.10, 0.62, 0.00, 0.00, "smile",
              0.00, 0.55, 0.00, 1.00, 1.00),
    "sad": (0.62, -0.12, 0.15, 0.36, 0.00, 0.00, "frown",
            0.20, 0.00, -0.60, 0.95, 1.05),
    "angry": (0.59, 0.24, -0.28, 0.83, 0.00, 0.08, "tight",
              0.25, 0.00, 0.60, 1.00, 0.85),
    "sleepy": (0.50, 0.00, 0.00, 0.24, 0.00, 0.00, "closed",
               0.50, 0.00, 0.00, 1.00, 1.00),
    "surprise": (1.00, 0.00, 0.00, 0.88, 0.00, 0.00, "open",
                 0.00, 0.00, 0.00, 1.12, 0.70),
    "disappointment": (0.55, -0.08, 0.16, 0.25, 0.00, 0.00, "frown",
                       0.32, 0.00, -0.35, 0.96, 1.04),
    "sorry": (0.60, -0.09, 0.18, 0.31, 0.00, 0.00, "frown",
              0.28, 0.00, -0.45, 0.95, 1.05),
    "crying": (0.66, -0.08, 0.13, 0.45, 0.92, 0.00, "frown",
               0.20, 0.00, -0.60, 0.95, 1.05),
    "ego_fire": (0.72, 0.24, -0.32, 1.00, 0.00, 1.00, "open",
                 0.25, 0.00, 0.60, 1.00, 0.80),
}


class FaceAnimator:
    def __init__(
        self,
        blink_interval_ms=3200,
        blink_duration_ms=190,
        transition_duration_ms=320,
        auto_blink=True,
        idle_mode=True,
    ):
        self.blink_interval_ms = max(100, int(blink_interval_ms))
        self.blink_duration_ms = max(20, int(blink_duration_ms))
        self.transition_duration_ms = max(0, int(transition_duration_ms))
        self.auto_blink = bool(auto_blink)
        self.idle_mode = bool(idle_mode)
        self.expression = "neutral"
        self.intensity = 0.5
        self._next_blink_at = None
        self._blink_started_at = None
        self._eyes_closed = False
        self._blink_amount = 0.0
        self._blink_requested = False
        self._next_glance_at = None
        self._rng_state = 0xB111
        self._pupil_x = 0
        self._pupil_y = 0
        self._transition_started_at = 0
        self._transition_from = _POSES["neutral"]
        self._current_pose = _POSES["neutral"]
        self._target_pose = _POSES["neutral"]
        self._mouth = "closed"

    def _random(self):
        # Small deterministic LCG: no random module or entropy dependency.
        self._rng_state = (1103515245 * self._rng_state + 12345) & 0x7FFFFFFF
        return self._rng_state / 2147483648.0

    def _random_int(self, low, high):
        return int(low + (self._random() * (high - low + 1)))

    def _schedule_blink(self, now_ms, first=False):
        # Match the reference's occasional double blink while keeping
        # explicit test/custom intervals deterministic.
        if self.blink_interval_ms == 3200:
            delay = self._random_int(1500, 3000) if first else (
                250 if self._random() < 0.15 else self._random_int(2000, 5500)
            )
        else:
            delay = self.blink_interval_ms
        self._next_blink_at = add_ms(now_ms, delay)

    def blink(self):
        """Request one smooth blink on the next animation tick."""
        self._blink_requested = True

    def set_auto_blink(self, enabled):
        self.auto_blink = bool(enabled)
        if not self.auto_blink:
            self._next_blink_at = None

    def set_idle_mode(self, enabled):
        self.idle_mode = bool(enabled)
        self._next_glance_at = None
        if not self.idle_mode:
            self._pupil_x = 0
            self._pupil_y = 0

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

    def _update_blink(self, now_ms):
        if self.auto_blink and self._next_blink_at is None:
            self._schedule_blink(now_ms, first=True)

        scheduled = (
            self.auto_blink and self._next_blink_at is not None
            and diff_ms(now_ms, self._next_blink_at) >= 0
        )
        if self._blink_started_at is None and (self._blink_requested or scheduled):
            # Back-date a scheduled blink to its target time so a missed frame
            # does not stretch the animation.
            self._blink_started_at = self._next_blink_at if scheduled else now_ms

        self._blink_requested = False
        if self._blink_started_at is None:
            self._blink_amount = 0.0
            self._eyes_closed = False
            return

        elapsed = max(0, diff_ms(now_ms, self._blink_started_at))
        duration = self.blink_duration_ms
        close_ms = max(1.0, duration * (70.0 / 190.0))
        hold_ms = max(0.0, duration * (20.0 / 190.0))
        open_ms = max(1.0, duration - close_ms - hold_ms)

        if elapsed < close_ms:
            self._blink_amount = elapsed / close_ms
        elif elapsed < close_ms + hold_ms:
            self._blink_amount = 1.0
        elif elapsed < duration:
            self._blink_amount = 1.0 - ((elapsed - close_ms - hold_ms) / open_ms)
        else:
            self._blink_amount = 0.0
            self._blink_started_at = None
            if self.auto_blink:
                self._schedule_blink(now_ms)
        self._blink_amount = _clamp(self._blink_amount, 0.0, 1.0)
        self._eyes_closed = self._blink_started_at is not None

    def _update_idle_gaze(self, now_ms):
        if not self.idle_mode:
            return
        if self._next_glance_at is None:
            self._next_glance_at = add_ms(now_ms, 1000)
        if diff_ms(now_ms, self._next_glance_at) >= 0:
            if self._random() < 0.30:
                self._pupil_x = 0
                self._pupil_y = 0
            else:
                self._pupil_x = self._random_int(-8, 8)
                self._pupil_y = self._random_int(-6, 6)
            self._next_glance_at = add_ms(now_ms, self._random_int(800, 3500))

    def tick(self, now_ms):
        now_ms = int(now_ms)
        self._update_blink(now_ms)
        self._update_idle_gaze(now_ms)

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
        values = [a[i] + ((b[i] - a[i]) * eased) for i in range(6)]
        shape = [a[i] + ((b[i] - a[i]) * eased) for i in range(7, 12)]
        if progress >= 1.0:
            self._current_pose = self._target_pose

        phase = (now_ms % 6000) * (2.0 * math.pi / 6000.0)
        breathe = 0.5 + (0.5 * math.sin(phase))
        strength = self.intensity
        neutral = _POSES["neutral"]

        eye_open = neutral[0] + ((values[0] - neutral[0]) * strength)
        eye_tilt = values[1] * strength
        brow_tilt = values[2] * strength
        glow_base = neutral[3] + ((values[3] - neutral[3]) * strength)
        tear_base = values[4] * strength
        fire_base = values[5] * strength
        lid_top = neutral[7] + ((shape[0] - neutral[7]) * strength)
        lid_bottom = neutral[8] + ((shape[1] - neutral[8]) * strength)
        lid_tilt = shape[2] * strength
        eye_scale = neutral[10] + ((shape[3] - neutral[10]) * strength)
        pupil_scale = neutral[11] + ((shape[4] - neutral[11]) * strength)

        blink = self._blink_amount
        if blink > 0.0:
            # The embedded renderer uses lid masks for closure; eye_open is
            # retained for old telemetry consumers.
            eye_open = max(0.05, 1.0 - lid_top - lid_bottom)
        glow = _clamp(glow_base * (0.91 + (0.09 * breathe)), 0.0, 1.0)
        tear = _clamp(tear_base * (0.82 + (0.18 * math.sin(phase * 0.73))), 0.0, 1.0)
        fire = _clamp(fire_base * (0.72 + (0.28 * breathe)), 0.0, 1.0)
        gaze_x = _clamp((self._pupil_x / 8.0) + (math.sin(phase) * 0.035), -1.0, 1.0)
        gaze_y = _clamp((self._pupil_y / 6.0) + (math.sin(phase * 0.77) * 0.025), -1.0, 1.0)

        self._current_pose = (
            eye_open, eye_tilt, brow_tilt, glow_base, tear_base, fire_base,
            self._mouth, lid_top, lid_bottom, lid_tilt, eye_scale, pupil_scale,
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
            "lid_top": _clamp(lid_top, 0.0, 1.0),
            "lid_bottom": _clamp(lid_bottom, 0.0, 1.0),
            "lid_tilt": _clamp(lid_tilt, -1.0, 1.0),
            "eye_scale": _clamp(eye_scale, 0.7, 1.2),
            "pupil_scale": _clamp(pupil_scale, 0.6, 1.2),
            "transition": progress,
            "transitioning": progress < 1.0,
            "blink": blink,
            "glow": glow,
            "tear": tear,
            "fire": fire,
            "gaze_x": gaze_x,
            "gaze_y": gaze_y,
            "idle_breathe": breathe,
            "mouth": self._mouth,
            "mouth_open": 0.0,
        }
