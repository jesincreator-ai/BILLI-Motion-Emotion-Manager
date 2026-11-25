"""Display adapter for an initialized 240x240 ST7789 RGB565 TFT."""
from billi_motion.renderer import FaceRenderer


class ESP32FaceDisplay:
    def __init__(self, display, width=240, height=240):
        self.renderer = FaceRenderer(display, width, height)

    def draw(self, frame):
        self.renderer.render(frame)
