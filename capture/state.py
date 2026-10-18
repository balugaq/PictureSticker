"""选区状态机与几何（纯逻辑，不依赖 Qt，可单元测试）。

对应 STAGE.md A4。三态：未选择 NONE / 未确定 PENDING / 已选择 SELECTED。
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Optional, Tuple

Rect = Tuple[int, int, int, int]  # (x, y, w, h)


class SelectionState(Enum):
    NONE = auto()      # 未选择
    PENDING = auto()   # 未确定（hover 检测到程序窗口）
    SELECTED = auto()  # 已选择


class Selection:
    """选区几何：移动 / 8 向缩放（边框命中）/ 屏内钳制。"""

    MIN_SIZE = 40
    EDGE_MARGIN = 7
    EDGES = ("n", "s", "e", "w", "ne", "nw", "se", "sw")

    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w <= 0 or h <= 0:
            raise ValueError(f"selection size must be positive, got {w}x{h}")
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def as_rect(self) -> Rect:
        return (self.x, self.y, self.w, self.h)

    def contains(self, px: int, py: int) -> bool:
        """点是否在选区内部（不含边框）。"""
        return self.x <= px < self.right and self.y <= py < self.bottom

    def move(self, dx: int, dy: int, bounds: Optional[Rect] = None) -> None:
        self.x += int(dx)
        self.y += int(dy)
        if bounds is not None:
            self.clamp_to(bounds)

    def clamp_to(self, bounds: Rect) -> None:
        bx, by, bw, bh = bounds
        self.w = min(self.w, bw)
        self.h = min(self.h, bh)
        self.x = max(bx, min(self.x, bx + bw - self.w))
        self.y = max(by, min(self.y, by + bh - self.h))

    def resize(
        self,
        edge: str,
        dx: int,
        dy: int,
        min_size: int = MIN_SIZE,
        bounds: Optional[Rect] = None,
    ) -> None:
        """按边/角缩放；对边锚定，尺寸不小于 min_size。"""
        if edge not in self.EDGES:
            raise ValueError(f"invalid edge: {edge!r}")
        x, y, w, h = self.x, self.y, self.w, self.h
        if "e" in edge:
            w = max(min_size, w + int(dx))
        if "s" in edge:
            h = max(min_size, h + int(dy))
        if "w" in edge:
            w = max(min_size, w - int(dx))
            x = x + (self.w - w)  # 右缘锚定
        if "n" in edge:
            h = max(min_size, h - int(dy))
            y = y + (self.h - h)  # 下缘锚定
        self.x, self.y, self.w, self.h = x, y, w, h
        if bounds is not None:
            self.clamp_to(bounds)

    def edge_at(self, px: int, py: int, margin: int = EDGE_MARGIN) -> Optional[str]:
        """点落在边框（含角）附近时返回方向，否则 None。"""
        px, py = int(px), int(py)
        n = abs(py - self.y) <= margin
        s = abs(py - self.bottom) <= margin
        w = abs(px - self.x) <= margin
        e = abs(px - self.right) <= margin
        in_x = self.x - margin <= px <= self.right + margin
        in_y = self.y - margin <= py <= self.bottom + margin
        if not (in_x and in_y):
            return None
        if n and w:
            return "nw"
        if n and e:
            return "ne"
        if s and w:
            return "sw"
        if s and e:
            return "se"
        if n:
            return "n"
        if s:
            return "s"
        if w:
            return "w"
        if e:
            return "e"
        return None


class CaptureFlow:
    """截图选区流程状态机。

    NONE --hover 程序窗口--> PENDING --单击确认--> SELECTED
    NONE/PENDING --空白拖拽--> SELECTED
    任意态 --Esc--> NONE（覆盖层随后关闭）
    """

    DRAG_MIN = 8  # 拖拽边长小于该值视为误触

    def __init__(self, screen_w: int, screen_h: int) -> None:
        if screen_w <= 0 or screen_h <= 0:
            raise ValueError("screen size must be positive")
        self._screen: Rect = (0, 0, int(screen_w), int(screen_h))
        self._state = SelectionState.NONE
        self._pending: Optional[Rect] = None
        self._selection: Optional[Selection] = None
        self._drag_origin: Optional[Tuple[int, int]] = None
        self._drag_rect: Optional[Rect] = None

    @property
    def state(self) -> SelectionState:
        return self._state

    @property
    def pending(self) -> Optional[Rect]:
        return self._pending

    @property
    def selection(self) -> Optional[Selection]:
        return self._selection if self._state is SelectionState.SELECTED else None

    @property
    def drag_rect(self) -> Optional[Rect]:
        return self._drag_rect

    # --- 未确定（hover 程序窗口） ---

    def hover_window(self, rect: Optional[Rect]) -> None:
        """rect 为屏幕坐标 (x,y,w,h)；None 表示光标下无程序窗口。仅在 NONE/PENDING 生效。"""
        if self._state is SelectionState.SELECTED:
            return
        if rect is None or rect[2] <= 0 or rect[3] <= 0:
            self._pending = None
            if self._state is SelectionState.PENDING:
                self._state = SelectionState.NONE
            return
        self._pending = self._clip(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        self._state = SelectionState.PENDING

    def confirm_pending(self) -> Optional[Selection]:
        if self._state is not SelectionState.PENDING or self._pending is None:
            return None
        x, y, w, h = self._pending
        self._selection = Selection(x, y, w, h)
        self._selection.clamp_to(self._screen)
        self._pending = None
        self._state = SelectionState.SELECTED
        return self._selection

    # --- 拖拽选区（NONE/PENDING → SELECTED） ---

    def begin_drag(self, x: int, y: int) -> bool:
        if self._state is SelectionState.SELECTED:
            return False
        self._pending = None
        self._state = SelectionState.NONE
        self._drag_origin = (int(x), int(y))
        self._drag_rect = None
        return True

    def update_drag(self, x: int, y: int) -> None:
        if self._drag_origin is None:
            return
        ox, oy = self._drag_origin
        x0, x1 = sorted((ox, int(x)))
        y0, y1 = sorted((oy, int(y)))
        self._drag_rect = (x0, y0, x1 - x0, y1 - y0)

    def finish_drag(self) -> Optional[Selection]:
        if self._drag_origin is None:
            return None
        rect, self._drag_rect, self._drag_origin = self._drag_rect, None, None
        if rect is None or rect[2] < self.DRAG_MIN or rect[3] < self.DRAG_MIN:
            return None
        x, y, w, h = rect
        # 拖出屏幕的部分裁掉（保持拖拽起点锚定）
        w = min(w, self._screen[2] - x)
        h = min(h, self._screen[3] - y)
        if w <= 0 or h <= 0:
            return None
        self._selection = Selection(x, y, w, h)
        self._selection.clamp_to(self._screen)
        self._state = SelectionState.SELECTED
        return self._selection

    # --- 确认 / 取消 ---

    def confirm(self) -> Optional[Selection]:
        """已选择态下返回选区（确认截图），否则 None。"""
        if self._state is SelectionState.SELECTED:
            return self._selection
        return None

    def cancel(self) -> None:
        self._state = SelectionState.NONE
        self._pending = None
        self._drag_origin = None
        self._drag_rect = None

    # --- 内部 ---

    def _clip(self, x: int, y: int, w: int, h: int) -> Rect:
        w = min(w, self._screen[2] - x)
        h = min(h, self._screen[3] - y)
        return (x, y, max(0, w), max(0, h))
