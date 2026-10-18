"""剪贴板工具。"""
from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication


def copy_pixmap(pixmap: QPixmap) -> bool:
    """把位图写入系统剪贴板（图片格式），成功返回 True。

    剥掉 DPR 元数据：粘贴出去的是完整物理像素，避免高分屏下粘出缩水图。
    """
    if pixmap is None or pixmap.isNull():
        return False
    image = pixmap.toImage()
    image.setDevicePixelRatio(1.0)
    QApplication.clipboard().setImage(image)
    return True
