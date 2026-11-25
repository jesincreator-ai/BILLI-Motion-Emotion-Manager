# M6 integration contract

M6 is a face-only subsystem. It does not access servo PWM and cannot bypass M8.

- Create one `MotionEmotionManager()` at startup.
- Call `tick(now_ms)` from the main cooperative loop. Use the same monotonic millisecond clock as M7/M8.
- Call `set_emotion(name, intensity, now_ms)` for emotion state.
- Call `begin_speech(now_ms)`, `update_speech_level(now_ms, normalized_level)` and `end_speech()` from the local voice/audio pipeline. Do not pass raw audio buffers into M6.
- Drain events using `next_event()`; the queue is bounded and drops oldest events on overflow.
- M6 may render face frames to a display adapter, but the robot motion request path must still pass through M7 and M8.

Supported language codes are `en`, `ta`, and `si`. Text shaping/rendering depends on the display font and controller; the included face renderer draws shapes only.
