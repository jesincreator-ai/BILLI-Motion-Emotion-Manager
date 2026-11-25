"""Top-level face and emotion manager with a tiny, bounded event queue."""
from .emotion import EmotionEngine
from .animation import FaceAnimator
from .speech import SpeechSynchronizer
from .events import EventQueue


class MotionEmotionManager:
    def __init__(self, event_capacity=16):
        self.emotion = EmotionEngine()
        self.animator = FaceAnimator()
        self.speech = SpeechSynchronizer()
        self.events = EventQueue(event_capacity)

    def set_emotion(self, emotion, intensity=1.0, now_ms=0):
        if not self.emotion.set_emotion(emotion, intensity, now_ms):
            return False
        self.animator.set_expression(emotion, intensity)
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
            frame["mouth"] = self.speech.mouth
        frame["emotion"] = self.emotion.get_state()["emotion"]
        return frame

    def next_event(self):
        return self.events.pop()
