import unittest
from spotold.status import SpotStatus, NOT_DETECTED, DETECTED, MISSING, DEAD
from spotold.config import normalize, geometry, icon_name, icon_html

class SpotoldTest(unittest.TestCase):
    def test_original_lifecycle(self):
        s = SpotStatus()
        s.reset({10: True, 20: False})
        self.assertEqual(s.get(10), NOT_DETECTED)
        self.assertEqual(s.get(20), DEAD)
        self.assertEqual(s.update(10, False), MISSING)
        self.assertEqual(s.update(10, True), DETECTED)
        self.assertEqual(s.update(10, False), MISSING)
        self.assertEqual(s.kill(10), DEAD)
        self.assertIsNone(s.update(10, True))

    def test_unknown_and_reset(self):
        s = SpotStatus()
        s.reset([1])
        self.assertIsNone(s.update(999, True))
        s.reset([2])
        self.assertIsNone(s.get(1))
        self.assertEqual(s.get(2), NOT_DETECTED)

    def test_exact_icons(self):
        self.assertEqual(icon_name(NOT_DETECTED), 'missing')
        self.assertEqual(icon_name(DETECTED), 'detected')
        self.assertEqual(icon_name(MISSING), 'undetected')
        self.assertEqual(icon_name(MISSING, True), 'colorblind')
        self.assertEqual(icon_name(DEAD), '')
        self.assertIn('styles/1/detected.png', icon_html(DETECTED))

    def test_original_geometry(self):
        self.assertEqual(geometry({'align': 0})['x'], -109)
        self.assertEqual(geometry({'align': 1})['x'], 22)
        self.assertEqual(geometry({'align': 1, 'hidePrestige': True})['x'], 4)
        self.assertEqual(geometry({'align': 1, 'offsetX': 23})['x'], 45)
        self.assertEqual(normalize({'offsetX': 900})['offsetX'], 150)

if __name__ == '__main__':
    unittest.main()
