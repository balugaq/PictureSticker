"""桌面悬浮球 + 设置面板（对应 DESIGN.md 2.1/2.2，STAGE.md A1/A2）。"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (QCheckBox, QLabel, QPushButton, QVBoxLayout, QWidget)

from core.clipboard import copy_pixmap
from pin.manager import PinManager
from ui import theme


class SettingsPopup(QWidget):
    """悬浮球设置面板：连接所有钉截图开关 + 一键最小化。"""

    def __init__(self, pin_manager: PinManager) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(250)
        self._switch = QCheckBox("连接所有钉截图")
        desc = QLabel("开启后所有钉图加入同一分组，可一键最小化；呼出时同组一起到前台。")
        desc.setWordWrap(True)
        self._btn_min = QPushButton("一键最小化所有钉图")
        self._btn_min.setEnabled(False)
        self._switch.toggled.connect(self._btn_min.setEnabled)
        self._btn_min.clicked.connect(pin_manager.minimize_all)
        self._switch.toggled.connect(self._on_link_toggled)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.addWidget(self._switch)
        lay.addWidget(desc)
        lay.addWidget(self._btn_min)
        self.setStyleSheet(
            f"QWidget {{ background: {theme.PANEL}; color: {theme.TEXT}; font-size: 12px; }}"
            f"QCheckBox {{ spacing: 8px; }}"
            f"QLabel {{ color: {theme.TEXT_SECONDARY}; }}"
            f"QPushButton {{ background: {theme.ACCENT}; color: #FFFFFF; border: none;"
            f" border-radius: {theme.RADIUS_BTN}px; padding: 6px; }}"
            f"QPushButton:disabled {{ background: {theme.HOVER}; color: {theme.TEXT_SECONDARY}; }}"
        )

    def _on_link_toggled(self, on: bool) -> None:
        # 通知 manager（P0： PinManager.link_enabled 由 ball 侧同步）
        self._link_callback(on)

    _link_callback = None  # type: ignore[var-annotated]

    def set_link_callback(self, cb) -> None:
        self._link_callback = cb


class FloatingBall(QWidget):
    """圆形悬浮球：截图 / 设置；按住球体拖动。"""

    def __init__(self) -> None:
        # Qt.Window（非 Tool）：任务栏显示「PictureSticker」按钮
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowTitle("PictureSticker")
        self.setFixedSize(76, 76)
        self._drag_pos: Optional[QPoint] = None
        self._overlay = None  # 延迟创建（避免循环引用）

        self.pin_manager = PinManager()
        self._settings = SettingsPopup(self.pin_manager)
        self._settings.set_link_callback(lambda on: setattr(self.pin_manager, "link_enabled", on))
        self._settings.hide()

        btn_cap = QPushButton("✂ 截图")
        btn_cfg = QPushButton("⚙ 设置")
        for b in (btn_cap, btn_cfg):
            b.setFixedSize(64, 24)
            b.setCursor(Qt.PointingHandCursor)
        btn_cap.clicked.connect(self._start_capture)
        btn_cfg.clicked.connect(self._toggle_settings)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch(1)
        lay.addWidget(btn_cap, 0, Qt.AlignCenter)
        lay.addWidget(btn_cfg, 0, Qt.AlignCenter)
        lay.addStretch(1)
        self.setStyleSheet(
            "QWidget { background: transparent; }"
            f"QPushButton {{ background: transparent; color: #FFFFFF; border: none;"
            f" border-radius: {theme.RADIUS_BTN}px; font-size: 13px; }}"
            f"QPushButton:hover {{ background: {theme.HOVER}; }}"
        )

    # --- 悬浮球外观（圆形） ---

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(QPen(theme.qcolor(theme.BORDER), 1))
        p.setBrush(theme.qcolor(theme.PANEL, 230))  # #2C2C2E @ 90%
        p.drawEllipse(self.rect().adjusted(0, 0, -1, -1))

    # --- 拖动 ---

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        if self._drag_pos is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        self._drag_pos = None

    # --- 截图 / 设置 ---

    def _start_capture(self) -> None:
        from capture.overlay import CaptureOverlay  # 局部导入避免循环引用

        if self._overlay is None:
            self._overlay = CaptureOverlay()
            self._overlay.confirmed.connect(self._on_captured)
            self._overlay.cancelled.connect(self.show)
        self._settings.hide()
        self.hide()          # 隐藏自身后截图
        self._overlay.start()

    def _toggle_settings(self) -> None:
        if self._settings.isVisible():
            self._settings.hide()
            return
        g = self.frameGeometry()
        self._settings.adjustSize()
        self._settings.move(g.left() - self._settings.width() - 10, g.top())
        self._settings.show()
        self._settings.raise_()

    def _on_captured(self, pixmap, top_left) -> None:
        copy_pixmap(pixmap)                               # A5：进剪贴板
        self.pin_manager.create_pin(pixmap, top_left)     # A5：原地生成钉图
        self.show()
