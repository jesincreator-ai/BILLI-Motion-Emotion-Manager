# Glossy Eye Reference Adaptation

## Reference

The visual reference is [ESP32 Robot Eyes](https://github.com/ElroyChenWI/esp32-robot-eyes) by Elroy Chen. The upstream repository declares the MIT License; see its [LICENSE](https://github.com/ElroyChenWI/esp32-robot-eyes/blob/main/LICENSE).

## What BILLI adapts

M6 ports the reference's two selectable drawing styles and six mood geometries:

- **Flat:** a tall filled oval and a small dark vertical pupil
- **Glossy:** a rounded-rectangle eye shell and inner lens, recessed pupil, two white catchlights and upper/lower eyelid masks
- **Moods:** neutral, happy, sad, angry, sleepy and surprised

The lid presets preserve the reference parameters for top closure, happy lower-lid arc, sad/angry slope, eye scale and pupil scale. Blinks use a close/hold/open envelope (70/20/100 ms). Idle gaze changes are scheduled without blocking the M6 cooperative loop. On WROOM-32, curved lids and rounded rectangles are approximated by a fixed number of clipped RGB565 spans to bound SPI transactions and avoid an off-screen framebuffer.

BILLI's two colour profiles are deliberately fixed in both eye styles:
- **Calm:** pearl-white eye surface and cool blue-grey shadows.
- **Rugged:** saturated crimson eye surface and deep red shadows.

The six reference moods are shared by Calm and Rugged. BILLI's additional `disappointment`, `sorry` and `crying` poses remain Calm-only, while `ego_fire` remains Rugged-only. Glossy is the default style; Flat remains selectable.

The offline Canvas preview uses the same colour intent and glossy layers.

## Why the upstream firmware is not copied into the device image

The reference project targets an ESP32-S3, a 240x320 ST7789 display and an Arduino/C++ stack using LovyanGFX and an off-screen sprite. BILLI's target is an ESP32-WROOM-32 without PSRAM, a 240x240 ST7789 and MicroPython. Installing the upstream firmware/library directly would introduce an incompatible board/toolchain/display contract.

Therefore this is a hardware-specific port of the drawing and animation approach, not a binary installation or direct reuse of the upstream Arduino library. The adapted logic is accompanied by the upstream MIT copyright and permission notice in `third_party/ESP32-Robot-Eyes-MIT.txt`. BILLI keeps its MicroPython display interface and draws directly through the existing `fill`, `rect`, `fill_rect`, `line` and `show` operations. It does not allocate a 240x240 RGB565 framebuffer or introduce an online asset dependency.

## Verification boundary

Host tests verify palette colours, specular highlights, curved lid spans, display clipping, transaction bounds and the absence of a framebuffer. They do not establish real WROOM-32 frame rate, heap usage, panel colour order or rotation; those remain physical-device checks.
