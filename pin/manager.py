"""钉图窗口管理：创建、最小化全部（「连接所有钉截图」联动，P0 简版）。"""
from __future__ import annotations

from typing import List

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap

from pin.pin_window import PinWindow


class PinManager:
    def __init__(self) -> None:
        self._pins: List[PinWindow] = []
        self.link_enabled = False  # 悬浮球设置「连接所有钉截图」

    @property
    def pins(self) -> tuple:
        return tuple(self._pins)

    def create_pin(self, pixmap: QPixmap, global_pos: QPoint) -> PinWindow:
        pin = PinWindow(pixmap, global_pos)
        pin.destroyed.connect(lambda: self._forget(pin))
        self._pins.append(pin)
        pin.show()
        return pin

    def minimize_all(self) -> None:
        """一键最小化所有钉图（设置开关开启后可用）。"""
        for pin in self._pins:
            pin.showMinimized()

    def _forget(self, pin: PinWindow) -> None:
        if pin in self._pins:
            self._pins.remove(pin)
