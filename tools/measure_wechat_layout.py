# -*- coding: utf-8 -*-
"""Measure WeChat window geometry and DPI on the interactive desktop."""

from __future__ import annotations

import ctypes
import json
import sys
from pathlib import Path

import win32gui
import win32process

OUTPUT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r'E:\project\WeChatMassTool\.tmp\wechat_layout.json')


def enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()


def window_dpi(window_handle: int) -> int:
    try:
        get_dpi_for_window = ctypes.windll.user32.GetDpiForWindow
    except AttributeError:
        return 0
    get_dpi_for_window.argtypes = [ctypes.c_void_p]
    get_dpi_for_window.restype = ctypes.c_uint
    return int(get_dpi_for_window(ctypes.c_void_p(window_handle)))


def main() -> None:
    enable_dpi_awareness()
    rows = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        class_name = win32gui.GetClassName(hwnd)
        if not class_name.startswith('Qt5'):
            return True
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        if (right - left) < 300 or (bottom - top) < 200:
            return True
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        rows.append({
            'hwnd': hwnd,
            'process_id': process_id,
            'class_name': class_name,
            'title': win32gui.GetWindowText(hwnd),
            'rect': [left, top, right, bottom],
            'width': right - left,
            'height': bottom - top,
            'dpi': window_dpi(hwnd),
            'iconic': bool(win32gui.IsIconic(hwnd)),
            'maximized': bool(win32gui.GetWindowLong(hwnd, -16) & 0x01000000),
            'foreground': win32gui.GetForegroundWindow() == hwnd
        })
        return True

    win32gui.EnumWindows(callback, None)
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    payload = {
        'screen': [screen_width, screen_height],
        'system_dpi': window_dpi(win32gui.GetDesktopWindow()),
        'windows': rows
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {OUTPUT_PATH}')


main()
