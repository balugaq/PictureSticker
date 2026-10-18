"""钉图窗口（P0 最小版：拖动 / 滚轮缩放 / Ctrl+左键选中边框 / 双击关闭）。

完整交互（右键菜单/hover tip/绑定分组）见 STAGE.md B7/B8。
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from ui import theme


class PinWindow(QWidget):
    MIN_SCALE = 0.2
    MAX_SCALE = 5.0
    SCALE_STEP = 1.21  # 滚轮灵敏度（1.1 基准 × 1.1，主人要求 +10%）
    SCALE_TIP_MS = 3000

    def __init__(self, pixmap: QPixmap, global_pos: QPoint) -> None:
        # Qt.Window（非 Tool）：每张钉图在任务栏有自己的按钮
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowTitle("钉图")
        self._pixmap = pixmap
        self._scale = 1.0
        self._selected = False
        self._drag_offset: Optional[QPoint] = None
        self._scale_text: Optional[str] = None  # 左上角缩放百分比（3 秒自动消失）
        self._scale_timer = QTimer(self)
        self._scale_timer.setSingleShot(True)
        self._scale_timer.timeout.connect(self._hide_scale)
        self.setFixedSize(pixmap.size())
        self.move(global_pos)
        self.setCursor(Qt.OpenHandCursor)

    @property
    def selected(self) -> bool:
        return self._selected

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        p.drawPixmap(self.rect(), self._pixmap)
        pen_color = theme.ACCENT_PIN if self._selected else theme.HOVER
        p.setPen(QPen(theme.qcolor(pen_color), 2 if self._selected else 1))
        p.drawRect(0, 0, self.width() - 1, self.height() - 1)
        if self._scale_text:
            # 左上角：相对原图的缩放百分比（缩放后显示 3 秒）
            p.fillRect(0, 0, 68, 22, QColor(theme.PANEL_DEEP, 217))
            p.setPen(QPen(QColor("#FFFFFF")))
            p.drawText(self.rect().adjusted(0, 0, -(self.width() - 68), -(self.height() - 22)),
                       Qt.AlignCenter, self._scale_text)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.modifiers() & Qt.ControlModifier and e.button() == Qt.LeftButton:
            self._selected = not self._selected  # Ctrl+左键 选中（边框浅蓝）
            self.update()
            e.accept()
            return
        if e.button() == Qt.LeftButton:
            self._drag_offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        if self._drag_offset is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        self._drag_offset = None
        self.setCursor(Qt.OpenHandCursor)

    def wheelEvent(self, e) -> None:  # noqa: N802
        factor = PinWindow.SCALE_STEP if e.angleDelta().y() > 0 else 1 / PinWindow.SCALE_STEP
        new_scale = max(self.MIN_SCALE, min(self.MAX_SCALE, self._scale * factor))
        if new_scale != self._scale:
            self._scale = new_scale
            self.setFixedSize(self._pixmap.size() * self._scale)
            self._scale_text = f"{round(self._scale * 100)}%"  # 相对原图
            self._scale_timer.start(self.SCALE_TIP_MS)
            self.update()
        e.accept()

    def _hide_scale(self) -> None:
        self._scale_text = None
        self.update()

    def mouseDoubleClickEvent(self, e) -> None:  # noqa: N802
        self.close()  # P0 临时退出方式；右键菜单体系见 B7/B8
