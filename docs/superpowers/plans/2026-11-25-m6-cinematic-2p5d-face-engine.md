# M6 Cinematic 2.5D Face Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace M6's primitive facial renderer with a cinematic, offline 2.5D face engine that is expressive on the ESP32-WROOM-32 and visually richer in a desktop/mobile browser preview.

**Architecture:** Keep a shared MicroPython-friendly emotion/animation state model. Render that state through a no-framebuffer ST7789 primitive renderer on-device and a higher-quality Canvas 2D renderer in the browser. Use bounded geometry, fixed palettes, eased transitions and mode-specific effects.

**Tech Stack:** MicroPython-compatible Python standard library; ST7789 display operations already used by this repo; vanilla HTML/CSS/JavaScript Canvas 2D; Python unittest; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-25-m6-2p5d-face-engine-design.md`

## Global Constraints

- Target: ESP32-WROOM-32 without PSRAM; 240x240 ST7789 SPI; RGB565.
- No full-screen RGB565 framebuffer (115,200 bytes), no mesh renderer, no GPU shader dependency and no network access at runtime.
- Standard mode supports `happy`, `sad`, `surprise`, `disappointment`, `sorry`, `crying`; rugged mode supports `angry`, `ego_fire`; `neutral` is an idle/fallback pose in either mode.
- Preserve `standard` and `rugged` mode names and the existing manager/render entry points where practical.
- Preserve the known display operations: `fill`, `rect`, `fill_rect`, `line`, `show`.
- M6 is face/emotion-only; M7 owns servos and M8 remains the safety authority; M5 owns voice/TTS.
- Do not publish an ESP32 frame-rate claim until measured on the actual WROOM-32/ST7789 hardware.

## Review Focus

- Unknown mode or emotion values must be rejected without mutating current state.
- Switching modes while an incompatible expression is active must return to neutral safely.
- Large or wrap-adjacent tick values must not create unbounded loops or negative effect values.
- Narrow, non-square display dimensions must clip renderer writes to the display bounds.
- Browser mode/emotion changes during an active transition must not leave stale timers or invalid emotion options.

---

### Task 1: Lock the emotion-mode contract with tests

**Files:**
- Create: `tests/test_cinematic_face.py`
- Modify: `tests/test_motion.py`

**Interfaces:**
- Consumes: current `EmotionEngine`, `MotionEmotionManager.set_mode()`, `set_emotion()`.
- Produces: canonical emotion names, mode-aware validation, neutral fallback on mode changes.

- [x] Add tests for all eight named emotions and the neutral idle pose.
- [x] Test that each Calm expression is rejected in rugged mode and rugged expressions are rejected in standard mode.
- [x] Test `surprised` as a compatibility alias for canonical `surprise`.
- [x] Test that unknown inputs leave the existing state unchanged.
- [x] Run `python -m unittest discover -s tests -v`; expected: new contract tests fail for the missing mode enforcement/canonicalization.
- [x] Commit the failing contract tests.

### Task 2: Implement bounded animation and the embedded renderer

**Files:**
- Modify: `billi_motion/emotion.py`
- Modify: `billi_motion/animation.py`
- Modify: `billi_motion/manager.py`
- Modify: `billi_motion/renderer.py`
- Modify: `tests/test_cinematic_face.py`

**Interfaces:**
- Produces: `MotionEmotionManager.set_emotion(name, intensity=1.0, now_ms=0) -> bool`; `set_mode(mode, now_ms=0) -> bool`; `tick(now_ms) -> dict`.
- Produces: bounded frame fields `eye_open`, `eye_tilt`, `brow_tilt`, `transition`, `blink`, `glow`, `tear`, `fire`, `gaze_x`, `gaze_y`, `mouth`.
- Produces: a display renderer using only the existing five display operations and no full-screen framebuffer.

- [x] Add renderer fake-display tests before production changes: supported API only, clipped writes, RGB565 bounds and no framebuffer allocation.
- [x] Run the focused renderer tests; expected: fail because the current renderer ignores the new face geometry/effect fields.
- [x] Implement emotion constants and alias normalization; enforce mode-specific emotion validation in the manager.
- [x] Implement eased expression interpolation, timed blinks and bounded idle/effect phases without blocking loops.
- [x] Implement layered RGB565 eye shells, stepped radial glow, highlights, brows, mouth, tears and ember-style rugged accents using clipped spans/primitives.
- [x] Run focused and full Python unittest suites; expected: all existing and new tests pass.
- [x] Commit the embedded engine and tests.

### Task 3: Replace the browser preview with an offline cinematic Canvas renderer

**Files:**
- Modify: `index.html`
- Create: `scripts/check_preview.py`
- Create: `tests/test_preview.py`

**Interfaces:**
- Produces: responsive single-file browser preview; no external imports or requests.
- UI: Calm/Standard and Rugged modes, mode-filtered emotions, intensity, auto-idle, blink, and reset controls.
- Renderer: Canvas 2D layered eye geometry, gradient depth, highlights/reflections, bloom, tear droplets, ember accents and eased transitions.

- [x] Add static preview-contract tests first: Canvas presence, all eight emotion IDs, local-only assets, responsive layout and required controls.
- [x] Run preview-contract tests; expected: fail because the current page contains only a small SVG face and no mode-filtered emotion controls.
- [x] Implement the browser Canvas renderer and controls with vanilla JavaScript only.
- [x] Add a preview checker that extracts inline JavaScript and validates it with Node `--check`.
- [x] Run Python preview tests and Node syntax validation; expected: no external network references and valid inline JavaScript.
- [x] Commit the browser preview and checks.

### Task 4: Wire continuous verification and update deployment/integration docs

**Files:**
- Modify: `.github/workflows/tests.yml`
- Modify: `README.md`
- Modify: `docs/INTEGRATION_CONTRACT.md`
- Modify: `config.py` only if the public constants need updating.

- [x] Add Node syntax validation to the existing CI workflow without adding runtime dependencies.
- [x] Document local preview, emotion/mode matrix, firmware copying, memory boundaries and the hardware-only verification boundary.
- [x] Confirm Vercel remains a static HTML deployment with no build tool or remote assets.
- [x] Run all Python tests plus the preview checker on the remote GitHub Actions workflow; expected: all Python matrix jobs and browser syntax checks succeed.
- [x] Commit CI and documentation changes.

### Task 5: Final review and handoff

**Files:**
- Review all changed files on this branch.

- [x] Compare each acceptance criterion in the spec against code and test evidence.
- [x] Review for display API drift, allocations in hot loops, out-of-bounds drawing, stale browser controls and M6/M7/M8 ownership violations.
- [x] Inspect the final GitHub Actions run logs and repository diff.
- [x] Open a draft pull request against `main`; do not merge automatically.
- [x] Report desktop/mobile test evidence separately from unperformed physical ESP32 measurements.

---

## Verification commands

```bash
python -m unittest discover -s tests -v
python scripts/check_preview.py
```

The actual device acceptance run remains a required owner-side check: flash the MicroPython package to the WROOM-32, connect the existing ST7789 module, exercise all valid expressions in both modes, and record actual frame rate and free heap. Do not infer this from host CI.


## Execution notes

- The TDD red/green cycle was recorded in GitHub Actions. Contract, renderer-transaction and localization tests each failed before the corresponding implementation/fix and passed after it.
- The final checked CI run validates Python 3.10, 3.11 and 3.12 and parses the single-file browser preview with Node.js 22.
- The local browser interaction/visual inspection and hosted Vercel preview were not run in this environment.
- The actual WROOM-32/ST7789 device check remains an owner-side acceptance step: flash the feature branch and measure FPS, free heap, SPI colour order and display rotation.


### Task 6: Adapt the glossy-eye reference to BILLI's WROOM renderer

**Files:**
- Modify: `billi_motion/renderer.py`
- Modify: `index.html`
- Modify: `README.md`
- Create: `docs/REFERENCE_GLOSSY_EYE_ADAPTATION.md`
- Modify: `tests/test_cinematic_face.py`
- Modify: `tests/test_preview.py`

**Interfaces:**
- Preserve `FaceRenderer.render(frame)` and the five-operation ST7789 display contract.
- Keep Calm pearl-white and Rugged crimson palettes consistent between firmware and browser preview.
- Do not add a framebuffer, PSRAM dependency, Arduino/LovyanGFX dependency or external runtime asset.

- [x] Add tests for pearl lens colour, crimson lens colour, specular reflections and curved lid masks.
- [x] Observe the new renderer tests fail on the old renderer (missing crimson lens and eyelid-mask spans).
- [x] Add matching browser palette contract tests.
- [x] Port two bounded catchlights and quantized curved lid occlusion using clipped RGB565 spans.
- [x] Update offline preview colours to pearl white (Calm) and crimson red (Rugged).
- [x] Document reference attribution and why its ESP32-S3/Arduino/LovyanGFX firmware is not installed as-is on WROOM-32 MicroPython.
- [x] Run the complete Python suite on Python 3.10, 3.11 and 3.12 and validate the offline browser preview on the final implementation branch; all three matrix jobs pass.
- [x] Inspect the PR diff and latest CI run; physical WROOM-32/ST7789 display calibration, frame rate and free-heap measurements remain unverified.
