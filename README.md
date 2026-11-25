# BILLI Motion & Emotion Manager (M6)

Offline facial-expression, animation and display-theme manager for BILLI R-20. The manager core is MicroPython-friendly and desktop-testable.

## Browser test / Vercel deployment

The repository root contains a static `index.html` browser demo. Import this repository into Vercel and deploy it as a static site (Framework Preset: **Other**; leave Build Command and Output Directory empty). The demo lets you switch between standard white and rugged red face themes, select expressions, blink, and preview browser speech.

The browser demo is a simulation. It does not connect to an ESP32 or drive physical hardware.

## Display target

The current hardware target is the **1.3-inch square 240x240 ST7789 SPI TFT**. The renderer uses RGB565 colours and a black background:
- **standard mode:** white face graphics
- **rugged mode:** red face graphics

The display body/cardboard paint colour is independent of this setting. No external LED lighting is required.

The visible 1.3-inch square panel is approximately 33 mm on each side if the panel specification means 1.3-inch square active area; confirm the exact module PCB and active-area dimensions before cutting the bezel. The renderer canvas is 240x240 pixels.

## Modes

```python
manager = MotionEmotionManager()
manager.set_mode("standard", now_ms)  # white graphics
manager.set_mode("rugged", now_ms)    # red graphics
frame = manager.tick(now_ms)
display.draw(frame)
```

M1 should send the same mode to M6 and Voice Lite. M6 owns face graphics only; it must not command servos. M8 remains the safety authority.

## Features

- Seven deterministic expressions: neutral, happy, sad, angry, curious, surprised and sleepy.
- Timed blinking, bounded pupil movement and speech mouth synchronization.
- Fixed-capacity event queue.
- Cooperative rendering loop; do not block it with audio, storage or network operations.
- Display driver is supplied by the hardware project; no runtime download.

## ESP32 setup

The MicroPython entry point is stored at `firmware/main.py` so Vercel does not mistake it for a Python web-function entry point. When flashing the robot, copy it to the ESP32 as `main.py` together with the `billi_motion/` package and hardware driver files.

Initialize a MicroPython ST7789 driver for 240x240 RGB565 and pass the display object to `ESP32FaceDisplay(display, 240, 240)`. The driver must expose `fill`, `rect`, `fill_rect`, `line`, and `show`. Confirm the driver colour order and rotation on the actual module.

## License

MIT. See `LICENSE`.
