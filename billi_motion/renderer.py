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
        self.style = "glossy"

    def set_style(self, style):
        """Select 'flat' or 'glossy' eye rendering; reject unknown styles."""
        if style not in ("flat", "glossy"):
            return False
        self.style = style
        return True

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

    def _round_rect(self, cx, cy, width, height, radius, color):
        """Draw a rounded rectangle as a small set of clipped RGB565 bands."""
        width = max(2, int(width))
        height = max(2, int(height))
        radius = max(1, min(int(radius), width // 2, height // 2))
        if self.quality_tier <= 0:
            segments = 6
        elif self.quality_tier == 1:
            segments = 8
        else:
            segments = 10
        diameter = height
        for band in range(segments):
            top = -height // 2 + ((diameter * band) // segments)
            bottom = -height // 2 + ((diameter * (band + 1)) // segments) - 1
            if bottom < top:
                bottom = top
            mid_y = (top + bottom) // 2
            corner_y = max(0, abs(mid_y) - (height / 2.0 - radius))
            if corner_y >= radius:
                inset = radius
            else:
                inset = radius - int(sqrt(max(0.0, (radius * radius) - (corner_y * corner_y))))
            half = max(1, (width // 2) - inset)
            self._fill_rect(cx - half, cy + top, half * 2, bottom - top + 1, color)

    def _draw_eye(self, cx, cy, mirror, mode, style, gaze_x, gaze_y,
                  lid_top, lid_bottom, lid_tilt, eye_scale, pupil_scale, blink):
        """Render the reference oval or glossy rounded-rectangle eye."""
        rugged = mode == "rugged"
        scale = max(0.7, min(1.2, float(eye_scale)))
        blink = max(0.0, min(1.0, float(blink)))
        if rugged:
            eye_color = rgb565(255, 56, 66)
            eye_low = rgb565(126, 7, 20)
            rim = rgb565(255, 150, 160)
            pupil = rgb565(24, 2, 7)
            flat_pupil = rgb565(34, 2, 8)
            highlight = WHITE
        else:
            eye_color = rgb565(242, 246, 250)
            eye_low = rgb565(150, 177, 191)
            rim = rgb565(183, 219, 232)
            pupil = rgb565(5, 17, 26)
            flat_pupil = rgb565(8, 24, 34)
            highlight = WHITE

        is_flat = style == "flat"
        width = int((72 if is_flat else 84) * scale)
        height = int(98 * scale)
        gx = float(gaze_x)
        gy = float(gaze_y)
        eye_cx = int(cx + gx * (28 if is_flat else 18))
        eye_cy = int(cy + gy * (22 if is_flat else 12))
        x0 = eye_cx - width // 2
        y0 = eye_cy - height // 2

        if is_flat:
            self._lens(eye_cx, eye_cy, width // 2, height // 2, eye_color)
            px = int(eye_cx + gx * 20)
            py = int(eye_cy + gy * 22)
            self._lens(px, py, max(3, int(7 * pupil_scale)),
                       max(5, int(17 * pupil_scale)), flat_pupil)
        else:
            radius = int(width * 0.38)
            self._round_rect(eye_cx, eye_cy, width, height, radius, rim)
            inset = max(3, int(6 * scale))
            inner_w = width - (inset * 2)
            inner_h = height - (inset * 2)
            inner_radius = max(2, radius - inset)
            self._round_rect(eye_cx, eye_cy, inner_w, inner_h,
                             inner_radius, eye_color)
            # Low-side shading gives the bright surface volume without a
            # framebuffer or a high-cost per-pixel gradient.
            self._round_rect(eye_cx, eye_cy + int(height * 0.16),
                             max(2, inner_w - inset * 2),
                             max(2, int(inner_h * 0.36)),
                             max(2, inner_radius // 2), eye_low)
            px = int(eye_cx + gx * 14)
            py = int(eye_cy + gy * 10)
            pupil_rx = max(4, int(20 * scale * pupil_scale))
            pupil_ry = max(6, int(25 * scale * pupil_scale))
            self._lens(px, py, pupil_rx, pupil_ry, pupil)
            self._lens(px - max(3, pupil_rx // 2), py - max(4, pupil_ry // 2),
                       max(3, int(5 * scale)), max(3, int(7 * scale)), highlight)
            self._lens(px + max(3, pupil_rx // 2), py + max(3, pupil_ry // 2),
                       max(2, int(2.5 * scale)), max(2, int(3 * scale)), highlight)

        self._draw_lids(
            eye_cx, eye_cy, width, height,
            lid_top, lid_bottom, lid_tilt, blink, mirror
        )

    def _draw_lids(self, cx, cy, width, height, lid_top, lid_bottom,
                   lid_tilt, blink, mirror):
        """Carve curved upper/lower lids using bounded vertical span bands.

        This is a MicroPython/direct-SPI adaptation of the reference's
        column-wise lid equations. The band count trades curve smoothness
        against display transactions on the ESP32-WROOM-32.
        """
        if self.quality_tier <= 0:
            segments = 6
        elif self.quality_tier == 1:
            segments = 9
        else:
            segments = 12

        top_shape = float(lid_top) * (1.0 - blink) + (0.55 * blink)
        tilt = float(lid_tilt) * (1.0 - blink)
        arc = float(lid_bottom) * (1.0 - blink)
        lower_flat = 0.45 * blink
        x0 = cx - width // 2 - 1
        top_edge = cy - height // 2 - 2
        bottom_edge = cy + height // 2 + 2
        for band in range(segments):
            left = x0 + ((width + 2) * band // segments)
            right = x0 + ((width + 2) * (band + 1) // segments)
            if right <= left:
                continue
            mid_x = (left + right) // 2
            u = (mid_x - cx) / float(max(1, width * 0.5))
            yt = cy - height // 2 + top_shape * height + tilt * mirror * u * height * 0.35
            if yt > cy - height // 2:
                self._fill_rect(left, top_edge, right - left,
                                int(yt) - top_edge, BLACK)
            yb = cy + height // 2 - height * (lower_flat + arc * (1.0 - u * u))
            if yb < cy + height // 2:
                self._fill_rect(left, int(yb), right - left,
                                bottom_edge - int(yb), BLACK)

    def _draw_mouth(self, cx, cy, mode, mouth, glow, mouth_open=0.0):
        rugged = mode == "rugged"
        color = rgb565(255, 58, 66) if rugged else rgb565(180, 235, 247)
        dark = rgb565(30, 4, 8) if rugged else rgb565(8, 22, 30)
        width = max(10, int(self.width * 0.115))
        if mouth == "talk":
            level = max(0.0, min(1.0, float(mouth_open)))
            open_h = max(2, int(self.height * (0.018 + 0.075 * level)))
            talk_w = int(width * (0.78 + 0.34 * level))
            self._lens(cx, cy, talk_w, open_h, color)
            self._lens(cx, cy + 1, max(3, talk_w - 3), max(1, int(open_h * 0.72)), dark)
            if level > 0.55:
                self._line(cx - talk_w // 2, cy - open_h // 2,
                           cx + talk_w // 2, cy - open_h // 2, color)
        elif mouth == "open":
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
        elif mouth == "smirk":
            self._line(cx - width, cy + 1, cx, cy + 5, color)
            self._line(cx, cy + 5, cx + width, cy - 4, color)
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
        eye_style = frame.get("eye_style", self.style)
        if eye_style not in ("flat", "glossy"):
            eye_style = self.style
        lid_defaults = {
            "happy": (0.0, 0.55, 0.0, 1.0, 1.0),
            "sad": (0.20, 0.0, -0.60, 0.95, 1.05),
            "angry": (0.25, 0.0, 0.60, 1.0, 0.85),
            "sleepy": (0.50, 0.0, 0.0, 1.0, 1.0),
            "surprise": (0.0, 0.0, 0.0, 1.12, 0.70),
            "surprised": (0.0, 0.0, 0.0, 1.12, 0.70),
        }
        defaults = lid_defaults.get(expression, (0.0, 0.0, 0.0, 1.0, 1.0))
        lid_top = max(0.0, min(1.0, float(frame.get("lid_top", defaults[0]))))
        lid_bottom = max(0.0, min(1.0, float(frame.get("lid_bottom", defaults[1]))))
        lid_tilt = max(-1.0, min(1.0, float(frame.get("lid_tilt", defaults[2]))))
        eye_scale = max(0.7, min(1.2, float(frame.get("eye_scale", defaults[3]))))
        pupil_scale = max(0.6, min(1.2, float(frame.get("pupil_scale", defaults[4]))))
        blink = max(0.0, min(1.0, float(frame.get("blink", 0.0))))
        glow = max(0.0, min(1.0, float(frame.get("glow", 0.38))))
        gaze_x = max(-1.0, min(1.0, float(frame.get("gaze_x", frame.get("pupil_x", 0) / 8.0))))
        gaze_y = max(-1.0, min(1.0, float(frame.get("gaze_y", frame.get("pupil_y", 0) / 5.0))))
        eye_tilt = max(-1.0, min(1.0, float(frame.get("eye_tilt", -0.2 if expression == "angry" else 0.0))))
        brow_tilt = max(-1.0, min(1.0, float(frame.get("brow_tilt", eye_tilt))))
        tear = max(0.0, min(1.0, float(frame.get("tear", 0.0))))
        fire = max(0.0, min(1.0, float(frame.get("fire", 0.0))))

        d.fill(BLACK)
        scale = min(self.width / 240.0, self.height / 240.0)
        rx = max(10, int((36 if eye_style == "flat" else 42) * eye_scale * scale))
        ry = max(8, int(49 * eye_scale * scale))
        eye_width = rx * 2
        eye_height = ry * 2
        left_cx = int(self.width * 0.285)
        right_cx = int(self.width * 0.715)
        eye_cy = int(self.height * 0.50)
        mouth_cy = int(self.height * 0.76)
        self._draw_eye(left_cx, eye_cy, +1, mode, eye_style, gaze_x, gaze_y,
                       lid_top, lid_bottom, lid_tilt, eye_scale, pupil_scale, blink)
        self._draw_eye(right_cx, eye_cy, -1, mode, eye_style, gaze_x, gaze_y,
                       lid_top, lid_bottom, lid_tilt, eye_scale, pupil_scale, blink)
        if tear > 0:
            self._draw_tears(left_cx, eye_cy, rx, ry, tear, mode)
        if fire > 0:
            self._draw_fire(right_cx, eye_cy, rx, fire)
        mouth = frame.get("mouth_pose", frame.get("mouth", "frown" if expression in ("sad", "crying", "sorry", "disappointment") else "closed"))
        mouth_open = max(0.0, min(1.0, float(frame.get("mouth_open", 0.0))))
        self._draw_mouth(self.width // 2, mouth_cy, mode, mouth, glow, mouth_open)
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
