import unittest
from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"


class PreviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.elements = []
        self.external_assets = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.elements.append((tag, values))
        if "id" in values:
            self.ids.add(values["id"])
        for key in ("src", "href"):
            value = values.get(key, "")
            if value.startswith(("http://", "https://", "//")):
                self.external_assets.append(value)


class BrowserPreviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.parser = PreviewParser()
        cls.parser.feed(cls.html)

    def test_preview_uses_canvas_and_required_controls(self):
        self.assertTrue(any(tag == "canvas" and attrs.get("id") == "face"
                            for tag, attrs in self.parser.elements))
        required = {"standard", "rugged", "emotion", "intensity",
                    "autoIdle", "blink", "reset"}
        self.assertTrue(required.issubset(self.parser.ids))

    def test_all_eight_emotions_are_present(self):
        for emotion in ("happy", "sad", "surprise", "disappointment",
                        "sorry", "crying", "angry", "ego_fire"):
            with self.subTest(emotion=emotion):
                self.assertIn(emotion, self.html)

    def test_preview_exposes_layered_lighting_and_animation(self):
        for feature in ("createRadialGradient", "createLinearGradient",
                        "requestAnimationFrame", "transition", "glow"):
            with self.subTest(feature=feature):
                self.assertIn(feature, self.html)

    def test_preview_has_no_external_runtime_assets(self):
        self.assertEqual(self.parser.external_assets, [])
        self.assertNotRegex(self.html, re.compile(r"@import\\s+url\\(\\s*['\"]?https?://", re.I))


if __name__ == "__main__":
    unittest.main()
