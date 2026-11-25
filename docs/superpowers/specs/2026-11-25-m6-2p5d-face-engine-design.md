# M6 2.5D Face Engine — Design Specification

**Date:** 2026-11-25  
**Repository:** `jesincreator-ai/BILLI-Motion-Emotion-Manager`  
**Status:** Proposed — awaiting owner approval  
**Target hardware:** ESP32-WROOM-32, no PSRAM, ST7789 240×240 SPI display, RGB565

## 1. Intent

Replace M6's basic rectangular-eye/SVG-expression implementation with an offline face engine that looks dimensional and emotionally readable. The same face model and emotion vocabulary must drive a polished desktop/mobile preview and a lightweight embedded renderer. M6 owns face visuals and emotion animation only; it must not control servos or duplicate M7's motion ownership.

The visual direction is premium stylized robotics: sculpted eye silhouettes, layered depth, deliberate highlights and reflections, soft light spill, controlled bloom, subtle shadows, rich but coherent color grading, and expressive motion. The design must remain practical on the ESP32-WROOM-32 without PSRAM or added hardware.

## 2. Goals

- Deliver two visual modes:
  - **Calm / Standard:** cool white and pearl highlights with restrained cyan-blue shadow tones; expressions are `happy`, `sad`, `surprise`, `disappointment`, `sorry`, and `crying`.
  - **Rugged:** deep red, ember and dark graphite palette; expressions are `angry` and `ego_fire`.
- Preserve a neutral safe/idle pose as the startup and fallback state; it is not an additional named emotion in either mode.
- Make expressions recognizable through eye shape, eyelid angle, brow position, gaze, mouth geometry, timing and secondary effects—not color alone.
- Add smooth transitions, easing, anticipation, overshoot, blink timing, idle breathing, subtle gaze drift and emotion-specific motion.
- Provide software-rendered shader-style lighting: layered glow, edge/rim light, radial falloff, specular highlights, soft shadow, reflection and mode-specific effects.
- Run fully offline on the device and in the browser preview; no CDN, cloud rendering, paid assets, external GPU, PSRAM or additional hardware.
- Keep the existing M6 public integration surface and display-driver adapter compatible where practical.
- Keep M6 isolated from M7 servo control and M8 safety/guardian authority.

## 3. Non-goals and honest rendering boundary

- The ESP32 target will **not** run a full mesh-based 3D engine, real-time physically based rendering, or programmable GPU fragment shaders. It has no dedicated graphics GPU or PSRAM in this configuration.
- “3D” on the embedded device means carefully composed **2.5D procedural graphics**: depth layers, shape masks, lighting ramps, highlight geometry, occlusion and parallax-like motion. Shader effects are CPU/raster approximations with fixed-size lookup tables and primitives.
- The browser preview may use higher-quality Canvas 2D gradients and compositing, but it must not require WebGL or an internet connection. It should demonstrate the same animation states and emotion design, not pretend the ESP32 renders at desktop quality.
- No new servo, sensor, display, audio or power hardware is introduced. Voice/TTS remains M5's responsibility.

## 4. Approaches considered

1. **Layered 2.5D software renderer (selected):** Shared expression/animation model with a high-quality browser Canvas renderer and an optimized ESP32 raster/primitive renderer. It provides the best visual-to-memory trade-off and preserves offline use.
2. **Full desktop 3D / WebGL:** Could produce more realistic desktop visuals, but would create a large mismatch with the embedded renderer and introduce a separate graphics stack. Rejected for this hardware-first M6 rebuild.
3. **Pre-baked sprite/pixel-art engine:** Fast and predictable, but limits organic eye geometry, dynamic lighting and emotion-specific deformation. Selected only as an optional optimization technique for fixed glow masks or tiny lookup assets, not as the main design.

## 5. Proposed architecture

### 5.1 Shared face and animation model

Create a backend-neutral model containing mode, emotion, normalized time, gaze, blink phase, eye aperture, eye tilt, brow pose, mouth pose, glow intensity, effect phase and transition progress. Expression presets define these parameters and transition rules. Both renderers consume the same model so expression semantics and timing remain consistent.

The animation manager remains cooperative and non-blocking: callers advance it with elapsed time and render only when a frame is due. Use bounded easing curves and fixed-size lookup tables where they reduce embedded CPU cost. Avoid dynamic allocation inside the per-frame path.

### 5.2 Browser renderer

Replace the current minimal SVG demo with an offline HTML Canvas preview. Draw layered eye shells, inner eye surfaces, pupils/iris details, eyelids, brows and mouth as clean vector/raster geometry. Use Canvas gradients, clipped highlights, shadow layers and additive-like glow compositing to create a refined 2.5D result. Add controls to switch Calm/Rugged, select each valid emotion, trigger blink/idle and inspect transitions. Make the layout responsive for desktop and mobile.

The page must load locally with no build step and no network requests. Browser quality can exceed the embedded result, but use the same expression presets, palette intent and motion timeline.

### 5.3 ESP32 renderer

Keep the 240×240 ST7789 RGB565 target and existing display adapter contract. Build effects from bounded primitives and small lookup tables: shape outlines/fills, clipped regions, horizontal bands, ellipse/circle approximations, highlight streaks, stepped radial glow and layered shadow/rim passes. Convert colors to RGB565 once per palette/frame where practical.

Do not allocate a 240×240 RGB565 framebuffer (115,200 bytes) or large intermediate canvases. Prefer direct display writes / small bounded spans and reuse preallocated scratch data only when required by the actual driver. If the current adapter lacks an operation, implement it using the adapter's supported low-level calls without assuming an unverified API. Keep the renderer cooperative; it must not block integration, voice, or guardian tasks.

