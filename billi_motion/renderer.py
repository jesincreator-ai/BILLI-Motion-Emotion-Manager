"""Low-memory 2.5D face renderer for a 240x240 RGB565 ST7789 display.

The renderer draws directly through the existing display adapter. It never
allocates a full-screen framebuffer and only calls fill, rect, fill_rect,
line and show, so the embedded path remains MicroPython-friendly.
"""
from math import sqrt
import time

from .timebase import diff_ms

BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800


def rgb565(red, green, blue):
    """Pack 8-bit RGB components into one 16-bit RGB565 colour."""
    red = max(0, min(255, int(red)))
    green = max(0, min(255, int(green)))
    blue = max(0, min(255, int(blue)))
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


class FaceRenderer:
    def __init__(self, display, width=240, height=240):
        self.display = display
        self.width = int(width)
        self.height = int(height)
        if self.width < 1 or self.height < 1:
            raise ValueError("display dimensions must be positive")
        self._scratch_bytes = 0
        self.quality_tier = 1
        self.render_time_ms = 0

    def _clock_ms(self):
        if hasattr(time, "ticks_ms"):
            return time.ticks_ms()
        return int(time.time() * 1000)

    def _fill_rect(self, x, y, width, height, color):
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + width)
        y1 = min(self.height, y + height)
        if x1 > x0 and y1 > y0:
            self.display.fill_rect(x0, y0, x1 - x0, y1 - y0, int(color) & 0xFFFF)

    def _line(self, x0, y0, x1, y1, color):
        x0 = max(0, min(self.width - 1, int(x0)))
        y0 = max(0, min(self.height - 1, int(y0)))
        x1 = max(0, min(self.width - 1, int(x1)))
        y1 = max(0, min(self.height - 1, int(y1)))
        self.display.line(x0, y0, x1, y1, int(color) & 0xFFFF)

    def _lens(self, cx, cy, rx, ry, color, tilt=0.0):
        """Fill a tilted ellipse-like lens using one clipped horizontal span per row."""
        rx = max(1, int(rx))
        ry = max(1, int(ry))
        # Quantized horizontal bands trade a small amount of curve smoothness
        # for far fewer SPI window transactions on the WROOM-32.
        if self.quality_tier <= 0:
            segments = 4 if ry >= 8 else 3
        elif self.quality_tier == 1:
            segments = 6 if ry >= 8 else 4
        else:
            segments = 8 if ry >= 8 else 5
        diameter = (ry * 2) + 1
        for band in range(segments):
            top = -ry + ((diameter * band) // segments)
            bottom = -ry + ((diameter * (band + 1)) // segments) - 1
            if bottom < top:
                bottom = top
            dy = (top + bottom) // 2
            normalized = dy / float(ry)
            half = int(rx * sqrt(max(0.0, 1.0 - (normalized * normalized))))
            shift = int(float(tilt) * dy * 0.24)
            self._fill_rect(int(cx) + shift - half, int(cy) + top,
                            (half * 2) + 1, bottom - top + 1, color)

    def _draw_eye(self, cx, cy, rx, ry, mode, gaze_x, gaze_y, eye_tilt, glow, eye_open):
        rugged = mode == "rugged"
        if rugged:
            halo_outer = rgb565(72, 0, 3)
            halo_mid = rgb565(128, 0, 8)
            halo_inner = rgb565(210, 8, 18)
            shell = rgb565(74, 11, 20)
            socket = rgb565(9, 2, 5)
            lens = rgb565(240, 34, 42)
            lens_low = rgb565(118, 3, 12)
            iris = rgb565(255, 80, 48)
            highlight = rgb565(255, 198, 161)
        else:
            halo_outer = rgb565(7, 32, 50)
            halo_mid = rgb565(14, 78, 105)
            halo_inner = rgb565(38, 145, 174)
            shell = rgb565(66, 112, 133)
            socket = rgb565(5, 14, 22)
            lens = rgb565(205, 237, 248)
            lens_low = rgb565(94, 161, 182)
            iris = rgb565(86, 218, 245)
            highlight = WHITE

        strength = max(0.0, min(1.0, float(glow)))
        outer = int((4 + (8 * strength)))
        mid = int((2 + (5 * strength)))
        self._lens(cx, cy, rx + outer, ry + 7, halo_outer, eye_tilt)
        self._lens(cx, cy, rx + mid, ry + 4, halo_mid, eye_tilt)
        self._lens(cx, cy, rx + 2, ry + 2, halo_inner, eye_tilt)
        self._lens(cx, cy, rx, ry, shell, eye_tilt)
        self._lens(cx, cy + 1, rx - 4, max(2, ry - 4), socket, eye_tilt)
        # Lit surface is shaded in three horizontal bands rather than a flat outline.
        self._lens(cx, cy - 1, rx - 7, max(2, ry - 8), lens, eye_tilt)
        self._lens(cx, cy + max(1, ry // 4), rx - 9, max(2, ry // 2), lens_low, eye_tilt)

        px = int(cx + (float(gaze_x) * 9))
        py = int(cy + (float(gaze_y) * 6))
        self._lens(px, py, max(4, rx // 3), max(5, ry // 2), iris)
        self._lens(px, py + 1, max(2, rx // 7), max(3, ry // 4), socket)
        self._lens(px - max(2, rx // 9), py - max(3, ry // 5), 3, 3, highlight)
        self._line(cx - rx + 2, cy - (ry // 3), cx, cy - ry + 3, highlight)
        self._line(cx, cy - ry + 3, cx + rx - 2, cy - (ry // 3), highlight)

        lid_y = cy - int((ry * (0.62 - (eye_open * 0.1))))
        self._line(cx - rx - 2, lid_y + int(eye_tilt * 7), cx + rx + 2,
                   lid_y - int(eye_tilt * 7), shell)

    def _draw_mouth(self, cx, cy, mode, mouth, glow):
        rugged = mode == "rugged"
        color = rgb565(255, 58, 66) if rugged else rgb565(180, 235, 247)
        dark = rgb565(30, 4, 8) if rugged else rgb565(8, 22, 30)
        width = max(10, int(self.width * 0.115))
        if mouth == "open":
            self._lens(cx, cy, width, max(5, int(self.height * 0.07)), color)
            self._lens(cx, cy + 1, max(4, width - 4), max(3, int(self.height * 0.045)), dark)
            self._line(cx - width // 2, cy - 2, cx + width // 2, cy - 2, color)
        elif mouth == "smile":
            self._line(cx - width, cy - 3, cx - (width // 2), cy + 5, color)
            self._line(cx - (width // 2), cy + 5, cx, cy + 8, color)
            self._line(cx, cy + 8, cx + (width // 2), cy + 5, color)
            self._line(cx + (width // 2), cy + 5, cx + width, cy - 3, color)
        elif mouth == "frown":
            self._line(cx - width, cy + 6, cx - (width // 2), cy - 2, color)
            self._line(cx - (width // 2), cy - 2, cx, cy - 5, color)
            self._line(cx, cy - 5, cx + (width // 2), cy - 2, color)
            self._line(cx + (width // 2), cy - 2, cx + width, cy + 6, color)
        elif mouth == "tight":
            self._line(cx - width, cy, cx - (width // 3), cy - 2, color)
            self._line(cx - (width // 3), cy - 2, cx + (width // 3), cy - 2, color)
            self._line(cx + (width // 3), cy - 2, cx + width, cy, color)
        else:
            self._line(cx - width, cy, cx + width, cy, color)

    def _draw_tears(self, cx, cy, rx, ry, amount, mode):
        if amount <= 0.02:
            return
        blue = rgb565(90, 205, 255)
        length = max(3, int((self.height * 0.085) * amount))
        self._line(cx - rx + 4, cy + ry - 1, cx - rx + 4, cy + ry + length, blue)
        self._line(cx - rx + 4, cy + ry + length, cx - rx + 7, cy + ry + length + 3, blue)
        self._lens(cx - rx + 7, cy + ry + length + 4, 2, 3, blue)
        if amount > 0.55:
            self._line(cx + rx - 5, cy + ry, cx + rx - 5, cy + ry + (length // 2), blue)

    def _draw_fire(self, cx, cy, rx, amount):
        if amount <= 0.02:
            return
        ember = rgb565(255, 92, 24)
        hot = rgb565(255, 202, 84)
        rise = int(5 + (12 * amount))
        self._line(cx - rx, cy + 5, cx - rx - 5, cy - rise, ember)
        self._line(cx - rx - 5, cy - rise, cx - rx + 1, cy - 2, hot)
        self._line(cx + rx, cy + 5, cx + rx + 5, cy - rise, ember)
        self._line(cx + rx + 5, cy - rise, cx + rx - 1, cy - 2, hot)
        self._lens(cx - rx - 8, cy - rise - 3, 2, 2, hot)
        self._lens(cx + rx + 8, cy - rise - 1, 2, 2, ember)

    def render(self, frame):
        started_at = self._clock_ms()
        d = self.display
        mode = "rugged" if frame.get("mode") == "rugged" else "standard"
        expression = frame.get("expression", frame.get("emotion", "neutral"))
        eye_open = max(0.05, min(1.0, float(frame.get("eye_open", 0.88))))
        glow = max(0.0, min(1.0, float(frame.get("glow", 0.38))))
        gaze_x = max(-1.0, min(1.0, float(frame.get("gaze_x", frame.get("pupil_x", 0) / 8.0))))
        gaze_y = max(-1.0, min(1.0, float(frame.get("gaze_y", frame.get("pupil_y", 0) / 5.0))))
        eye_tilt = max(-1.0, min(1.0, float(frame.get("eye_tilt", -0.2 if expression == "angry" else 0.0))))
        brow_tilt = max(-1.0, min(1.0, float(frame.get("brow_tilt", eye_tilt))))
        tear = max(0.0, min(1.0, float(frame.get("tear", 0.0))))
        fire = max(0.0, min(1.0, float(frame.get("fire", 0.0))))

        d.fill(BLACK)
        scale_x = self.width / 240.0
        scale_y = self.height / 240.0
        scale = min(scale_x, scale_y)
        rx = max(10, int(32 * scale))
        base_ry = max(8, int(29 * scale))
        ry = max(3, int(base_ry * eye_open))
        left_cx = int(self.width * 0.33)
        right_cx = int(self.width * 0.67)
        eye_cy = int(self.height * 0.39)
        mouth_cy = int(self.height * 0.76)
        self._draw_eye(left_cx, eye_cy, rx, ry, mode, gaze_x, gaze_y, eye_tilt, glow, eye_open)
        self._draw_eye(right_cx, eye_cy, rx, ry, mode, gaze_x, gaze_y, -eye_tilt, glow, eye_open)
        if tear > 0:
            self._draw_tears(left_cx, eye_cy, rx, ry, tear, mode)
        if fire > 0:
            self._draw_fire(right_cx, eye_cy, rx, fire)
        self._line(left_cx - rx, eye_cy - ry - 5, left_cx + rx, eye_cy - ry - 5 + int(brow_tilt * 8),
                   rgb565(230, 244, 255) if mode == "standard" else rgb565(255, 80, 80))
        self._line(right_cx - rx, eye_cy - ry - 5 - int(brow_tilt * 8), right_cx + rx,
                   eye_cy - ry - 5, rgb565(230, 244, 255) if mode == "standard" else rgb565(255, 80, 80))
        mouth = frame.get("mouth", "frown" if expression in ("sad", "crying", "sorry", "disappointment") else "closed")
        self._draw_mouth(self.width // 2, mouth_cy, mode, mouth, glow)
        d.show()

        elapsed = diff_ms(self._clock_ms(), started_at)
        if elapsed < 0:
            elapsed = 0
        self.render_time_ms = int(elapsed)
        # Start at balanced quality. If a full draw exceeds the roughly
        # 15-fps frame budget, step down; when comfortably under budget,
        # restore detail one tier at a time. This adapts the next frame.
        if self.render_time_ms >= 67:
            self.quality_tier = max(0, self.quality_tier - 1)
        elif self.render_time_ms <= 30:
            self.quality_tier = min(2, self.quality_tier + 1)
