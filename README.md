# BILLI Motion & Emotion Manager (M6)

Offline facial-expression and animation manager for BILLI R-20. The core runs with MicroPython on ESP32-WROOM and with CPython for desktop tests. It has no network, cloud, LLM, or third-party runtime dependency.

## Features

- Seven deterministic expressions: neutral, happy, sad, angry, curious, surprised and sleepy.
- Timed blinking, bounded pupil movement and small face-frame dictionaries.
- Speech mouth synchronization from a local normalized audio-amplitude value.
- Fixed-capacity event queue; overflow discards the oldest event instead of growing RAM use.
- English, Tamil and Sinhala phrase table (`billi_motion.locales`). Tamil/Sinhala text requires a display font with those glyphs; the primitive face renderer itself draws shapes.
- Optional SSD1306-like display adapter; the display driver is supplied by the hardware project, not downloaded at runtime.

## Quick start (desktop)

```bash
python -m unittest discover -s tests -v
python examples/desktop_demo.py
```

## ESP32 setup

Copy `billi_motion/`, `hardware/`, `config.py`, and `main.py` to the board. Install a display driver compatible with your actual panel, initialize it in your board startup code, then pass `ESP32FaceDisplay(display)` to `run()`. The display adapter expects `fill`, `rect`, `fill_rect`, `line`, and `show` methods. Do not assume the panel is 128x64 until verified.

The default loop is 20 ms (50 Hz). Keep rendering and sensor/audio sampling cooperative; do not block the loop with network access or long sleeps. The face manager is not a motor safety controller: M8 Guardian must remain the movement safety authority.

## Core API

```python
manager = MotionEmotionManager()
manager.set_emotion("happy", 0.8, now_ms)
manager.begin_speech(now_ms)
manager.update_speech_level(now_ms, 0.55)  # normalized 0.0..1.0
frame = manager.tick(now_ms)
```

## Resource notes

This package uses plain classes, tuples/dicts, and bounded lists. It avoids `dataclasses`, `asyncio`, NumPy, model runtimes, and network libraries for MicroPython compatibility. Keep event payloads small and do not store audio samples in this manager.

## License

MIT. See `LICENSE`.
