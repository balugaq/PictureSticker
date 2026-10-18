"""PictureSticker 入口：启动桌面悬浮球（STAGE.md A1）。"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ball.ball import FloatingBall


def _base_dir() -> Path:
    """资源目录：源码运行 = 项目根；PyInstaller 冻结后 = 解包目录。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PictureSticker")
    app.setApplicationDisplayName("PictureSticker")
    app.setWindowIcon(QIcon(str(_base_dir() / "favicon.png")))  # 任务栏/窗口图标
    app.setQuitOnLastWindowClosed(False)  # 悬浮球常驻（Qt.Tool 窗口不计入关闭判定）
    ball = FloatingBall()
    ball.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
