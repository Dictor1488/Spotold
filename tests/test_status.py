import unittest
from spotold.status import SpotStatus, NEVER_SEEN, VISIBLE, LOST
from spotold.config import normalize, icon_name

class SpotoldTest(unittest.TestCase):
    def test_lifecycle(self):
        s = SpotStatus()
        s.reset([10, 20])
        self.assertEqual(s.get(10), NEVER_SEEN)
        self.assertIsNone(s.update(10, False))
        self.assertEqual(s.update(10, True), VISIBLE)
        self.assertIsNone(s.update(10, True))
        self.assertEqual(s.update(10, False), LOST)
        self.assertIsNone(s.update(10, False))
        self.assertEqual(s.update(10, True), VISIBLE)
        s.reset([30])
        self.assertIsNone(s.get(10))
        self.assertEqual(s.get(30), NEVER_SEEN)

    def test_unknown_unit(self):
        s = SpotStatus()
        s.reset([1])
        self.assertIsNone(s.update(999, True))

    def test_config(self):
        self.assertEqual(normalize({'indicatorStyle': 1, 'align': 'right', 'offsetX': 500})['offsetX'], 250)
        self.assertEqual(icon_name(VISIBLE, True), 'colorblind.png')
        self.assertEqual(icon_name(LOST), 'missing.png')

if __name__ == '__main__':
    unittest.main()
