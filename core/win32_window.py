"""Win32 窗口检测：hover 时获取光标下可见顶层窗口矩形（屏幕坐标）。

pywin32 缺失时优雅降级（返回 None，拖拽选区仍可用）。
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

Rect = Tuple[int, int, int, int]  # (x, y, w, h)

try:
    import win32gui
    import win32process
except ImportError:  # 未装 pywin32 时降级
    win32gui = None  # type: ignore[assignment]


def window_rect_at(px: int, py: int) -> Optional[Rect]:
    """返回包含点 (px, py) 的最上层可见顶层窗口（跳过本进程窗口）；找不到返回 None。"""
    if win32gui is None:
        return None
    result: list[Rect] = []

    def _cb(hwnd: int, _unused: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
            return True
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == os.getpid():
                return True  # 跳过覆盖层等本进程窗口
        except Exception:
            pass
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        if r <= l or b <= t:
            return True
        if l <= px < r and t <= py < b:
            result.append((l, t, r - l, b - t))
            return False  # EnumWindows 按 Z 序枚举，首个命中即最上层
        return True

    try:
        win32gui.EnumWindows(_cb, None)
    except Exception:
        # 命中时 EnumWindows 以 error 中断枚举，属预期路径
        pass
    return result[0] if result else None