Provide quality tiers so the renderer can lower glow samples, shadow passes or secondary particles when frame time rises. The face and expression must remain legible in the lowest tier.

### 5.4 Lighting and visual effects

- **Eye depth:** outer shell/rim, recessed dark socket, lit eye surface, pupil/iris detail, controlled specular highlight and eyelid occlusion.
- **Glow:** several low-cost intensity rings/bands with distance falloff; avoid a single flat outline. Browser uses smooth gradients; ESP32 uses quantized RGB565 steps.
- **Lighting:** key-light highlight, opposite-side cool/warm fill, rim light and restrained contact shadow. Lighting direction must remain consistent across both eyes and the mouth.
- **Color grading:** Calm uses pearly white with cool shadow and a restrained cyan accent; Rugged uses red/ember highlights against deep charcoal. Preserve contrast and avoid clipping whites/reds.
- **Emotion effects:** crying uses animated tear tracks/droplets and subtle tremble; surprise uses fast eye opening and a brief glow lift; sorry uses softened, lowered lids; disappointment uses gaze drop and reduced eye aperture; angry uses angled compressed eyes and sharp red pulse; ego_fire uses layered ember/flame-like energy accents and a high-intensity but bounded glow.
- **Motion:** easing, short anticipation and overshoot where appropriate, natural asymmetric blinks, idle breathing and low-amplitude gaze drift. Avoid abrupt jumps and avoid continuous expensive particle simulation on the ESP32.

“Correct glow” means visible falloff around the eye geometry, edge separation from the dark face, and controlled light intensity—not simply changing an outline to white or red.

## 6. Hardware, memory and performance constraints

- Target is ESP32-WROOM-32 without PSRAM; display remains 240×240 ST7789 SPI, RGB565.
- No full-screen framebuffer, no large temporary textures, no runtime 3D meshes, no network dependency, and no graphics dependency that requires unavailable native modules.
- Keep per-frame memory bounded and stable; preallocate small fixed tables/scratch buffers at startup and avoid per-frame list/dict/string creation.
- Measure elapsed render time and expose frame-time / quality-tier diagnostics in the browser test harness and device debug output where safe.
- Use adaptive quality and frame skipping rather than allowing long render bursts to stall the main cooperative loop.
- Treat a target near 15 fps as an initial engineering objective, **not a guaranteed result**. Actual speed depends on SPI clock, display driver implementation, MicroPython build and enabled effects; record measured results on real hardware before publishing any performance claim.
- If the full effect stack cannot maintain a stable frame budget, keep eye geometry, emotion readability and core lighting first; reduce particles, shadow resolution and glow samples before reducing expression quality.

## 7. Compatibility and integration

- Preserve M6's public `set_mode`, `set_emotion`, `tick/update` and render integration behavior where those interfaces exist; inspect exact current signatures before implementation.
- Validate mode/emotion pairs. Calm accepts the six Calm expressions; Rugged accepts `angry` and `ego_fire`. Unsupported pairs must fail safely to neutral or return a clear validation result without crashing the firmware.
- Preserve the display adapter's known operations (`fill`, `rect`, `fill_rect`, `line`, `show`) unless repository inspection proves a different concrete contract.
- M6 emits visual state only. It must not command servos, own audio playback, or bypass M8 safety state.
- Keep firmware imports compatible with the project's MicroPython environment; browser-only code stays isolated from firmware imports.

## 8. Verification and acceptance criteria

1. **Emotion contract:** automated tests prove all eight named expressions are available only in their intended mode; unsupported combinations safely fall back or report validation failure.
2. **Animation:** tests cover time-step progression, transition completion, blink state, idle behavior, non-negative/ bounded effect values, and large elapsed-time inputs without runaway loops.
3. **Renderer contract:** fake-display tests verify only supported display calls are used, RGB565 output stays within 16-bit range, drawing is clipped to 240×240, and no full-screen framebuffer is created.
4. **Browser preview:** local desktop and mobile viewport checks verify both modes and all eight expressions, visible glow/depth layers, working controls, and no external network requests or console errors.
5. **Firmware compatibility:** import and smoke tests run with a MicroPython-compatible test shim; no CPython-only or browser-only imports leak into firmware modules.
6. **Performance:** host timing tests catch pathological loops, while real-device profiling records measured frame rate and memory/heap behavior. Hardware claims remain unverified until tested on the actual WROOM-32/ST7789 device.
7. **Deployment:** static preview opens directly and the repository's existing deployment path is tested. Do not mark hardware deployment complete without a real-device test.

## 9. Decisions left to the implementer

- Exact module/file split and helper names, based on the existing repository structure.
- Precise eye geometry and visual tuning, while preserving the palette and expression semantics above.
- Which tiny fixed lookup tables or pre-baked masks offer the best speed/memory trade-off after profiling.
- Whether the adapter can support efficient span writes; this must be established from its actual implementation, not assumed.
- Exact adaptive-quality thresholds, calibrated from measurements rather than guessed.

## 10. Builder review — self-check

No independent subagent reviewer is available in this session, so this design was reviewed against the current M6 interfaces and constraints.

- **Potential ambiguity resolved:** “3D shader effects” on the ESP32 means software-generated 2.5D lighting and glow, not GPU shaders or mesh rendering.
- **Potential mismatch resolved:** Browser visuals may be smoother, but share the same emotion model and timeline; hardware remains the source of truth for performance claims.
- **Memory risk addressed:** No full-framebuffer design; bounded primitives and small reusable tables only.
- **Integration risk addressed:** M6 remains graphics/emotion-only and keeps M7/M8 ownership boundaries intact.
- **Open material dependency:** The exact low-level ST7789 write path and achievable frame rate must be confirmed from the checked-in driver and on the actual board before performance targets are finalized.
