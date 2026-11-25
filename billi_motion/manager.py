"""Top-level face/emotion manager with bounded events and selectable visual modes."""
from .emotion import EmotionEngine, canonical_emotion
from .animation import FaceAnimator
from .speech import SpeechSynchronizer
from .events import EventQueue


class MotionEmotionManager:
    MODES = ("standard", "rugged")
    MODE_ALIASES = {"calm": "standard"}
    STANDARD_EMOTIONS = (
        "happy", "sad", "surprise", "disappointment", "sorry", "crying"
    )
    RUGGED_EMOTIONS = ("angry", "ego_fire")

    def __init__(self, event_capacity=16, mode="standard"):
        self.emotion = EmotionEngine()
        self.animator = FaceAnimator()
        self.speech = SpeechSynchronizer()
        self.events = EventQueue(event_capacity)
        mode = self.MODE_ALIASES.get(mode, mode)
        self.mode = mode if mode in self.MODES else "standard"

    def _emotion_allowed(self, emotion):
        if emotion == "neutral":
            return True
        allowed = self.RUGGED_EMOTIONS if self.mode == "rugged" else self.STANDARD_EMOTIONS
        return emotion in allowed

    def set_mode(self, mode, now_ms=0):
        """Switch face theme. Calm is an alias for standard; neutral is universal."""
        mode = self.MODE_ALIASES.get(mode, mode)
        if mode not in self.MODES:
            return False
        if mode != self.mode:
            self.mode = mode
            current = self.emotion.get_state()["emotion"]
            if not self._emotion_allowed(current):
                self.emotion.set_emotion("neutral", 0.5, now_ms)
                self.animator.set_expression("neutral", 0.5, now_ms)
            self.events.push({"kind": "mode", "value": mode, "at_ms": int(now_ms)})
        return True

    def set_emotion(self, emotion, intensity=1.0, now_ms=0):
        emotion = canonical_emotion(emotion)
        if not self._emotion_allowed(emotion):
            return False
        if not self.emotion.set_emotion(emotion, intensity, now_ms):
            return False
        self.animator.set_expression(emotion, intensity, now_ms)
        self.events.push({"kind": "emotion", "value": emotion, "at_ms": int(now_ms)})
        return True

    def begin_speech(self, now_ms, intensity=1.0):
        self.speech.begin_speech(now_ms, intensity)
        self.events.push({"kind": "speech_start", "at_ms": int(now_ms)})

    def update_speech_level(self, now_ms, amplitude):
        return self.speech.update(now_ms, amplitude)

    def end_speech(self):
        self.speech.end_speech()
        self.events.push({"kind": "speech_end"})

    def look(self, x=0, y=0):
        self.animator.look(x, y)

    def tick(self, now_ms):
        frame = self.animator.tick(now_ms)
        if self.speech.active:
            frame["mouth"] = "open" if self.speech.mouth == "open" else "closed"\n            frame["mouth_pose"] = "talk" if self.speech.mouth == "open" else "closed"
            frame["mouth_open"] = self.speech.smoothed_level if self.speech.mouth == "open" else 0.0
            frame["speech_active"] = True
        else:
            frame["mouth_open"] = 0.0
            frame["speech_active"] = False
        frame["emotion"] = self.emotion.get_state()["emotion"]
        frame["mode"] = self.mode
        frame["color"] = "red" if self.mode == "rugged" else "white"
        return frame

    def next_event(self):
        return self.events.pop()
