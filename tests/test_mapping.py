import unittest

from mapping import (
    camera_point_to_screen,
    oriented_vertical_delta,
    project_desk_normal,
    transform_normalized,
    validate_area,
    validate_camera_angle,
)


class MappingTests(unittest.TestCase):
    def assertPointAlmostEqual(self, actual, expected):
        self.assertAlmostEqual(actual[0], expected[0], places=7)
        self.assertAlmostEqual(actual[1], expected[1], places=7)

    def test_rotations(self):
        p = (0.2, 0.3)
        self.assertPointAlmostEqual(transform_normalized(*p, 0), (0.2, 0.3))
        self.assertPointAlmostEqual(transform_normalized(*p, 90), (0.7, 0.2))
        self.assertPointAlmostEqual(transform_normalized(*p, 180), (0.8, 0.7))
        self.assertPointAlmostEqual(transform_normalized(*p, 270), (0.3, 0.8))

    def test_active_area_maps_to_screen(self):
        area = (0.1, 0.2, 0.9, 0.8)
        self.assertPointAlmostEqual(
            camera_point_to_screen(10, 20, 100, 100, area), (0.0, 0.0))
        self.assertPointAlmostEqual(
            camera_point_to_screen(90, 80, 100, 100, area), (1.0, 1.0))
        self.assertPointAlmostEqual(
            camera_point_to_screen(50, 50, 100, 100, area), (0.5, 0.5))

    def test_invalid_area(self):
        with self.assertRaises(ValueError):
            validate_area((0.9, 0.1, 0.2, 0.8))

    def test_camera_angle_validation(self):
        self.assertEqual(validate_camera_angle(0), 0.0)
        self.assertEqual(validate_camera_angle(90), 90.0)
        with self.assertRaises(ValueError):
            validate_camera_angle(-1)
        with self.assertRaises(ValueError):
            validate_camera_angle(91)

    def test_front_angle_uses_image_vertical_motion(self):
        tip = (10.0, -20.0, 50.0)
        base = (10.0, 0.0, 0.0)
        self.assertAlmostEqual(
            project_desk_normal(tip, base, 100.0, 0.0), -0.2)

    def test_top_down_angle_matches_relative_z(self):
        tip = (10.0, -20.0, -30.0)
        base = (10.0, 0.0, 0.0)
        self.assertAlmostEqual(
            project_desk_normal(tip, base, 100.0, 90.0), -0.3)

    def test_angle_blends_y_and_z(self):
        tip = (0.0, -10.0, -10.0)
        base = (0.0, 0.0, 0.0)
        self.assertAlmostEqual(
            project_desk_normal(tip, base, 100.0, 45.0),
            -(2 ** 0.5) / 10.0)

    def test_rotation_changes_physical_image_vertical_axis(self):
        self.assertEqual(oriented_vertical_delta(7, 3, 90), 7.0)
        self.assertEqual(oriented_vertical_delta(7, 3, 270), -7.0)


if __name__ == "__main__":
    unittest.main()
