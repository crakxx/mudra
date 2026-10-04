import unittest

from gestures import DepthHoldDetector, DepthTapDetector


class GestureTests(unittest.TestCase):
    def test_tap_fires_on_return_to_rest(self):
        d = DepthTapDetector(trigger=0.10, release=0.03, cooldown=0.2)
        self.assertFalse(d.update(0.00, 0.0))
        self.assertFalse(d.update(0.12, 0.1))
        self.assertFalse(d.update(0.08, 0.15))
        self.assertTrue(d.update(0.02, 0.2))
        self.assertFalse(d.update(0.00, 0.21))

    def test_tap_is_direction_independent(self):
        d = DepthTapDetector(trigger=0.10, release=0.03, cooldown=0.0)
        d.update(0.20, 0.0)
        self.assertFalse(d.update(0.08, 0.1))
        self.assertTrue(d.update(0.19, 0.2))

    def test_hold_starts_and_stops(self):
        d = DepthHoldDetector(trigger=0.10, release=0.03)
        self.assertEqual(d.update(0.0), (False, False))
        self.assertEqual(d.update(0.12), (True, True))
        self.assertEqual(d.update(0.10), (True, False))
        self.assertEqual(d.update(0.02), (False, True))


if __name__ == "__main__":
    unittest.main()
