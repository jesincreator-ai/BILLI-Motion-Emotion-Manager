import unittest

from billi_motion.animation import FaceAnimator
from billi_motion.emotion import EMOTIONS, EmotionEngine
from billi_motion.manager import MotionEmotionManager
from billi_motion.renderer import FaceRenderer, rgb565


STANDARD = ("happy", "sad", "surprise", "disappointment", "sorry", "crying")
RUGGED = ("angry", "ego_fire")


class EmotionContractTests(unittest.TestCase):
    def test_all_named_emotions_and_neutral_are_declared(self):
        self.assertEqual(
            set(EMOTIONS),
            {"neutral", "happy", "sad", "surprise", "disappointment",
             "sorry", "crying", "angry", "ego_fire"},
        )

    def test_standard_accepts_only_standard_emotions_and_neutral(self):
        manager = MotionEmotionManager()
        for emotion in STANDARD:
            self.assertTrue(manager.set_emotion(emotion, 0.8, 10), emotion)
        for emotion in RUGGED:
            self.assertFalse(manager.set_emotion(emotion, 0.8, 20), emotion)
        self.assertTrue(manager.set_emotion("neutral", 0.5, 30))

    def test_rugged_accepts_only_rugged_emotions_and_neutral(self):
        manager = MotionEmotionManager()
        self.assertTrue(manager.set_mode("rugged", 10))
        for emotion in RUGGED:
            self.assertTrue(manager.set_emotion(emotion, 0.8, 20), emotion)
        for emotion in STANDARD:
            self.assertFalse(manager.set_emotion(emotion, 0.8, 30), emotion)
        self.assertTrue(manager.set_emotion("neutral", 0.5, 40))

    def test_surprised_compatibility_alias_is_canonicalized(self):
        engine = EmotionEngine()
        self.assertTrue(engine.set_emotion("surprised", 0.7, 5))
        self.assertEqual(engine.get_state()["emotion"], "surprise")
        manager = MotionEmotionManager()
        self.assertTrue(manager.set_emotion("surprised", 0.7, 5))
        self.assertEqual(manager.tick(6)["emotion"], "surprise")

    def test_mode_change_resets_incompatible_expression_to_neutral(self):
        manager = MotionEmotionManager()
        self.assertTrue(manager.set_emotion("happy", 1.0, 1))
        self.assertTrue(manager.set_mode("rugged", 2))
        frame = manager.tick(3)
        self.assertEqual(frame["emotion"], "neutral")
        self.assertEqual(frame["mode"], "rugged")

    def test_invalid_mode_or_emotion_does_not_mutate_state(self):
        manager = MotionEmotionManager()
        self.assertTrue(manager.set_emotion("happy", 0.6, 1))
        self.assertFalse(manager.set_mode("ultraviolet", 2))
        self.assertFalse(manager.set_emotion("not-an-emotion", 1.0, 3))
        frame = manager.tick(4)
        self.assertEqual(frame["mode"], "standard")
        self.assertEqual(frame["emotion"], "happy")

    def test_calm_alias_selects_standard_mode(self):
        manager = MotionEmotionManager()
        self.assertTrue(manager.set_mode("calm", 10))
        self.assertEqual(manager.tick(11)["mode"], "standard")


class EmotionLocaleTests(unittest.TestCase):
    def test_all_named_emotions_have_english_tamil_and_sinhala_labels(self):
        from billi_motion.locales import phrase
        for emotion in STANDARD + RUGGED + ("neutral",):
            for language in ("en", "ta", "si"):
                with self.subTest(emotion=emotion, language=language):
                    self.assertNotEqual(phrase(emotion, language), emotion)


