# -*- coding: utf-8 -*-
"""Click and capture the WeChat window using logical (96 DPI) coordinates."""

from __future__ import annotations

import ctypes
import sys
import time
from pathlib import Path

import uiautomation as auto
import win32con
import win32gui
from PIL import ImageGrab

ctypes.windll.shcore.SetProcessDpiAwareness(2)
auto.SetProcessDpiAwareness(auto.ProcessDpiAwareness.PerMonitorDpiAware)

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def find_wechat_window() -> int:
    candidates: list[tuple[int, int]] = []

    def callback(hwnd: int, _) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        if not win32gui.GetClassName(hwnd).startswith('Qt5'):
            return True
        if win32gui.GetWindowText(hwnd) != '微信':
            return True
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        candidates.append((hwnd, (right - left) * (bottom - top)))
        return True

    win32gui.EnumWindows(callback, None)
    if not candidates:
        raise LookupError('WeChat Qt window not found')
    return max(candidates, key=lambda item: item[1])[0]


def dpi_scale(window_handle: int) -> float:
    dpi = int(ctypes.windll.user32.GetDpiForWindow(ctypes.c_void_p(window_handle)))
    if dpi <= 0:
        raise RuntimeError(f'cannot read DPI for hwnd={window_handle}')
    return dpi / 96.0


def click_logical(window_handle: int, logical_x: int, logical_y: int) -> tuple[int, int]:
    win32gui.ShowWindow(window_handle, win32con.SW_RESTORE)
    try:
        win32gui.SetForegroundWindow(window_handle)
    except Exception:
        pass
    time.sleep(0.6)
    foreground = win32gui.GetForegroundWindow()
    print(f'foreground={foreground} target={window_handle} match={foreground == window_handle}')
    left, top, _, _ = win32gui.GetWindowRect(window_handle)
    scale = dpi_scale(window_handle)
    screen_x = left + int(logical_x * scale)
    screen_y = top + int(logical_y * scale)
    auto.Click(x=screen_x, y=screen_y)
    return screen_x, screen_y


def capture_window(window_handle: int, path: Path) -> None:
    """Capture the window area from the desktop so GPU-rendered Qt content is visible."""
    left, top, right, bottom = win32gui.GetWindowRect(window_handle)
    image = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('usage: inspect_wechat_ui.py <screenshot|click> ...')
    command = sys.argv[1]
    window_handle = find_wechat_window()
    left, top, right, bottom = win32gui.GetWindowRect(window_handle)
    scale = dpi_scale(window_handle)
    print(f'hwnd={window_handle} rect={left},{top},{right},{bottom} dpi_scale={scale:.4f}')
    if command == 'screenshot':
        output = Path(sys.argv[2])
        capture_window(window_handle, output)
        print(f'saved={output} size={output.stat().st_size}')
        return
    if command == 'click':
        logical_x = int(sys.argv[2])
        logical_y = int(sys.argv[3])
        screen_x, screen_y = click_logical(window_handle, logical_x, logical_y)
        print(f'clicked logical=({logical_x},{logical_y}) screen=({screen_x},{screen_y})')
        if len(sys.argv) > 4:
            output = Path(sys.argv[4])
            time.sleep(1.5)
            capture_window(window_handle, output)
            print(f'saved={output} size={output.stat().st_size}')
        return
    raise SystemExit(f'unknown command: {command}')


main()
