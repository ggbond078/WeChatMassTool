# -*- coding: utf-8 -*-
# Name:         main.py
# Date:         2024/4/01 00:00
# Description:

import datetime
import logging
import os
import platform
import sys
from ctypes import windll

import PySide2
import uiautomation
from PySide2 import QtGui
from PySide2.QtWidgets import (QApplication, QMessageBox)
from cprint import cprint

from config import (Animate, WeChat)
from controllers import ControllerMain
from utils import (
    get_specific_process, is_process_running, get_resource_path, get_config, minimize_wechat, write_file, delete_file,
    path_exists, get_temp_file_path, read_file, get_pid, delete_old_files_with_extension, join_path,
    get_wechat_version, format_version, open_webpage, log_event, log_exception, setup_logging
)
from version import (__version__, __project_name__)

logger = logging.getLogger(__name__)


def set_app_user_model_id():
    """设置应用程序用户模型ID"""
    try:
        myapp_id = 'myapp_id'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myapp_id)
    except ImportError:
        pass


def print_startup_info():
    # 获取系统信息
    system_info = platform.uname()
    screen_width = windll.user32.GetSystemMetrics(0)
    screen_height = windll.user32.GetSystemMetrics(1)
    log_event(
        logger,
        logging.INFO,
        'startup_environment',
        project=__project_name__,
        version=__version__,
        os_name=system_info.system,
        os_release=system_info.release,
        os_version=system_info.version,
        processor=system_info.processor,
        python_version=platform.python_version(),
        pyside_version=PySide2.__version__,
        uiautomation_version=uiautomation.version.VERSION,
        screen_width=screen_width,
        screen_height=screen_height,
        frozen=bool(getattr(sys, 'frozen', False)),
        executable=sys.executable,
        cwd=os.getcwd()
    )

    bot_logo = r"""

    /¯¯¯¯\         /¯¯¯¯\         /¯¯¯¯\
  o-|[][]|-o     o-|[][]|-o     o-|[][]|-o
    |_--_|         |_--_|         |_--_|
 /¯¯¯¯¯¯¯¯¯¯\   /¯¯¯¯¯¯¯¯¯¯\   /¯¯¯¯¯¯¯¯¯¯\
 |||  «»  |||   |||  «»  |||   |||  «»  |||
 |||      |||   |||      |||   |||      |||
(o)|      |(o) (o)|      |(o) (o)|      |(o)
   |  ||  |       |  ||  |       |  ||  |
   |__||__|       |__||__|       |__||__|
   |__||__|       |__||__|       |__||__|
"""
    # 启动信息
    startup_info = f"""
        项目名称: {__project_name__}
        版本: {__version__}
        启动时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        系统: {system_info.system} {system_info.release}
        版本: {system_info.version}
        处理器: {system_info.processor}
        Python: {platform.python_version()}
        PySide2: {PySide2.__version__}
        uiautomation: {uiautomation.version.VERSION}

        项目启动中...
    """
    if sys.stdout is None:
        log_event(logger, logging.INFO, 'console_output_unavailable')
        return
    try:
        cprint.info(bot_logo.rstrip('\n'))
        cprint.info(startup_info.rstrip('\n'))
    except (AttributeError, UnicodeEncodeError, ValueError, OSError) as error:
        log_event(
            logger,
            logging.WARNING,
            'console_output_failed',
            error_type=type(error).__name__,
            error=str(error)
        )


def show_wechat_upgrade_dialog(current_version: str):
    """提示用户升级微信版本以保持兼容性"""
    required_version = format_version(WeChat.MIN_SUPPORTED_VERSION)
    message_box = QMessageBox()
    message_box.setWindowTitle('微信版本兼容性提示')
    message_box.setIcon(QMessageBox.Warning)
    message_box.setText(f'当前微信版本：{current_version}')
    message_box.setInformativeText(
        f'本工具需要微信 {required_version} 及以上版本才能稳定运行。\n'
        '建议升级微信，并在设置中关闭微信自动更新，避免版本变化导致群发功能失效。'
    )
    download_button = message_box.addButton('前往下载', QMessageBox.AcceptRole)
    message_box.addButton('稍后', QMessageBox.RejectRole)
    message_box.setDefaultButton(download_button)
    message_box.exec_()
    if message_box.clickedButton() is download_button:
        open_webpage(WeChat.DOWNLOAD_LINK)


