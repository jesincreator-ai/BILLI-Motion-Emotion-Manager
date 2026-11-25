# BILLI Motion & Emotion Manager (M6)

M6 is the offline face graphics and emotion subsystem for BILLI R-20. It provides one shared, MicroPython-friendly emotion/animation model, a direct-to-ST7789 renderer for the ESP32-WROOM-32, and a richer desktop/mobile browser preview.

## Visual engine

The face uses a stylized **2.5D** treatment: layered eye shells, recessed sockets, iris/pupil details, highlights, shadows, stepped light falloff, color grading and emotion-specific secondary effects. The browser preview uses Canvas 2D gradients and compositing. The ESP32 renderer uses quantized RGB565 bands and the existing ST7789 driver operations. It measures each completed draw and adapts among three glow-detail tiers for the next frame.

The ESP32-WROOM-32 does not have a programmable graphics GPU or PSRAM in this configuration. M6 therefore does **not** use full 3D meshes, PBR or GPU fragment shaders on the device. It draws a low-memory 2.5D approximation directly to the display and does not allocate a 240x240 RGB565 framebuffer (115,200 bytes). Browser effects are a higher-quality preview, not evidence of embedded frame rate.

### Glossy eye reference

The eye treatment takes visual cues from [ESP32 Robot Eyes by Elroy Chen](https://github.com/ElroyChenWI/esp32-robot-eyes): layered glossy lens surfaces, recessed sockets, iris/pupil depth, bright catchlights and curved eyelid masks. BILLI's port is implemented for its own hardware rather than installing the reference firmware unchanged; see [the adaptation notes](docs/REFERENCE_GLOSSY_EYE_ADAPTATION.md).

## Face profiles and emotion set

| Profile | Display palette | Supported expressions |
|---|---|---|
| Calm / Standard | White, pearl and cool cyan shadow accents | `happy`, `sad`, `surprise`, `disappointment`, `sorry`, `crying` |
| Rugged | Deep red, ember and dark graphite | `angry`, `ego_fire` |
| Shared idle/fallback | Dim neutral lighting | `neutral` |

`surprised` remains accepted as a compatibility alias for `surprise`. The manager rejects expressions that do not belong to the active profile. Switching profiles resets an incompatible active expression to `neutral`.

## Browser preview

Open `index.html` directly on a desktop or mobile browser; it has no CDN, remote font, build step or runtime network dependency. Controls include profile selection, mode-specific emotion selection, expression intensity, idle breathing/gaze, blink and reset. The page is a visual simulator; it does not connect to physical hardware.

Vercel deployment remains static: import the repository, select Framework Preset **Other**, and leave Build Command and Output Directory empty. The repository's `vercel.json` serves the root `index.html`.

## Python usage

```python
from billi_motion.manager import MotionEmotionManager

manager = MotionEmotionManager()
manager.set_mode("standard", now_ms=0)
manager.set_emotion("happy", 0.85, now_ms=0)

frame = manager.tick(20)
# Send frame to the M6 display adapter from the cooperative loop.
```

The public mode names remain `standard` and `rugged`; `calm` is an alias for `standard`. Use a monotonic millisecond clock shared with the rest of the robot. M6's `tick()` is designed to be called repeatedly from a cooperative loop; do not block it with audio, storage or network operations.

## ESP32 setup

The MicroPython entry point is `firmware/main.py`. Copy it to the ESP32 as `main.py`, together with the `billi_motion/` package and `hardware/` adapter, plus the ST7789 driver used by the hardware project.

Initialize the actual 240x240 ST7789 SPI display in RGB565 mode and pass its driver object to:

```python
from hardware.esp32_display import ESP32FaceDisplay

face_display = ESP32FaceDisplay(display, 240, 240)
face_display.draw(manager.tick(now_ms))
```

The driver must expose `fill`, `rect`, `fill_rect`, `line` and `show`. Confirm colour order, rotation, SPI frequency and the concrete driver's argument semantics on the actual module. Do not add a framebuffer or use a driver that silently allocates a full-screen image.

**Hardware status:** host tests and static checks verify the renderer's driver-call contract, RGB565 bounds, display clipping and a bounded number of drawing transactions. They do not prove the actual WROOM-32 frame rate, free heap or screen appearance. Those must be measured on the robot before publishing a performance claim; approximately 15 fps remains an initial engineering objective, not a guarantee.

## Verification

Run the repository checks with:

```bash
python -m unittest discover -s tests -v
python scripts/check_preview.py
```

GitHub Actions runs the Python suite on Python 3.10, 3.11 and 3.12 and validates the inline browser JavaScript with Node.js. The firmware modules use MicroPython-compatible standard-library features only.

## System ownership

- **M6:** face geometry, expression state and display rendering only.
- **M5:** voice and TTS; M6 only receives normalized speech level samples for mouth synchronization.
- **M7:** sole servo and robot-motion owner.
- **M8:** safety/guardian veto authority. M6 must not bypass it.

## License

MIT. See `LICENSE`.
