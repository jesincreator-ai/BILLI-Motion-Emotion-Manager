"""BILLI R-20 M6 MicroPython firmware entry point.

Copy this file to the ESP32 as main.py together with the billi_motion/
package and the hardware driver files. This file is intentionally kept
outside the repository root so Vercel treats the repository as a static site.
"""
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
        if hasattr(time, "sleep_ms"):
            time.sleep_ms(20)
        else:
            time.sleep(0.02)


if __name__ == "__main__":
    run()
