# M6 integration contract

M6 is a face-only subsystem. It does not access servo PWM and cannot bypass M8.

## Public interface

- Create one `MotionEmotionManager()` at startup.
- Call `tick(now_ms)` from the main cooperative loop using a monotonic millisecond clock shared with M7/M8.
- Call `set_mode(mode, now_ms)`; accepted modes are `standard` (white) and `rugged` (red). `calm` is an alias for `standard`.
- Call `set_emotion(name, intensity, now_ms)`; intensity is clamped to 0.0–1.0.
- Call `begin_speech(now_ms)`, `update_speech_level(now_ms, normalized_level)` and `end_speech()` from the local voice/audio pipeline. The level must be normalized 0.0–1.0 amplitude/RMS, sampled at a cooperative cadence; M6 smooths it and maps it to a talking-mouth opening. Do not pass raw audio buffers into M6.\n- Speech mouth is an overlay (`mouth="talk"`, `mouth_open` 0.0–1.0). The selected emotion remains active underneath; after `end_speech()`, the mouth returns to that emotion's resting shape.
- Call `look(x, y)` with bounded gaze offsets when the integration layer has a gaze target.
- Drain events using `next_event()`; the fixed-capacity queue drops the oldest event on overflow.

## Mode/emotion contract

| Mode | Accepted named expressions |
|---|---|
| `standard` / `calm` | `happy`, `sad`, `surprise`, `disappointment`, `sorry`, `crying` |
| `rugged` | `angry`, `ego_fire` |
| Both | `neutral` idle/fallback pose |

The legacy spelling `surprised` is canonicalized to `surprise`. Invalid names and cross-mode emotion requests return `False` without changing the current state. Switching profiles while a now-invalid expression is active resets that expression to `neutral`.

## Rendering and hardware

- `tick(now_ms)` returns the current face pose/effect state; the display adapter consumes it.
- Use `ESP32FaceDisplay(display, 240, 240)` for the checked-in ST7789 adapter.
- The display driver's known required methods are `fill`, `rect`, `fill_rect`, `line` and `show`; verify the concrete driver and its RGB565 colour order on the selected module.
- The ESP32 renderer is a no-full-framebuffer 2.5D raster approximation; the Canvas 2D desktop/mobile preview intentionally provides smoother gradients and more elaborate compositing.
- Host fake-display tests cover supported operations, clipping, 16-bit colors, bounded transaction count, and adaptive quality diagnostics. The renderer exposes `render_time_ms` and `quality_tier` for device-side profiling; detail is reduced when a draw exceeds about 67 ms and restored gradually when comfortably under 30 ms. Physical display timing, free-heap impact and the final visual appearance still require measurements on the actual WROOM-32/ST7789 hardware.

## Ownership boundaries

- M6 may render face frames but must not issue servo commands.
- M5 owns voice and TTS; M6 consumes only normalized speech amplitude.
- The robot motion request path must still pass through M7 and M8.
- Supported language codes remain `en`, `ta` and `si`; text shaping/rendering depends on the display font and controller. The face renderer draws shapes only.