def check_wechat_version(proc_name: str):
    """检查微信版本是否满足兼容性要求"""
    try:
        version = get_wechat_version(proc_name=proc_name)
    except (ValueError, OSError) as error:
        log_exception(
            logger,
            'wechat_version_detection_failed',
            process_name=proc_name
        )
        if proc_name == WeChat.LEGACY_PROCESS_NAME:
            show_wechat_upgrade_dialog(current_version='3.x')
            return
        QMessageBox.warning(
            None,
            '微信版本检测失败',
            f'无法读取微信版本，请确认微信安装完整后重试。\n{error}'
        )
        return

    version_text = format_version(version)
    log_event(
        logger,
        logging.INFO,
        'wechat_version_detected',
        process_name=proc_name,
        version=version_text
    )
    if version < WeChat.MIN_SUPPORTED_VERSION:
        show_wechat_upgrade_dialog(current_version=version_text)


def check_wechat_running():
    """检查微信是否运行，并提示版本兼容性"""
    if get_specific_process(proc_name=WeChat.WeChat_PROCESS_NAME):
        log_event(logger, logging.INFO, 'wechat_process_detected', process_name=WeChat.WeChat_PROCESS_NAME)
        check_wechat_version(proc_name=WeChat.WeChat_PROCESS_NAME)
        return
    if get_specific_process(proc_name=WeChat.LEGACY_PROCESS_NAME):
        log_event(logger, logging.INFO, 'wechat_process_detected', process_name=WeChat.LEGACY_PROCESS_NAME)
        check_wechat_version(proc_name=WeChat.LEGACY_PROCESS_NAME)
        return
    log_event(logger, logging.ERROR, 'wechat_process_missing')
    QMessageBox.critical(None, '报错咯', "微信未启动!")
    sys.exit()  # 退出程序


def initialize_application():
    app = QApplication()
    app.setWindowIcon(QtGui.QIcon(get_resource_path(r'views/resources/images/favicon.ico')))
    check_wechat_running()
    log_event(logger, logging.INFO, 'application_window_starting')
    # 获取默认配置, 看是否需要以动画形式启动
    controller = ControllerMain(get_config(WeChat.APP_NAME, section=Animate.SECTION, option=Animate.OPTION))
    # 绑定退出事件, 关闭微信窗口
    app.aboutToQuit.connect(lambda: minimize_wechat(WeChat.WINDOW_CLASSNAME, name=WeChat.WINDOW_NAME))
    sys.exit(app.exec_())


def ensure_single_instance():
    """用于保证只能有一个应用程序实例运行"""
    # 使用文件锁来保证单实例运行, 获取系统存储临时文件路径
    lock_file = get_temp_file_path(file_name=join_path(WeChat.APP_NAME, WeChat.APP_LOCK_NAME))

    # 检查并删除过时的锁文件
    if path_exists(lock_file):
        try:
            # 检查是否有进程在运行
            if not is_process_running(pid=read_file(lock_file)[0], proc_name=WeChat.APP_PROCESS_NAME):
                delete_file(lock_file)
        except (FileExistsError, FileNotFoundError):
            delete_file(lock_file)

    if path_exists(lock_file):
        print("另一个实例已经在运行。")
        log_event(logger, logging.WARNING, 'second_instance_detected', lock_file=lock_file)
        sys.exit()

    # 创建锁文件
    write_file(lock_file, data=[str(get_pid())])


def main():
    """主入口"""
    log_file = setup_logging(WeChat.APP_NAME)
    log_event(
        logger,
        logging.INFO,
        'application_starting',
        argv=sys.argv,
        log_file=log_file
    )
    # 删除三天前的进度缓存文件
    delete_old_files_with_extension(get_temp_file_path(WeChat.APP_NAME), days=3, file_extension='.tmp')
    # 删除运行缓存文件
    delete_old_files_with_extension(
        get_temp_file_path(join_path(WeChat.APP_NAME, '.cache')), days=0, file_extension='.pkl'
    )

    # 保证只有一个应用实例运行
    ensure_single_instance()

    # 正常走的流程
    set_app_user_model_id()
    print_startup_info()  # 打印启动信息
    initialize_application()


if __name__ == '__main__':
    main()
