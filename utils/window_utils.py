# -*- coding: utf-8 -*-

# @Time   : 2024/5/12 下午5:22
# @Name   : window_utils.py
import os
import subprocess
import winreg

import win32con
import win32gui

from utils.process_utils import get_specific_process, get_wechat_path


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