class CinematicAnimationTests(unittest.TestCase):
    def test_expression_transition_is_bounded_and_completes(self):
        animator = FaceAnimator(transition_duration_ms=300)
        self.assertTrue(animator.set_expression("happy", 1.0, 0))
        start = animator.tick(0)
        middle = animator.tick(150)
        end = animator.tick(300)
        self.assertGreaterEqual(start["transition"], 0.0)
        self.assertLess(middle["transition"], 1.0)
        self.assertGreater(middle["transition"], 0.0)
        self.assertEqual(end["transition"], 1.0)
        self.assertFalse(end["transitioning"])

    def test_expression_specific_effects_are_bounded(self):
        animator = FaceAnimator()
        for emotion in EMOTIONS:
            self.assertTrue(animator.set_expression(emotion, 1.0, 0))
            frame = animator.tick(250)
            for key in ("eye_open", "glow", "tear", "fire", "transition", "blink"):
                self.assertGreaterEqual(frame[key], 0.0, (emotion, key))
                self.assertLessEqual(frame[key], 1.0, (emotion, key))
        animator.set_expression("crying", 1.0, 0)
        self.assertGreater(animator.tick(10)["tear"], 0.0)
        animator.set_expression("ego_fire", 1.0, 0)
        self.assertGreater(animator.tick(10)["fire"], 0.0)

    def test_intensity_scales_expression_pose_and_glow(self):
        full = FaceAnimator(transition_duration_ms=0)
        soft = FaceAnimator(transition_duration_ms=0)
        self.assertTrue(full.set_expression("angry", 1.0, 0))
        self.assertTrue(soft.set_expression("angry", 0.2, 0))
        full_frame = full.tick(10)
        soft_frame = soft.tick(10)
        self.assertLess(abs(soft_frame["eye_tilt"]), abs(full_frame["eye_tilt"]))
        self.assertLess(soft_frame["glow"], full_frame["glow"])

    def test_idle_gaze_has_bounded_subtle_drift(self):
        animator = FaceAnimator()
        animator.look(0, 0)
        frame = animator.tick(1000)
        self.assertGreater(abs(frame["gaze_x"]) + abs(frame["gaze_y"]), 0.0)
        self.assertLessEqual(abs(frame["gaze_x"]), 0.1)
        self.assertLessEqual(abs(frame["gaze_y"]), 0.1)

    def test_look_is_bounded_and_large_time_step_does_not_loop(self):
        animator = FaceAnimator()
        animator.look(999, -999)
        frame = animator.tick(2_000_000_000)
        self.assertLessEqual(abs(frame["gaze_x"]), 1.0)
        self.assertLessEqual(abs(frame["gaze_y"]), 1.0)
        self.assertTrue(0.0 <= frame["glow"] <= 1.0)

    def test_blink_remains_timed(self):
        animator = FaceAnimator(blink_interval_ms=100, blink_duration_ms=20)
        self.assertFalse(animator.tick(0)["eyes_closed"])
        self.assertTrue(animator.tick(100)["eyes_closed"])
        self.assertTrue(animator.tick(115)["eyes_closed"])
        self.assertFalse(animator.tick(121)["eyes_closed"])


class FakeDisplay:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.calls = []

    def _color(self, color):
        if not 0 <= int(color) <= 0xFFFF:
            raise AssertionError("color outside RGB565 range")

    def fill(self, color):
        self._color(color)
        self.calls.append(("fill", color))

    def rect(self, x, y, w, h, color):
        self._color(color)
        self._bounds(x, y, w, h)
        self.calls.append(("rect", x, y, w, h, color))

    def fill_rect(self, x, y, w, h, color):
        self._color(color)
        self._bounds(x, y, w, h)
        self.calls.append(("fill_rect", x, y, w, h, color))

    def line(self, x1, y1, x2, y2, color):
        self._color(color)
        self._point(x1, y1)
        self._point(x2, y2)
        self.calls.append(("line", x1, y1, x2, y2, color))

    def show(self):
        self.calls.append(("show",))

    def _point(self, x, y):
        if not (0 <= int(x) < self.width and 0 <= int(y) < self.height):
            raise AssertionError("draw point outside display bounds")

    def _bounds(self, x, y, w, h):
        if w <= 0 or h <= 0:
            raise AssertionError("empty drawing primitive")
        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            raise AssertionError("drawing primitive outside display bounds")


