"""CaptureFlow 状态机单元测试（纯逻辑，无 Qt 依赖）。"""
import unittest

from capture.state import CaptureFlow, SelectionState


class TestCaptureFlow(unittest.TestCase):
    def setUp(self):
        self.f = CaptureFlow(800, 600)

    def _select_by_drag(self):
        self.assertTrue(self.f.begin_drag(10, 10))
        self.f.update_drag(110, 110)
        self.assertIsNotNone(self.f.finish_drag())
        self.assertIs(self.f.state, SelectionState.SELECTED)

    # --- 初始 ---

    def test_initial(self):
        self.assertIs(self.f.state, SelectionState.NONE)
        self.assertIsNone(self.f.selection)
        self.assertIsNone(self.f.pending)
        self.assertIsNone(self.f.drag_rect)

    def test_invalid_screen_raises(self):
        with self.assertRaises(ValueError):
            CaptureFlow(0, 600)
        with self.assertRaises(ValueError):
            CaptureFlow(800, 0)

    # --- PENDING：hover 程序窗口 ---

    def test_hover_sets_pending(self):
        self.f.hover_window((10, 10, 200, 100))
        self.assertIs(self.f.state, SelectionState.PENDING)
        self.assertEqual(self.f.pending, (10, 10, 200, 100))

    def test_hover_none_returns_to_none(self):
        self.f.hover_window((10, 10, 200, 100))
        self.f.hover_window(None)
        self.assertIs(self.f.state, SelectionState.NONE)
        self.assertIsNone(self.f.pending)

    def test_hover_invalid_rect_ignored(self):
        self.f.hover_window((0, 0, 0, 0))
        self.assertIs(self.f.state, SelectionState.NONE)

    def test_hover_clipped_to_screen(self):
        self.f.hover_window((700, 500, 400, 300))
        self.assertEqual(self.f.pending, (700, 500, 100, 100))

    def test_hover_ignored_when_selected(self):
        self._select_by_drag()
        self.f.hover_window((0, 0, 100, 100))
        self.assertIs(self.f.state, SelectionState.SELECTED)
        self.assertIsNone(self.f.pending)

    def test_confirm_pending(self):
        self.f.hover_window((10, 10, 200, 100))
        sel = self.f.confirm_pending()
        self.assertIsNotNone(sel)
        self.assertEqual(sel.as_rect(), (10, 10, 200, 100))
        self.assertIs(self.f.state, SelectionState.SELECTED)
        self.assertIsNone(self.f.pending)
        self.assertIs(self.f.confirm(), sel)

    def test_confirm_pending_in_none_returns_none(self):
        self.assertIsNone(self.f.confirm_pending())

    # --- 拖拽选区 ---

    def test_begin_drag_blocked_when_selected(self):
        self._select_by_drag()
        self.assertFalse(self.f.begin_drag(0, 0))

    def test_begin_drag_from_pending_resets(self):
        self.f.hover_window((10, 10, 200, 100))
        self.assertTrue(self.f.begin_drag(5, 5))
        self.assertIs(self.f.state, SelectionState.NONE)
        self.assertIsNone(self.f.pending)

    def test_drag_updates_rect_normalized(self):
        self.f.begin_drag(100, 100)
        self.f.update_drag(40, 160)
        self.assertEqual(self.f.drag_rect, (40, 100, 60, 60))

    def test_drag_too_small_ignored(self):
        self.assertTrue(self.f.begin_drag(100, 100))
        self.f.update_drag(104, 103)
        self.assertIsNone(self.f.finish_drag())
        self.assertIs(self.f.state, SelectionState.NONE)
        self.assertIsNone(self.f.selection)

    def test_drag_ok_selects(self):
        self.assertTrue(self.f.begin_drag(100, 100))
        self.f.update_drag(40, 160)
        sel = self.f.finish_drag()
        self.assertEqual(sel.as_rect(), (40, 100, 60, 60))
        self.assertIs(self.f.state, SelectionState.SELECTED)
        self.assertIs(self.f.selection, sel)

    def test_drag_clipped_to_screen(self):
        self.f.begin_drag(700, 500)
        self.f.update_drag(1000, 900)
        sel = self.f.finish_drag()
        self.assertEqual(sel.as_rect(), (700, 500, 100, 100))

    def test_finish_without_drag_returns_none(self):
        self.assertIsNone(self.f.finish_drag())

    # --- 确认 / 取消 ---

    def test_confirm_only_when_selected(self):
        self.assertIsNone(self.f.confirm())
        self.f.hover_window((0, 0, 50, 50))
        self.assertIsNone(self.f.confirm())

    def test_cancel_resets(self):
        self._select_by_drag()
        self.f.cancel()
        self.assertIs(self.f.state, SelectionState.NONE)
        self.assertIsNone(self.f.selection)
        self.assertIsNone(self.f.confirm())
        # 取消后可重新拖拽
        self.assertTrue(self.f.begin_drag(0, 0))


if __name__ == "__main__":
    unittest.main()
