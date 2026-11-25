# Glossy Eye Reference Adaptation

## Reference

The visual reference is [ESP32 Robot Eyes](https://github.com/ElroyChenWI/esp32-robot-eyes) by Elroy Chen. The upstream repository declares the MIT License; see its [LICENSE](https://github.com/ElroyChenWI/esp32-robot-eyes/blob/main/LICENSE).

## What BILLI adapts

M6 adopts the reference's glossy-eye design language: a bright outer rim, a recessed dark socket, a shaded eye lens, separate iris and pupil depth, multiple specular catchlights, and curved eyelid occlusion. The embedded renderer approximates the eyelid curve with a small fixed number of clipped vertical spans, reducing SPI transactions and keeping the frame path bounded.

BILLI's two mode palettes are deliberately fixed:
- **Calm:** pearl-white lens, cool graphite-blue shadows, subtle icy reflections.
- **Rugged:** saturated crimson lens, deep red shadows, warm red glow and white specular reflections.

The offline Canvas preview uses the same colour intent and glossy layers.

## Why the upstream firmware is not copied into the device image

The reference project targets an ESP32-S3, a 240x320 ST7789 display and an Arduino/C++ stack using LovyanGFX and an off-screen sprite. BILLI's target is an ESP32-WROOM-32 without PSRAM, a 240x240 ST7789 and MicroPython. Installing the upstream firmware/library directly would introduce an incompatible board/toolchain/display contract.

Therefore this is a hardware-specific port of the visual approach, not a binary or library installation. BILLI keeps its MicroPython display interface and draws directly through the existing `fill`, `rect`, `fill_rect`, `line` and `show` operations. It does not allocate a 240x240 RGB565 framebuffer or introduce an online asset dependency.

## Verification boundary

Host tests verify palette colours, specular highlights, curved lid spans, display clipping, transaction bounds and the absence of a framebuffer. They do not establish real WROOM-32 frame rate, heap usage, panel colour order or rotation; those remain physical-device checks.
