import unittest
from billi_motion.emotion import EmotionEngine
from billi_motion.animation import FaceAnimator
from billi_motion.speech import SpeechSynchronizer
from billi_motion.events import EventQueue
from billi_motion.manager import MotionEmotionManager
from billi_motion.locales import phrase


class EmotionTests(unittest.TestCase):
    def test_unknown_emotion_is_rejected_and_intensity_is_bounded(self):
        engine = EmotionEngine()
        self.assertFalse(engine.set_emotion("not-a-face", 0.5, 0))
        self.assertTrue(engine.set_emotion("happy", 4.0, 10))
        self.assertEqual(engine.get_state()["emotion"], "happy")
        self.assertEqual(engine.get_state()["intensity"], 1.0)

    def test_expression_changes_through_tick_state(self):
        engine = EmotionEngine()
        engine.set_emotion("sad", 0.7, 20)
        state = engine.tick(30)
        self.assertEqual(state["emotion"], "sad")
        self.assertAlmostEqual(state["intensity"], 0.7)


class AnimationTests(unittest.TestCase):
    def test_blink_is_timed_and_returns_to_open_eyes(self):
        animator = FaceAnimator(blink_interval_ms=100, blink_duration_ms=20)
        self.assertFalse(animator.tick(0)["eyes_closed"])
        self.assertTrue(animator.tick(100)["eyes_closed"])
        self.assertTrue(animator.tick(115)["eyes_closed"])
        self.assertFalse(animator.tick(121)["eyes_closed"])

    def test_expression_is_validated(self):
        animator = FaceAnimator()
        self.assertFalse(animator.set_expression("unknown"))
        self.assertTrue(animator.set_expression("surprised"))
        self.assertEqual(animator.tick(0)["expression"], "surprise")


class SpeechTests(unittest.TestCase):
    def test_speech_level_drives_mouth_and_is_clamped(self):
        speech = SpeechSynchronizer(open_threshold=0.2)
        speech.begin_speech(0)
        self.assertEqual(speech.update(10, 0.8), "open")
        self.assertEqual(speech.update(20, 0.0), "closed")
        self.assertEqual(speech.update(30, 5.0), "open")
        speech.end_speech()
        self.assertEqual(speech.update(40, 1.0), "closed")


class EventQueueTests(unittest.TestCase):
    def test_fixed_queue_drops_oldest_when_full(self):
        queue = EventQueue(2)
        queue.push({"kind": "one"})
        queue.push({"kind": "two"})
        queue.push({"kind": "three"})
        self.assertEqual(queue.pop()["kind"], "two")
        self.assertEqual(queue.pop()["kind"], "three")
        self.assertIsNone(queue.pop())


class ManagerIntegrationTests(unittest.TestCase):
    def test_manager_combines_emotion_speech_and_bounded_events(self):
        manager = MotionEmotionManager(event_capacity=2)
        self.assertTrue(manager.set_emotion("happy", 0.8, 5))
        manager.begin_speech(6)
        manager.update_speech_level(7, 0.9)
        frame = manager.tick(8)
        self.assertEqual(frame["emotion"], "happy")
        self.assertEqual(frame["mouth"], "open")
        self.assertIsNotNone(manager.next_event())

    def test_tamil_and_sinhala_phrases_are_available(self):
        self.assertTrue(phrase("happy", "ta"))
        self.assertTrue(phrase("happy", "si"))


if __name__ == "__main__":
    unittest.main()
