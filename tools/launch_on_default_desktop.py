# -*- coding: utf-8 -*-
"""Launch a program on the interactive WinSta0\\Default desktop."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

STARTF_USESHOWWINDOW = 0x00000001
SW_SHOWNORMAL = 1


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('lpReserved', wintypes.LPWSTR),
        ('lpDesktop', wintypes.LPWSTR),
        ('lpTitle', wintypes.LPWSTR),
        ('dwX', wintypes.DWORD),
        ('dwY', wintypes.DWORD),
        ('dwXSize', wintypes.DWORD),
        ('dwYSize', wintypes.DWORD),
        ('dwXCountChars', wintypes.DWORD),
        ('dwYCountChars', wintypes.DWORD),
        ('dwFillAttribute', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('wShowWindow', wintypes.WORD),
        ('cbReserved2', wintypes.WORD),
        ('lpReserved2', ctypes.POINTER(wintypes.BYTE)),
        ('hStdInput', wintypes.HANDLE),
        ('hStdOutput', wintypes.HANDLE),
        ('hStdError', wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('hProcess', wintypes.HANDLE),
        ('hThread', wintypes.HANDLE),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId', wintypes.DWORD),
    ]


def launch_on_default_desktop(executable: str, arguments: str, working_directory: str) -> int:
    startup_info = STARTUPINFOW()
    startup_info.cb = ctypes.sizeof(startup_info)
    startup_info.lpDesktop = 'WinSta0\\Default'
    startup_info.dwFlags = STARTF_USESHOWWINDOW
    startup_info.wShowWindow = SW_SHOWNORMAL
    process_info = PROCESS_INFORMATION()
    command_line = ctypes.create_unicode_buffer(f'"{executable}" {arguments}'.strip())
    kernel32.CreateProcessW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.BOOL,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.LPCWSTR,
        ctypes.POINTER(STARTUPINFOW),
        ctypes.POINTER(PROCESS_INFORMATION),
    ]
    kernel32.CreateProcessW.restype = wintypes.BOOL
    created = kernel32.CreateProcessW(
        executable,
        command_line,
        None,
        None,
        False,
        0,
        None,
        working_directory,
        ctypes.byref(startup_info),
        ctypes.byref(process_info)
    )
    if not created:
        error_code = ctypes.get_last_error()
        raise OSError(f'CreateProcessW failed: error={error_code} executable={executable}')
    kernel32.CloseHandle(process_info.hThread)
    kernel32.CloseHandle(process_info.hProcess)
    return int(process_info.dwProcessId)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('usage: launch_on_default_desktop.py <executable> [arguments] [working_directory]')
    executable = sys.argv[1]
    arguments = sys.argv[2] if len(sys.argv) > 2 else ''
    working_directory = sys.argv[3] if len(sys.argv) > 3 else ''
    process_id = launch_on_default_desktop(executable, arguments, working_directory)
    print(f'launched pid={process_id}')


if __name__ == '__main__':
    main()
