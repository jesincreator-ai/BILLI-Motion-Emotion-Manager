"""Adapter for an already initialized SSD1306-compatible display driver.

This module intentionally does not bundle a third-party display driver.
Pass an initialized display object with fill/rect/fill_rect/line/show methods.
"""
from billi_motion.renderer import FaceRenderer


class ESP32FaceDisplay:
    def __init__(self, display, width=128, height=64):
        self.renderer = FaceRenderer(display, width, height)

    def draw(self, frame):
        self.renderer.render(frame)
