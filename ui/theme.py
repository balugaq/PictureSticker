"""设计令牌唯一定义（对应 DESIGN.md 第 1 节）。组件一律引用此处，禁止硬编码色值。"""
from __future__ import annotations

from PySide6.QtGui import QColor

# --- 基础面板色 ---
PANEL_DEEP = "#1C1C1E"        # 工具条/尺寸标签
PANEL = "#2C2C2E"             # 悬浮球/二级面板/菜单
PANEL_SOLID = "#232325"       # seg 底槽/输入框
HOVER = "#3A3A3C"             # hover 背景/钉图默认边框
BORDER = "#48484A"            # 面板边框/滑块槽
DIVIDER = "#38383A"           # 分割线
TEXT = "#E5E5EA"              # 正文
TEXT_SECONDARY = "#8E8E93"    # 次要文字
ACCENT = "#0A84FF"            # 强调/激活
ACCENT_PIN = "#64D2FF"        # 钉图选中边框
SUCCESS = "#34C759"           # 确认 ✓
DANGER = "#FF3B30"            # 取消 ✕ / 危险项
PENDING = "#FFD60A"           # 未确定待定选区（虚线）

# --- 遮罩 ---
MASK_ALPHA = 115              # #000 45%
MASK_COLOR = QColor(0, 0, 0, MASK_ALPHA)

# --- 标记色板（形状/箭头/画笔/文本共用，默认红） ---
MARKER_COLORS = ("#FF3B30", "#FFCC00", "#34C759", "#0A84FF", "#FFFFFF", "#8E8E93")
DEFAULT_MARKER = "#FF3B30"

# --- 几何常量 ---
RADIUS_PANEL = 8              # 面板圆角
RADIUS_BTN = 6                # 按钮圆角
EDGE_MARGIN = 7               # 选区边框命中（与 capture.state.Selection.EDGE_MARGIN 一致）
MIN_SIZE = 40                 # 选区最小尺寸


def qcolor(name: str, alpha: int = 255) -> QColor:
    """十六进制色 → QColor（可带透明度）。"""
    c = QColor(name)
    c.setAlpha(alpha)
    return c
