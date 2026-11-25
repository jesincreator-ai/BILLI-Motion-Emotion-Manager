import unittest
from html.parser import HTMLParser
from pathlib import Path

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

    def test_speaking_state_is_available_in_both_modes(self):
        self.assertIn('standard: ["neutral"', self.html)
        self.assertIn('rugged: ["neutral"', self.html)
        self.assertIn('speaking: {', self.html)
        self.assertIn('mouth:"talk"', self.html)

    def test_mouth_animates_for_speech_and_emotions(self):
        for feature in ('function drawMouth(pose,palette,now)',
                       'pose.mouth==="talk"', 'talkWave', 'smileMotion',
                       'jawPulse', 'drawMouth(pose,palette,now)'):
            with self.subTest(feature=feature):
                self.assertIn(feature, self.html)

    def test_mouth_lab_is_offline_and_has_talk_volume_controls(self):
        mouth_html = (ROOT / "mouth-lab.html").read_text(encoding="utf-8")
        self.assertIn("BILLI · Mouth & Emotion Lab", mouth_html)
        self.assertIn("simulated speech volume", mouth_html.lower())
        self.assertIn("mouthOpen", mouth_html)
        self.assertIn("requestAnimationFrame", mouth_html)

    def test_glossy_palettes_are_pearl_white_for_calm_and_crimson_for_rugged(self):
        self.assertIn('eyeTop:"#ffffff"', self.html)
        self.assertIn('eyeMid:"#eef3f7"', self.html)
        self.assertIn('eyeLow:"#96aab6"', self.html)
        self.assertIn('eyeMid:"#e32335"', self.html)
        self.assertIn('eyeLow:"#5d0610"', self.html)
        self.assertIn('glow:"#ff283d"', self.html)

    def test_reference_eye_styles_are_selectable_with_glossy_default(self):
        self.assertIn('eyeStyle:"glossy"', self.html)
        self.assertIn('id="flatStyle"', self.html)
        self.assertIn('id="glossyStyle"', self.html)
        self.assertIn("function setEyeStyle", self.html)

    def test_reference_six_moods_are_available_in_both_profiles(self):
        for mood in ("happy", "sad", "angry", "sleepy", "surprise"):
            with self.subTest(mood=mood):
                self.assertIn(mood, self.html)
        self.assertIn('standard: ["neutral", "happy", "sad", "angry", "sleepy", "surprise"', self.html)
        self.assertIn('rugged: ["neutral", "happy", "sad", "angry", "sleepy", "surprise"', self.html)

    def test_reference_lid_geometry_and_blink_are_rendered(self):
        for field in ("lidTop", "lidBottom", "lidTilt", "eyeScale", "pupilScale", "blink"):
            with self.subTest(field=field):
                self.assertIn(field, self.html)
        self.assertIn("quadraticCurveTo", self.html)
        self.assertIn("roundRect", self.html)

    def test_preview_has_no_external_runtime_assets(self):
        self.assertEqual(self.parser.external_assets, [])
        self.assertNotIn("@import", self.html.lower())


if __name__ == "__main__":
    unittest.main()
