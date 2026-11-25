"""Compact deterministic emotion state engine; no model or network required."""

EMOTIONS = (
    "neutral",
    "happy",
    "sad",
    "surprise",
    "disappointment",
    "sorry",
    "crying",
    "angry",
    "ego_fire",
)
EMOTION_ALIASES = {"surprised": "surprise"}


def canonical_emotion(emotion):
    """Return the canonical emotion name, preserving unknown values for validation."""
    return EMOTION_ALIASES.get(emotion, emotion)


def _clamp(value, low, high):
    value = float(value)
    if value < low:
        return low
    if value > high:
        return high
    return value


class EmotionEngine:
    def __init__(self, initial="neutral"):
        initial = canonical_emotion(initial)
        if initial not in EMOTIONS:
            initial = "neutral"
        self._emotion = initial
        self._intensity = 0.5 if initial == "neutral" else 1.0
        self._changed_at = 0

    def set_emotion(self, emotion, intensity=1.0, now_ms=0):
        emotion = canonical_emotion(emotion)
        if emotion not in EMOTIONS:
            return False
        self._emotion = emotion
        self._intensity = _clamp(intensity, 0.0, 1.0)
        self._changed_at = int(now_ms)
        return True

    def tick(self, now_ms):
        return self.get_state()

    def get_state(self):
        return {
            "emotion": self._emotion,
            "intensity": self._intensity,
            "changed_at_ms": self._changed_at,
        }