class EmbeddedRendererTests(unittest.TestCase):
    def test_renderer_reports_bounded_adaptive_quality_diagnostics(self):
        display = FakeDisplay(240, 240)
        renderer = FaceRenderer(display, 240, 240)
        renderer.render({"mode": "standard", "emotion": "happy"})
        self.assertIn(renderer.quality_tier, (0, 1, 2))
        self.assertGreaterEqual(renderer.render_time_ms, 0)

    def test_renderer_uses_only_supported_driver_methods_and_rgb565(self):
        display = FakeDisplay(240, 240)
        renderer = FaceRenderer(display, 240, 240)
        renderer.render({
            "mode": "rugged", "emotion": "ego_fire", "eye_open": 0.9,
            "glow": 1.0, "fire": 1.0, "tear": 0.0, "mouth": "open",
            "gaze_x": 0.25, "gaze_y": -0.15,
        })
        self.assertGreater(len(display.calls), 30)
        self.assertEqual(display.calls[0][0], "fill")
        self.assertEqual(display.calls[-1][0], "show")
        self.assertFalse(hasattr(renderer, "framebuffer"))

    def test_renderer_uses_a_bounded_number_of_display_transactions(self):
        display = FakeDisplay(240, 240)
        renderer = FaceRenderer(display, 240, 240)
        renderer.render({
            "mode": "rugged", "emotion": "ego_fire", "eye_open": 0.9,
            "glow": 1.0, "fire": 1.0, "tear": 0.0, "mouth": "open",
        })
        # A full-frame draw should remain below this transaction budget.
        self.assertLess(len(display.calls), 230)

    def test_renderer_clips_to_non_square_display(self):
        display = FakeDisplay(160, 120)
        renderer = FaceRenderer(display, 160, 120)
        renderer.render({
            "mode": "standard", "emotion": "crying", "eye_open": 1.0,
            "glow": 1.0, "tear": 1.0, "fire": 0.0, "mouth": "frown",
        })
        self.assertTrue(display.calls)
        self.assertEqual(display.calls[-1][0], "show")


class GlossyEyeReferenceTests(unittest.TestCase):
    def test_calm_eyes_use_pearl_white_lens_and_specular_highlights(self):
        display = FakeDisplay(240, 240)
        renderer = FaceRenderer(display, 240, 240)
        renderer.render({"mode": "standard", "emotion": "neutral", "eye_open": 0.88})

        colours = {call[-1] for call in display.calls if call[0] == "fill_rect"}
        self.assertIn(rgb565(250, 253, 255), colours)
        self.assertIn(0xFFFF, colours)

    def test_rugged_eyes_use_saturated_red_lens_and_white_reflections(self):
        display = FakeDisplay(240, 240)
        renderer = FaceRenderer(display, 240, 240)
        renderer.render({"mode": "rugged", "emotion": "angry", "eye_open": 0.75})

        colours = {call[-1] for call in display.calls if call[0] == "fill_rect"}
        self.assertIn(rgb565(255, 56, 66), colours)
        self.assertIn(0xFFFF, colours)

    def test_glossy_eyes_use_curved_occluding_lids_without_box_outlines(self):
        display = FakeDisplay(240, 240)
        renderer = FaceRenderer(display, 240, 240)
        renderer.render({"mode": "standard", "emotion": "happy", "eye_open": 0.72})

        black_lid_bands = [
            call for call in display.calls
            if call[0] == "fill_rect" and call[-1] == 0x0000
        ]
        box_outlines = [call for call in display.calls if call[0] == "rect"]
        self.assertGreaterEqual(len(black_lid_bands), 8)
        self.assertEqual(box_outlines, [])


if __name__ == "__main__":
    unittest.main()
