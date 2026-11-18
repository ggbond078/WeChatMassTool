# -*- coding: utf-8 -*-

# @Time   : 2024/5/12 下午5:31
# @Name   : process_utils.py

from __future__ import annotations

from typing import Union

import pywintypes
import wmi
import win32api


def get_specific_process(proc_name: str = 'Weixin.exe') -> bool:
    """获取指定进程是否存在"""
    return any(process.Name == proc_name for process in wmi.WMI().Win32_Process(Name=proc_name))


def is_process_running(pid: Union[int, str], proc_name: str):
    """使用 WMI 检查给定的 PID 是否在运行状态"""
    # None 表示运行中, 判断指定进程id是否在运行中
    return any(
        process.ExecutionState is None and process.Name == proc_name for process in
        wmi.WMI().Win32_Process(ProcessId=pid)
    )


def get_wechat_path(proc_name: str = 'Weixin.exe') -> str:
    c = wmi.WMI()
    if processes := c.Win32_Process(Name=proc_name):
        return processes[0].ExecutablePath  # 返回第一个匹配进程的路径
    return ''


def get_file_version(file_path: str) -> tuple[int, int, int, int]:
    """Read a Windows executable's fixed file version."""
    try:
        version_info = win32api.GetFileVersionInfo(file_path, '\\')
    except pywintypes.error as error:
        raise ValueError(f'无法读取文件版本: file={file_path}') from error

    if 'FileVersionMS' not in version_info or 'FileVersionLS' not in version_info:
        raise ValueError(f'文件缺少版本信息: file={file_path}')

    version_ms = int(version_info['FileVersionMS'])
    version_ls = int(version_info['FileVersionLS'])
    return (
        (version_ms >> 16) & 0xFFFF,
        version_ms & 0xFFFF,
        (version_ls >> 16) & 0xFFFF,
        version_ls & 0xFFFF,
    )


def get_wechat_version(proc_name: str) -> tuple[int, int, int, int]:
    """Read the version of the running WeChat executable."""
    if not (exe_path := get_wechat_path(proc_name=proc_name)):
        raise FileNotFoundError(f'微信进程未运行: process_name={proc_name}')
    return get_file_version(file_path=exe_path)


def format_version(version: tuple[int, int, int, int]) -> str:
    """Format a version tuple as a dotted string."""
    return '.'.join(str(part) for part in version)
