"""Run on a desktop Python interpreter to inspect the animation state stream."""
import time
from billi_motion.manager import MotionEmotionManager

manager = MotionEmotionManager()
manager.set_emotion("happy", 0.9, 0)
manager.begin_speech(0)
for tick in range(10):
    now = tick * 100
    manager.update_speech_level(now, 0.8 if tick % 2 else 0.05)
    print(manager.tick(now))
    time.sleep(0.02)
manager.end_speech()
