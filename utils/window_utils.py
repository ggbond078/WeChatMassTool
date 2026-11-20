# -*- coding: utf-8 -*-

# @Time   : 2024/5/12 下午5:22
# @Name   : window_utils.py
import ctypes
import os
import subprocess
import winreg
from ctypes import wintypes

import win32con
import win32gui

from utils.process_utils import get_specific_process, get_wechat_path


LOGPIXELSX = 88
MONITOR_DEFAULTTONEAREST = 2
MDT_EFFECTIVE_DPI = 0


def _get_window_dpi(window_handle: int) -> int:
    """Read the window DPI via GetDpiForWindow when the system provides it."""
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    try:
        get_dpi_for_window = user32.GetDpiForWindow
    except AttributeError:
        return 0
    get_dpi_for_window.argtypes = [wintypes.HWND]
    get_dpi_for_window.restype = wintypes.UINT
    return int(get_dpi_for_window(wintypes.HWND(window_handle)))


def _get_device_dpi(window_handle: int) -> int:
    """Read the device DPI from a window device context."""
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.ReleaseDC.restype = ctypes.c_int
    gdi32.GetDeviceCaps.argtypes = [wintypes.HDC, ctypes.c_int]
    gdi32.GetDeviceCaps.restype = ctypes.c_int

    device_context = user32.GetDC(wintypes.HWND(window_handle))
    if not device_context:
        return 0
    try:
        return int(gdi32.GetDeviceCaps(device_context, LOGPIXELSX))
    finally:
        user32.ReleaseDC(wintypes.HWND(window_handle), device_context)


def _get_monitor_dpi(window_handle: int) -> int:
    """Read the effective monitor DPI via shcore, available since Windows 8.1."""
    try:
        shcore = ctypes.WinDLL('shcore', use_last_error=True)
    except OSError:
        return 0
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HMONITOR
    shcore.GetDpiForMonitor.argtypes = [
        wintypes.HMONITOR,
        ctypes.c_int,
        ctypes.POINTER(wintypes.UINT),
        ctypes.POINTER(wintypes.UINT)
    ]
    shcore.GetDpiForMonitor.restype = ctypes.c_long

    monitor = user32.MonitorFromWindow(wintypes.HWND(window_handle), MONITOR_DEFAULTTONEAREST)
    if not monitor:
        return 0
    dpi_x = wintypes.UINT()
    dpi_y = wintypes.UINT()
    result = shcore.GetDpiForMonitor(monitor, MDT_EFFECTIVE_DPI, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
    if result != 0:
        return 0
    return int(dpi_x.value)


def get_window_dpi_scale(window_handle: int) -> float:
    """
    Return the DPI scale of a window.

    GetDpiForWindow requires Windows 10 1607 or later, so fall back to the
    monitor DPI on Windows 8.1/10 1507 and to the device context afterwards.
    """
    dpi = _get_window_dpi(window_handle)
    if dpi <= 0:
        dpi = _get_monitor_dpi(window_handle)
    if dpi <= 0:
        dpi = _get_device_dpi(window_handle)
    if dpi <= 0:
        raise RuntimeError(f'无法获取窗口 DPI 缩放: hwnd={window_handle}')
    return dpi / 96


def find_visible_window(
        window_name: str,
        window_class_name: str,
        class_name_prefix: str
) -> int:
    """
    Find the largest visible top-level window matching a title and class.

    WeChat creates smaller helper windows with the same title, so prefer the
    largest matching window.
    """
    candidates = list()

    def collect(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        if win32gui.GetWindowText(hwnd) != window_name:
            return True
        class_name = win32gui.GetClassName(hwnd)
        if class_name != window_class_name and not class_name.startswith(class_name_prefix):
            return True
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        candidates.append((hwnd, (right - left) * (bottom - top)))
        return True

    win32gui.EnumWindows(collect, None)
    if not candidates:
        return 0
    return max(candidates, key=lambda item: item[1])[0]


def find_wechat_window(
        window_name: str,
        window_class_name: str,
        qt_class_name_prefix: str
) -> int:
    """Find the visible WeChat main window."""
    return find_visible_window(
        window_name=window_name,
        window_class_name=window_class_name,
        class_name_prefix=qt_class_name_prefix
    )


def minimize_wechat(class_name, name):
    """
    关闭Windows窗口

    Args:
        name(str):  进程名
        class_name(str):  进程class_name

    Returns:

    """
    hwnd = win32gui.FindWindow(class_name, name)
    if win32gui.IsWindowVisible(hwnd):
        win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)


def wake_up_window(process_name: str = 'Weixin.exe') -> bool:
    if get_specific_process(proc_name=process_name):
        return True

    # Get the executable path from the running process first because installation paths vary by machine.
    if exe_path := get_wechat_path(proc_name=process_name):
        subprocess.Popen(exe_path)
        return True

    # Fall back to the registry if WeChat is not running yet.
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Weixin"
        )
        path, _ = winreg.QueryValueEx(key, "InstallLocation")
        winreg.CloseKey(key)
        exe_path = os.path.join(path, process_name)
        if os.path.exists(exe_path):
            subprocess.Popen(exe_path)
            return True

    except FileNotFoundError as error:
        raise FileNotFoundError(f"WeChat executable not found: process_name={process_name}") from error

    return False
