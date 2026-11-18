# -*- coding: utf-8 -*-

from __future__ import annotations

import os

from utils.process_utils import get_wechat_path


UPDATE_NAME_MARKERS = ('update', 'upgrade')
DISABLED_SUFFIX = '.disabled'


def _get_install_dir(proc_name: str) -> str:
    if not (exe_path := get_wechat_path(proc_name=proc_name)):
        raise FileNotFoundError(f'无法定位微信安装目录: process_name={proc_name}')
    exe_dir = os.path.dirname(exe_path)
    parent_dir = os.path.dirname(exe_dir)
    if os.path.basename(parent_dir).lower() in ('weixin', 'wechat'):
        return parent_dir
    return exe_dir


def _is_update_file(file_name: str) -> bool:
    normalized_name = file_name.lower()
    if normalized_name.endswith(DISABLED_SUFFIX):
        normalized_name = normalized_name[:-len(DISABLED_SUFFIX)]
    return normalized_name.endswith('.exe') and any(
        marker in normalized_name for marker in UPDATE_NAME_MARKERS
    )


def _raise_walk_error(error: OSError) -> None:
    raise error


def _find_update_files(install_dir: str) -> list[str]:
    update_files = list()
    for root, _, files in os.walk(install_dir, onerror=_raise_walk_error):
        for file_name in files:
            if _is_update_file(file_name):
                update_files.append(os.path.join(root, file_name))
    return sorted(update_files)


def disable_wechat_auto_update(proc_name: str) -> list[str]:
    """Rename WeChat updater executables so automatic updates cannot run."""
    install_dir = _get_install_dir(proc_name=proc_name)
    update_files = _find_update_files(install_dir=install_dir)
    active_files = [path for path in update_files if not path.lower().endswith(DISABLED_SUFFIX)]
    disabled_files = [path for path in update_files if path.lower().endswith(DISABLED_SUFFIX)]

    if not active_files:
        if disabled_files:
            return list()
        raise FileNotFoundError(
            f'未找到微信更新程序: install_dir={install_dir}, pattern=*update*.exe'
        )

    renamed_files = list()
    for path in active_files:
        backup_path = path + DISABLED_SUFFIX
        if os.path.exists(backup_path):
            raise FileExistsError(f'微信更新程序备份已存在: file={backup_path}')
        try:
            os.rename(path, backup_path)
        except PermissionError as error:
            raise PermissionError(
                f'无法修改微信更新程序，请以管理员身份运行本工具: file={path}, error={error}'
            ) from error
        renamed_files.append(path)
    return renamed_files


def enable_wechat_auto_update(proc_name: str) -> list[str]:
    """Restore WeChat updater executables disabled by this tool."""
    install_dir = _get_install_dir(proc_name=proc_name)
    update_files = _find_update_files(install_dir=install_dir)
    disabled_files = [path for path in update_files if path.lower().endswith(DISABLED_SUFFIX)]

    restored_files = list()
    for path in disabled_files:
        original_path = path[:-len(DISABLED_SUFFIX)]
        if os.path.exists(original_path):
            raise FileExistsError(f'无法恢复微信更新程序，原文件已存在: file={original_path}')
        try:
            os.rename(path, original_path)
        except PermissionError as error:
            raise PermissionError(
                f'无法恢复微信更新程序，请以管理员身份运行本工具: file={path}, error={error}'
            ) from error
        restored_files.append(original_path)
    return restored_files
