# -*- coding: utf-8 -*-

# @Time   : 2024/5/12 下午5:22
# @Name   : config_utils.py

import os
from configparser import ConfigParser
from pathlib import Path

from config import (Animate, WeChatUpdate)

DEFAULT_OPTIONS = {
    Animate.SECTION: {Animate.OPTION: 'True'},
    WeChatUpdate.SECTION: {WeChatUpdate.OPTION: 'False'},
}


def get_user_config_dir(app_name):
    """
    根据操作系统类型获取用户的配置文件目录。

    Args:
        app_name(str): 应用程序的名称，用于创建或查找配置目录。

    Returns:
        一个Path对象，指向用户的配置目录
    """
    # 根据操作系统不同，返回用户的配置目录
    if os.name == "nt":
        # Windows
        return Path.home() / "AppData" / "Local" / app_name
    else:
        # Unix-like
        return Path.home() / ".config" / app_name


def ensure_config_options(config):
    """Add missing default sections and options to an existing config."""
    changed = False
    for section, options in DEFAULT_OPTIONS.items():
        if section != 'DEFAULT' and not config.has_section(section):
            config.add_section(section)
            changed = True
        for option, value in options.items():
            if not config.has_option(section, option):
                config.set(section, option, value)
                changed = True
    return changed


def save_config(config, config_path):
    with open(config_path, 'w') as configfile:
        config.write(configfile)


def create_default_config(config_path):
    """
    在指定路径创建一个默认配置文件。

    Args:
        config_path(str): 配置文件的路径。

    Returns:
        None
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = ConfigParser()
    ensure_config_options(config)
    save_config(config, config_path)


def get_config(app_name, section='DEFAULT', option=None):
    """
    获取指定应用程序配置项的值。

    Args:
        app_name(str): 应用程序的名称。
        section(str): 配置文件中的节名称。
        option(str): 要检索的配置项名称。

    Returns:
        配置项的值（bool）。
    """

    # 使用示例
    config_dir = get_user_config_dir(app_name)
    config_path = config_dir / "config.ini"

    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)  # exist_ok 避免重复创建时的错误

    # 确保配置文件存在，如果不存在则创建或复制默认配置
    if not config_path.exists():
        create_default_config(config_path)

    config = ConfigParser()
    if not config.read(config_path):
        create_default_config(config_path)
        config.read(config_path)
    ensure_config_options(config)
    return config.getboolean(section, option=option)


def write_config(app_name, section, option, value):
    """
    在配置文件中写入或更新一个配置项。

    Args:
        app_name(str): 应用程序的名称。
        section(str): 配置文件中的节名称。
        option(str): 配置项的名称。
        value(str): 配置项的新值。

    Returns:
        None
    """

    # 使用示例
    config_dir = get_user_config_dir(app_name)
    config_path = config_dir / "config.ini"

    config = ConfigParser()
    if not config.read(config_path):
        create_default_config(config_path=config_path)
        config.read(config_path)

    ensure_config_options(config)

    if section != 'DEFAULT' and not config.has_section(section):
        config.add_section(section)

    # 设置或更新配置项的值
    config.set(section, option, str(value))

    # 将更新后的配置写回文件
    save_config(config, config_path)
