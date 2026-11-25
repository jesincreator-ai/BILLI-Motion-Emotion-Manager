"""240x240 RGB565 face renderer for the BILLI R-20 ST7789 TFT.

The normal profile uses white graphics; rugged mode uses red graphics.
The display background remains black. Compatible with MicroPython ST7789
drivers exposing fill, rect, fill_rect, line and show.
"""

BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800


class FaceRenderer:
    def __init__(self, display, width=240, height=240):
        self.display = display
        self.width = int(width)
        self.height = int(height)

    def render(self, frame):
        d = self.display
        color = RED if frame.get("mode") == "rugged" else WHITE
        d.fill(BLACK)

        # Face layout is scaled for the square 240x240 panel.
        eye_y = 72
        eye_w = 62
        eye_h = 54
        left_x = 40
        right_x = self.width - left_x - eye_w
        expression = frame.get("expression", frame.get("emotion", "neutral"))

        if frame.get("eyes_closed"):
            d.line(left_x, eye_y + 27, left_x + eye_w, eye_y + 27, color)
            d.line(right_x, eye_y + 27, right_x + eye_w, eye_y + 27, color)
        else:
            d.rect(left_x, eye_y, eye_w, eye_h, color)
            d.rect(right_x, eye_y, eye_w, eye_h, color)
            px = max(-8, min(8, int(frame.get("pupil_x", 0)) * 2))
            py = max(-6, min(6, int(frame.get("pupil_y", 0)) * 2))
            d.fill_rect(left_x + 25 + px, eye_y + 19 + py, 13, 17, color)
            d.fill_rect(right_x + 25 + px, eye_y + 19 + py, 13, 17, color)

        if expression == "angry":
            d.line(left_x, 58, left_x + eye_w, 72, color)
            d.line(right_x, 72, right_x + eye_w, 58, color)
        elif expression == "sad":
            d.line(left_x, 66, left_x + eye_w, 56, color)
            d.line(right_x, 56, right_x + eye_w, 66, color)
        elif expression == "curious":
            d.line(left_x, 57, left_x + eye_w, 57, color)
            d.line(right_x, 57, right_x + eye_w, 57, color)
        else:
            d.line(left_x, 59, left_x + eye_w, 59, color)
            d.line(right_x, 59, right_x + eye_w, 59, color)

        cx = self.width // 2
        my = 183
        mouth = frame.get("mouth", "closed")
        if mouth == "open":
            d.rect(cx - 17, my - 13, 34, 27, color)
        elif mouth == "smile":
            d.line(cx - 27, my - 3, cx, my + 12, color)
            d.line(cx, my + 12, cx + 27, my - 3, color)
        elif mouth == "frown":
            d.line(cx - 27, my + 8, cx, my - 7, color)
            d.line(cx, my - 7, cx + 27, my + 8, color)
        else:
            d.line(cx - 22, my, cx + 22, my, color)

        d.show()
