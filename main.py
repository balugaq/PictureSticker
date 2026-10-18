"""PictureSticker 入口：启动桌面悬浮球（STAGE.md A1）。"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from ball.ball import FloatingBall
from ui import theme


def _base_dir() -> Path:
    """资源目录：源码运行 = 项目根；PyInstaller 冻结后 = 解包目录。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def _setup_tray(app: QApplication) -> QSystemTrayIcon:
    """系统托盘：后台常驻图标，右键「彻底退出」。"""
    tray = QSystemTrayIcon(QIcon(str(_base_dir() / "favicon.png")))
    tray.setToolTip("PictureSticker")
    menu = QMenu()
    menu.setStyleSheet(
        f"QMenu {{ background: {theme.PANEL}; color: {theme.TEXT}; border: 1px solid {theme.BORDER}; }}"
        f"QMenu::item {{ padding: 6px 24px; }}"
        f"QMenu::item:selected {{ background: {theme.ACCENT}; color: #FFFFFF; }}"
    )
    act_quit = QAction("彻底退出", menu)
    act_quit.triggered.connect(lambda: (tray.hide(), app.quit()))
    menu.addAction(act_quit)
    tray.setContextMenu(menu)
    tray.show()
    return tray


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PictureSticker")
    app.setApplicationDisplayName("PictureSticker")
    icon_file = next((f for f in ("favicon.png", "favicon.ico")
                      if (_base_dir() / f).exists()), None)
    if icon_file:
        app.setWindowIcon(QIcon(str(_base_dir() / icon_file)))  # 任务栏/窗口/托盘图标
    app.setQuitOnLastWindowClosed(False)  # 后台常驻：关窗口不退出，从托盘彻底退出

    ball = FloatingBall()
    ball.show()

    tray = _setup_tray(app)  # 常驻引用，防 GC
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
