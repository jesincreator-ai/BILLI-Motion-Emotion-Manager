"""Display adapter for an initialized 240x240 ST7789 RGB565 TFT."""
from billi_motion.renderer import FaceRenderer


class ESP32FaceDisplay:
    def __init__(self, display, width=240, height=240):
        self.renderer = FaceRenderer(display, width, height)

    def set_style(self, style):
        """Set the eye rendering style to 'flat' or 'glossy'."""
        return self.renderer.set_style(style)

    def draw(self, frame):
        self.renderer.render(frame)
