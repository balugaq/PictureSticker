"""全屏截图覆盖层：桌面快照静止 + 变暗遮罩 + 选区三态 + 放大镜取色。

对应 STAGE.md A3/A4/A5（P0 主屏；多显示器坐标换算见 C6）。
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from capture.state import CaptureFlow, SelectionState
from core import win32_window
from ui import theme


class Magnifier(QWidget):
    """放大镜：像素级放大 + 蓝色十字准心 + 底部色号条（对应 DESIGN.md 2.3）。"""

    SIZE = 120
    SRC = 24   # 采样 24×24 → 约 5× 像素放大
    HEX_BAR = 20

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._image: Optional[QImage] = None
        self._src: Optional[QRect] = None
        self._hex = "#FFFFFF"

    def attach_snapshot(self, pixmap: QPixmap) -> None:
        self._image = pixmap.toImage()
        self._src = None

    def update_at(self, pos: QPoint) -> None:
        """pos 为覆盖层本地坐标；跟随光标，靠近屏幕边缘自动翻转。"""
        if self._image is None or self._image.isNull():
            return
        parent = self.parentWidget()
        # 快照是设备像素、pos 是逻辑坐标 → 换算比例（高分屏必须）
        scale = self._image.width() / max(1, parent.width())
        cx = max(0, min(round(pos.x() * scale), self._image.width() - 1))
        cy = max(0, min(round(pos.y() * scale), self._image.height() - 1))
        c = self._image.pixelColor(cx, cy)
        self._hex = c.name(QColor.HexRgb).upper()
        half = self.SRC // 2
        sx = max(0, min(cx - half, self._image.width() - self.SRC))
        sy = max(0, min(cy - half, self._image.height() - self.SRC))
        self._src = QRect(sx, sy, self.SRC, self.SRC)
        px, py = pos.x() + 22, pos.y() + 22
        if px + self.SIZE + 6 > parent.width():
            px = pos.x() - 22 - self.SIZE
        if py + self.SIZE + self.HEX_BAR + 6 > parent.height():
            py = pos.y() - 22 - self.SIZE
        self.move(px, py)
        self.show()
        self.raise_()
        self.update()

    @property
    def hex(self) -> str:
        return self._hex

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)  # 像素级
        if self._image is not None and self._src is not None:
            p.drawImage(self.rect(), self._image, self._src)
        mid = self.SIZE // 2
        p.setPen(QPen(theme.qcolor(theme.ACCENT), 2))
        # 十字准心（避开底部色号条）
        p.drawLine(mid, 8, mid, self.SIZE - self.HEX_BAR - 8)
        p.drawLine(8, mid, self.SIZE - 8, mid)
        # 边框 + 色号条
        p.drawRect(0, 0, self.SIZE - 1, self.SIZE - 1)
        p.fillRect(0, self.SIZE - self.HEX_BAR, self.SIZE, self.HEX_BAR,
                   QColor(theme.PANEL_DEEP, 224))
        p.setPen(QPen(QColor("#FFFFFF")))
        p.drawText(QRect(0, self.SIZE - self.HEX_BAR, self.SIZE, self.HEX_BAR),
                   Qt.AlignCenter, self._hex)


class CaptureOverlay(QWidget):
    """全屏覆盖层。用法：ball 隐藏后调用 start()；确认/取消后发信号并自行 stop。"""

    confirmed = Signal(QPixmap, QPoint)  # (裁剪图, 选区左上角全局坐标)
    cancelled = Signal()

    CLICK_SLOP = 6  # 按下后位移超过该值（逻辑像素）→ 判定为拖拽框选而非点击确认

    EDGE_CURSORS = {
        "n": Qt.SizeVerCursor, "s": Qt.SizeVerCursor,
        "e": Qt.SizeHorCursor, "w": Qt.SizeHorCursor,
        "ne": Qt.SizeBDiagCursor, "sw": Qt.SizeBDiagCursor,
        "nw": Qt.SizeFDiagCursor, "se": Qt.SizeFDiagCursor,
    }

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setMouseTracking(True)          # 无按键也能 hover
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)
        self._snapshot: Optional[QPixmap] = None
        self._bright: Optional[QPixmap] = None  # 选区内的高亮裁剪缓存
        self._flow: Optional[CaptureFlow] = None
        self._mode: Optional[str] = None        # 'drag' | 'move' | 'resize:<edge>' | 'click-pending'
        self._press_pos: Optional[QPoint] = None
        self._magnifier = Magnifier(self)
        self._magnifier.hide()

    # --- 生命周期 ---

    def start(self) -> None:
        """悬浮球已隐藏后调用：抓桌面快照 → 覆盖主屏。"""
        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        self._snapshot = screen.grabWindow(0)   # 先抓快照再盖上去 → 画面「静止」
        self._magnifier.attach_snapshot(self._snapshot)
        self._flow = CaptureFlow(geometry.width(), geometry.height())
        self.setGeometry(geometry)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def stop(self) -> None:
        self._magnifier.hide()
        self.hide()
        self._snapshot = None
        self._bright = None
        self._flow = None
        self._mode = None
        self._press_pos = None

    # --- 绘制 ---

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        if self._snapshot is None or self._snapshot.isNull() or self._flow is None:
            return
        # 桌面快照静止 + 全屏变暗
        p.drawPixmap(0, 0, self._snapshot)
        p.fillRect(self.rect(), theme.MASK_COLOR)
        flow = self._flow
        if flow.state is SelectionState.PENDING and flow.pending:
            self._paint_pending(p, flow.pending)
        elif flow.state is SelectionState.SELECTED and flow.selection:
            self._paint_selected(p, flow.selection)
        elif flow.drag_rect:
            # 拖拽中：与已选择态同款样式（白实线 + 上方像素尺寸），实时刷新
            x, y, w, h = flow.drag_rect
            p.setPen(QPen(Qt.white, 1))
            p.drawRect(x, y, w, h)
            dpr = self._dpr()
            self._paint_size_label(p, x, y, round(w * dpr), round(h * dpr))

    def _paint_size_label(self, p: QPainter, x: int, y: int, pw: int, ph: int) -> None:
        """选区上方的深色尺寸标签（pw/ph 为物理像素尺寸）。"""
        label = f"{pw} × {ph}"
        lw = max(110, 10 * len(label) + 20)
        ly = max(0, y - 22)
        p.fillRect(x, ly, lw, 20, QColor(theme.PANEL_DEEP, 217))
        p.setPen(QPen(QColor("#FFFFFF")))
        p.drawText(QRect(x, ly, lw, 20), Qt.AlignCenter, label)

    def _paint_pending(self, p: QPainter, rect) -> None:
        x, y, w, h = rect
        pen = QPen(theme.qcolor(theme.PENDING), 1, Qt.DashLine)
        p.setPen(pen)
        p.drawRect(x, y, w, h)
        tag_h = 18
        tag_y = max(0, y - tag_h - 2)
        p.fillRect(x, tag_y, 132, tag_h, theme.qcolor(theme.PENDING))
        p.setPen(QPen(QColor("#000000")))
        p.drawText(QRect(x, tag_y, 132, tag_h), Qt.AlignCenter, "未确定 · 点击确认")

    def _paint_selected(self, p: QPainter, sel) -> None:
        r = QRect(sel.x, sel.y, sel.w, sel.h)
        if self._bright is not None and not self._bright.isNull():
            p.drawPixmap(r.topLeft(), self._bright)  # 选区内恢复亮度（挖空遮罩）
        p.setPen(QPen(Qt.white, 1))
        p.drawRect(r)
        # 尺寸标签（物理像素）
        dpr = self._dpr()
        self._paint_size_label(p, sel.x, sel.y, round(sel.w * dpr), round(sel.h * dpr))

    def _dpr(self) -> float:
        """快照的设备像素比（高分屏下 > 1）。"""
        dpr = self._snapshot.devicePixelRatio() if self._snapshot is not None else 0.0
        return dpr if dpr > 0 else (self.devicePixelRatioF() or 1.0)

    def _crop_device_rect(self, sel) -> QRect:
        """逻辑坐标选区 → 快照设备像素区域。"""
        dpr = self._dpr()
        return QRect(round(sel.x * dpr), round(sel.y * dpr),
                     round(sel.w * dpr), round(sel.h * dpr))

    def _crop(self, sel) -> QPixmap:
        """按选区裁剪快照，保留 DPR 元数据（显示为逻辑尺寸）。"""
        crop = self._snapshot.copy(self._crop_device_rect(sel))
        crop.setDevicePixelRatio(self._dpr())
        return crop

    def _refresh_bright(self) -> None:
        sel = self._flow.selection if self._flow else None
        if sel and self._snapshot is not None:
            self._bright = self._crop(sel)
        else:
            self._bright = None

    # --- 鼠标 ---

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.button() != Qt.LeftButton or self._flow is None:
            return
        pos = e.position().toPoint()
        flow = self._flow
        if flow.state is SelectionState.SELECTED and flow.selection is not None:
            sel = flow.selection
            edge = sel.edge_at(pos.x(), pos.y())
            if edge:
                self._mode = "resize:" + edge
            elif sel.contains(pos.x(), pos.y()):
                self._mode = "move"
            else:
                # 选区外按下 → 重新拖拽
                flow.cancel()
                flow.begin_drag(pos.x(), pos.y())
                self._mode = "drag"
            self._press_pos = pos
            e.accept()
            return
        # PENDING 选区内按下：暂不确认 —— 松手未移动=单击确认；按住移动=转为框选
        if flow.state is SelectionState.PENDING and flow.pending is not None:
            x, y, w, h = flow.pending
            if x <= pos.x() < x + w and y <= pos.y() < y + h:
                self._mode = "click-pending"
                self._press_pos = pos
                e.accept()
                return
        # NONE / PENDING 空白处 → 按住拖拽框选
        if flow.begin_drag(pos.x(), pos.y()):
            self._mode = "drag"
            self._press_pos = pos
        self.update()

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        pos = e.position().toPoint()
        flow = self._flow
        if flow is None:
            return
        if self._mode is not None and self._press_pos is not None:
            if self._mode == "click-pending":
                # 按住移动超阈值 → 转为拖拽框选（否则松手时才确认）
                if (pos - self._press_pos).manhattanLength() <= self.CLICK_SLOP:
                    e.accept()
                    return
                if not flow.begin_drag(self._press_pos.x(), self._press_pos.y()):
                    self._mode = None
                    return
                self._mode = "drag"
            if self._mode == "drag":
                flow.update_drag(pos.x(), pos.y())
                self.update()  # 拖拽中实时重绘选区与尺寸
            elif flow.state is SelectionState.SELECTED and flow.selection is not None:
                dx = pos.x() - self._press_pos.x()
                dy = pos.y() - self._press_pos.y()
                sel = flow.selection
                if self._mode == "move":
                    sel.move(dx, dy, bounds=(0, 0, self.width(), self.height()))
                    self._press_pos = pos
                elif self._mode.startswith("resize:"):
                    edge = self._mode.split(":", 1)[1]
                    sel.resize(edge, dx, dy, bounds=(0, 0, self.width(), self.height()))
                    self._press_pos = pos
                    self._refresh_bright()
                    self._magnifier.update_at(pos)  # 缩放时放大镜跟随
                self.update()
            e.accept()
            return
        # 无按键：SELECTED → 边框光标；NONE/PENDING → hover 程序窗口检测
        if flow.state is SelectionState.SELECTED and flow.selection is not None:
            edge = flow.selection.edge_at(pos.x(), pos.y())
            self.setCursor(self.EDGE_CURSORS[edge] if edge else Qt.ArrowCursor)
        elif flow.state in (SelectionState.NONE, SelectionState.PENDING):
            g = self.mapToGlobal(pos)
            rect = win32_window.window_rect_at(g.x(), g.y())
            if rect is not None:
                # Win32 GetWindowRect 返回物理像素 → 逻辑坐标（高分屏换算）
                dpr = self.devicePixelRatioF() or 1.0
                gx, gy = self.geometry().x(), self.geometry().y()
                rect = (round((rect[0] - gx) / dpr), round((rect[1] - gy) / dpr),
                        max(1, round(rect[2] / dpr)), max(1, round(rect[3] / dpr)))
            flow.hover_window(rect)
            self.update()

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() != Qt.LeftButton:
            return
        if self._flow is not None and self._mode is not None:
            if self._mode == "drag":
                self._flow.finish_drag()
                self._refresh_bright()
            elif self._mode == "click-pending":
                if self._flow.confirm_pending() is not None:  # 松手未移动 → 单击确认
                    self._refresh_bright()
        self._mode = None
        self._press_pos = None
        self._magnifier.hide()
        self.update()

    def mouseDoubleClickEvent(self, e) -> None:  # noqa: N802
        if self._flow is not None and self._flow.state is SelectionState.SELECTED:
            self._finish(cancel=False)

    def wheelEvent(self, e) -> None:  # noqa: N802
        # SELECTED 态下 Ctrl+滚轮 等比缩放选区（以中心为锚）
        if self._flow is None or not (e.modifiers() & Qt.ControlModifier):
            e.ignore()
            return
        sel = self._flow.selection
        if sel is None or self._flow.state is not SelectionState.SELECTED:
            return
        factor = 1.1 if e.angleDelta().y() > 0 else 1 / 1.1
        dw = int(sel.w * factor) - sel.w
        dh = int(sel.h * factor) - sel.h
        cx, cy = sel.x + sel.w // 2, sel.y + sel.h // 2
        sel.resize("se", dw, dh)
        sel.move(cx - sel.w // 2 - sel.x, cy - sel.h // 2 - sel.y,
                 bounds=(0, 0, self.width(), self.height()))
        self._refresh_bright()
        self.update()
        e.accept()

    # --- 键盘 ---

    def keyPressEvent(self, e) -> None:  # noqa: N802
        key = e.key()
        if key == Qt.Key_Escape:
            self._finish(cancel=True)
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self._finish(cancel=False)
        elif key == Qt.Key_C and self._magnifier.isVisible():
            QGuiApplication.clipboard().setText(self._magnifier.hex)  # 复制色号
        else:
            super().keyPressEvent(e)

    # --- 收尾 ---

    def _finish(self, cancel: bool) -> None:
        flow = self._flow
        if flow is None:
            return
        if cancel:
            flow.cancel()
            self.cancelled.emit()
            self.stop()
            return
        sel = flow.confirm()
        if sel is None or self._snapshot is None:
            return
        crop = self._crop(sel)
        top_left = self.mapToGlobal(QPoint(sel.x, sel.y))
        self.confirmed.emit(crop, top_left)
        self.stop()
