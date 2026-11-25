"""Minimal monochrome face renderer for SSD1306-like display APIs."""


class FaceRenderer:
    def __init__(self, display, width=128, height=64):
        self.display = display
        self.width = int(width)
        self.height = int(height)

    def render(self, frame):
        d = self.display
        d.fill(0)
        eye_y = 17
        eye_w = 34
        eye_h = 25
        left_x = 19
        right_x = self.width - left_x - eye_w
        if frame.get("eyes_closed"):
            d.line(left_x, eye_y + 13, left_x + eye_w, eye_y + 13, 1)
            d.line(right_x, eye_y + 13, right_x + eye_w, eye_y + 13, 1)
        else:
            d.rect(left_x, eye_y, eye_w, eye_h, 1)
            d.rect(right_x, eye_y, eye_w, eye_h, 1)
            px = int(frame.get("pupil_x", 0))
            py = int(frame.get("pupil_y", 0))
            d.fill_rect(left_x + 13 + px, eye_y + 8 + py, 8, 10, 1)
            d.fill_rect(right_x + 13 + px, eye_y + 8 + py, 8, 10, 1)
        expression = frame.get("expression", "neutral")
        if expression == "angry":
            d.line(left_x, 8, left_x + eye_w, 14, 1)
            d.line(right_x, 14, right_x + eye_w, 8, 1)
        elif expression == "sad":
            d.line(left_x, 10, left_x + eye_w, 6, 1)
            d.line(right_x, 6, right_x + eye_w, 10, 1)
        else:
            d.line(left_x, 8, left_x + eye_w, 8, 1)
            d.line(right_x, 8, right_x + eye_w, 8, 1)
        mouth = frame.get("mouth", "closed")
        cx = self.width // 2
        my = 53
        if mouth == "open":
            d.ellipse(cx - 8, my - 5, 16, 10, 1) if hasattr(d, "ellipse") else d.rect(cx - 6, my - 5, 12, 10, 1)
        elif mouth == "smile":
            d.line(cx - 12, my - 2, cx, my + 3, 1)
            d.line(cx, my + 3, cx + 12, my - 2, 1)
        elif mouth == "frown":
            d.line(cx - 12, my + 2, cx, my - 3, 1)
            d.line(cx, my - 3, cx + 12, my + 2, 1)
        else:
            d.line(cx - 9, my, cx + 9, my, 1)
        d.show()
