import unittest

from billi_motion.manager import MotionEmotionManager
from billi_motion.speech import SpeechSynchronizer


class MouthSpeechTests(unittest.TestCase):
    def test_speech_level_is_smoothed_and_clamped(self):
        sync = SpeechSynchronizer(smoothing=0.5)
        sync.begin_speech(0, 0.0)
        sync.update(20, 1.0)
        self.assertEqual(sync.mouth, "open")
        self.assertAlmostEqual(sync.smoothed_level, 0.5)
        sync.update(40, 2.0)
        self.assertLessEqual(sync.smoothed_level, 1.0)
        sync.end_speech()
        self.assertEqual(sync.mouth, "closed")
        self.assertEqual(sync.smoothed_level, 0.0)

    def test_mouth_talk_overlay_does_not_replace_emotion_rest_pose(self):
        manager = MotionEmotionManager()
        manager.set_emotion("happy", 1.0, 0)
        rest = manager.tick(400)["mouth"]
        self.assertEqual(rest, "smile")
        manager.begin_speech(500, 0.0)
        manager.update_speech_level(520, 0.8)
        talking = manager.tick(540)
        self.assertEqual(talking["mouth"], "open")
        self.assertEqual(talking["mouth_pose"], "talk")
        self.assertGreater(talking["mouth_open"], 0.0)
        manager.end_speech()
        after = manager.tick(560)
        self.assertEqual(after["mouth"], "smile")
        self.assertEqual(after["mouth_pose"], "smile")
        self.assertEqual(after["mouth_open"], 0.0)

    def test_low_volume_speech_closes_mouth_without_losing_emotion(self):
        manager = MotionEmotionManager()
        manager.set_emotion("sad", 0.8, 0)
        manager.begin_speech(100, 0.0)
        manager.update_speech_level(120, 0.01)
        frame = manager.tick(130)
        self.assertEqual(frame["mouth"], "closed")
        self.assertEqual(frame["emotion"], "sad")
        manager.end_speech()
        self.assertEqual(manager.tick(150)["mouth"], "frown")


if __name__ == "__main__":
    unittest.main()
