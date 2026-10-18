"""Selection 几何单元测试（纯逻辑，无 Qt 依赖）。运行：python -m unittest discover -s tests"""
import unittest

from capture.state import Selection


class TestSelectionInit(unittest.TestCase):
    def test_ok(self):
        s = Selection(3, 4, 50, 60)
        self.assertEqual((s.x, s.y, s.w, s.h), (3, 4, 50, 60))
        self.assertEqual(s.right, 53)
        self.assertEqual(s.bottom, 64)
        self.assertEqual(s.as_rect(), (3, 4, 50, 60))

    def test_invalid_size_raises(self):
        with self.assertRaises(ValueError):
            Selection(0, 0, 0, 10)
        with self.assertRaises(ValueError):
            Selection(0, 0, 10, -1)


class TestSelectionContains(unittest.TestCase):
    def test_inside_and_border(self):
        s = Selection(10, 10, 50, 50)
        self.assertTrue(s.contains(10, 10))
        self.assertTrue(s.contains(59, 59))
        self.assertFalse(s.contains(60, 60))  # 右下边界外
        self.assertFalse(s.contains(9, 30))


class TestSelectionMove(unittest.TestCase):
    def test_free_move(self):
        s = Selection(10, 10, 50, 50)
        s.move(5, -5)
        self.assertEqual(s.as_rect(), (15, 5, 50, 50))

    def test_move_clamped(self):
        s = Selection(0, 0, 50, 50)
        s.move(-10, -10, bounds=(0, 0, 200, 200))
        self.assertEqual((s.x, s.y), (0, 0))
        s.move(1000, 1000, bounds=(0, 0, 200, 200))
        self.assertEqual((s.x, s.y), (150, 150))

    def test_clamp_shrinks_oversize(self):
        s = Selection(0, 0, 200, 50)
        s.clamp_to((0, 0, 100, 100))
        self.assertEqual(s.w, 100)
        self.assertEqual((s.x, s.y, s.h), (0, 0, 50))


class TestSelectionResize(unittest.TestCase):
    def test_east_grows(self):
        s = Selection(10, 10, 50, 50)
        s.resize("e", 30, 0)
        self.assertEqual(s.as_rect(), (10, 10, 80, 50))

    def test_south_grows(self):
        s = Selection(10, 10, 50, 50)
        s.resize("s", 0, 20)
        self.assertEqual(s.as_rect(), (10, 10, 50, 70))

    def test_west_anchors_right(self):
        s = Selection(10, 10, 50, 50)
        s.resize("w", 5, 0)
        self.assertEqual(s.as_rect(), (15, 10, 45, 50))  # 右缘 60 不动

    def test_north_anchors_bottom(self):
        s = Selection(10, 10, 50, 50)
        s.resize("n", 0, 5)
        self.assertEqual(s.as_rect(), (10, 15, 50, 45))  # 下缘 60 不动

    def test_west_min_size(self):
        s = Selection(10, 10, 50, 50)
        s.resize("w", 100, 0)
        self.assertEqual((s.x, s.w), (20, 40))  # 最小 40，右缘 60 固定

    def test_north_min_size(self):
        s = Selection(10, 10, 50, 50)
        s.resize("n", 0, 100)
        self.assertEqual((s.y, s.h), (20, 40))

    def test_corner_ne(self):
        s = Selection(10, 10, 50, 50)
        s.resize("ne", 20, -10)
        self.assertEqual(s.as_rect(), (10, 0, 70, 60))

    def test_corner_sw(self):
        s = Selection(10, 10, 50, 50)
        s.resize("sw", -15, 25)
        # w = max(40, 50-(-15)) = 65, x = 10 + (50-65) = -5; h = max(40, 50+25) = 75
        self.assertEqual(s.as_rect(), (-5, 10, 65, 75))

    def test_invalid_edge_raises(self):
        s = Selection(0, 0, 10, 10)
        with self.assertRaises(ValueError):
            s.resize("x", 1, 1)


class TestEdgeAt(unittest.TestCase):
    def setUp(self):
        self.s = Selection(0, 0, 100, 100)

    def test_center_none(self):
        self.assertIsNone(self.s.edge_at(50, 50))

    def test_corners(self):
        self.assertEqual(self.s.edge_at(0, 0), "nw")
        self.assertEqual(self.s.edge_at(100, 100), "se")
        self.assertEqual(self.s.edge_at(100, 0), "ne")
        self.assertEqual(self.s.edge_at(0, 100), "sw")

    def test_edges(self):
        self.assertEqual(self.s.edge_at(50, 0), "n")
        self.assertEqual(self.s.edge_at(50, 100), "s")
        self.assertEqual(self.s.edge_at(0, 50), "w")
        self.assertEqual(self.s.edge_at(100, 50), "e")

    def test_margin_boundary(self):
        s = Selection(100, 100, 50, 50)
        self.assertEqual(s.edge_at(93, 120), "w")    # 左缘 -7 命中
        self.assertIsNone(s.edge_at(92, 120))        # -8 超出命中区
        self.assertEqual(s.edge_at(120, 157), "s")   # 下缘 +7 命中

    def test_far_outside_none(self):
        s = Selection(50, 50, 100, 100)
        self.assertIsNone(s.edge_at(0, 0))
        self.assertIsNone(self.s.edge_at(200, 50))   # 右侧远点（本选区右缘 100）


if __name__ == "__main__":
    unittest.main()
