"""MicroPython entry point. Wire an initialized display driver before enabling rendering."""
import time
from billi_motion.manager import MotionEmotionManager


def run(display_adapter=None):
    manager = MotionEmotionManager()
    manager.set_emotion("neutral", 0.5, 0)
    while True:
        now = time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)
        frame = manager.tick(now)
        if display_adapter is not None:
            display_adapter.draw(frame)
        time.sleep_ms(20) if hasattr(time, "sleep_ms") else time.sleep(0.02)


if __name__ == "__main__":
    run()
