# -*- coding: utf-8 -*-

from __future__ import annotations

# @Time   : 2022-09-11 17:16
# @Name   : wx_operation.py

"""微信群发消息"""

import ctypes
import re
import time
from copy import deepcopy
from difflib import SequenceMatcher
from typing import Iterable, List

import uiautomation as auto
import win32api
import win32con
import win32gui

from config import (WeChat, Interval)
from utils import (copy_files_to_clipboard, wake_up_window)
from utils.ocr_utils import (
    normalize_ocr_text,
    read_wechat_chat_title,
    read_window_text_lines
)
from utils.window_utils import find_visible_window, find_wechat_window


class WxOperation:
    """
    微信群发消息的类，提供了与微信应用交互的方法集，用于发送消息，管理联系人列表等功能。

    Attributes:
    ----------
    wx_window: auto.WindowControl
        微信控制窗口
    input_edit: wx_window.EditControl
        聊天界面输入框编辑控制窗口

    Methods:
    -------
    __goto_chat_box(name):
        跳转到 指定好友窗口
    __send_text(*msgs):
        发送文本。
    __send_file(*filepath):
        发送文件
    get_friend_list(tag, num):
        可指定tag，获取好友num页的好友数量
    send_msg(name, msgs, file_paths=None, add_remark_name=False, at_everyone=False,
            text_interval=0.05, file_interval=0.5) -> None:
        向指定的好友或群聊发送消息和文件。支持同时发送文本和文件。
    """

    def __init__(self):
        self.wx_window = None
        self.input_edit = None
        self.wx_window: auto.WindowControl
        self.input_edit: auto.EditControl
        auto.SetGlobalSearchTimeout(Interval.BASE_INTERVAL)
        self.visible_flag: bool = False
        self.window_handle: int = 0
        self.is_qt_window: bool = False

    def locate_wechat_window(self):
        if self.visible_flag and not win32gui.IsWindow(self.window_handle):
            self.visible_flag = False
        if not self.visible_flag:
            self.window_handle = find_wechat_window(
                window_name=WeChat.WINDOW_NAME,
                window_class_name=WeChat.WINDOW_CLASSNAME,
                qt_class_name_prefix=WeChat.QT_WINDOW_CLASSNAME_PREFIX
            )
            if not self.window_handle:
                wake_up_window(process_name=WeChat.WeChat_PROCESS_NAME)
                deadline = time.time() + WeChat.WINDOW_LAUNCH_SECOND
                while time.time() < deadline:
                    self.window_handle = find_wechat_window(
                        window_name=WeChat.WINDOW_NAME,
                        window_class_name=WeChat.WINDOW_CLASSNAME,
                        qt_class_name_prefix=WeChat.QT_WINDOW_CLASSNAME_PREFIX
                    )
                    if self.window_handle:
                        break
                    time.sleep(WeChat.WINDOW_LAUNCH_INTERVAL)
            if not self.window_handle:
                raise Exception('微信似乎并没有登录!')
            self.wx_window = auto.ControlFromHandle(self.window_handle)
            self.is_qt_window = win32gui.GetClassName(self.window_handle).startswith(
                WeChat.QT_WINDOW_CLASSNAME_PREFIX
            )
            self.visible_flag = True
        # 微信窗口置顶
        self.wx_window.SetTopmost(isTopmost=True)

    def __match_nickname(self, name) -> bool:
        """获取当前面板的好友昵称"""
        if self.is_qt_window:
            return False
        self.input_edit = self.wx_window.EditControl(Name=name)
        if self.input_edit.Exists(Interval.MAX_SEARCH_SECOND, searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL):
            return True
        return False

    def __activate_wechat_tab(self) -> None:
        left, top, right, bottom = win32gui.GetWindowRect(self.window_handle)
        win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
        try:
            win32gui.SetForegroundWindow(self.window_handle)
        except Exception:
            pass
        scale = ctypes.windll.user32.GetDpiForWindow(self.window_handle) / 96
        auto.Click(
            x=left + int(WeChat.CHAT_TAB_X * scale),
            y=top + int(WeChat.CHAT_TAB_Y * scale)
        )
        time.sleep(Interval.BASE_INTERVAL)
        auto.Click(
            x=left + int(WeChat.CHAT_FOCUS_X * scale),
            y=top + int(WeChat.CHAT_FOCUS_Y * scale)
        )
        time.sleep(Interval.BASE_INTERVAL)

    def __click_chat_input(self) -> None:
        left, top, right, bottom = win32gui.GetWindowRect(self.window_handle)
        auto.Click(
            x=int(left + (right - left) * 0.65),
            y=int(top + (bottom - top) * 0.88)
        )
        time.sleep(Interval.BASE_INTERVAL)

    def __verify_current_chat(self, name: str) -> None:
        title = read_wechat_chat_title(window_handle=self.window_handle)
        target_text = normalize_ocr_text(name)
        title_text = normalize_ocr_text(title)
        if target_text not in title_text:
            similarity = SequenceMatcher(None, target_text, title_text).ratio()
            if len(target_text) < 4 or similarity < 0.6:
                self.wx_window.SendKeys(text='{Esc}', waitTime=Interval.BASE_INTERVAL)
                raise NameError(f'昵称不匹配: OCR={title}, 目标={name}')

    def __goto_chat_box_qt(self, name: str) -> bool:
        """
        Open a chat in WeChat 4.2.

        The Qt main window does not expose search results through UIA.
        OCR locates the exact contact row, then the chat title is verified
        again before the input box is focused.
        """
        for attempt in range(2):
            self.__activate_wechat_tab()
            left, top, right, bottom = win32gui.GetWindowRect(self.window_handle)
            scale = ctypes.windll.user32.GetDpiForWindow(self.window_handle) / 96
            for _ in range(2):
                auto.Click(
                    x=left + int(WeChat.SEARCH_BOX_X * scale),
                    y=top + int(WeChat.SEARCH_BOX_Y * scale)
                )
                time.sleep(Interval.BASE_INTERVAL * 2)
            self.wx_window.SendKeys(text='{Ctrl}f', waitTime=Interval.BASE_INTERVAL)
            time.sleep(Interval.BASE_INTERVAL * 2)
            self.wx_window.SendKeys(text='{Ctrl}a', waitTime=Interval.BASE_INTERVAL)
            self.wx_window.SendKey(key=auto.SpecialKeyNames['DELETE'])
            auto.SetClipboardText(text=name)
            time.sleep(Interval.BASE_INTERVAL)
            self.wx_window.SendKeys(text='{Ctrl}v', waitTime=Interval.BASE_INTERVAL)
            time.sleep(Interval.BASE_INTERVAL * 10)
            auto.Click(
                x=left + int(WeChat.SEARCH_CONTACT_ROW_X * scale),
                y=top + int(WeChat.SEARCH_CONTACT_ROW_Y * scale)
            )
            time.sleep(Interval.BASE_INTERVAL * 5)
            try:
                self.__verify_current_chat(name=name)
                self.__click_chat_input()
                return True
            except (NameError, RuntimeError):
                if attempt == 1:
                    raise
                time.sleep(Interval.BASE_INTERVAL * 5)
        return False

    def __goto_chat_box(self, name: str) -> bool:
        """
        跳转到指定 name好友的聊天窗口。

        Args:
            name(str): 必选参数，好友名称

        Returns:
            None
        """
        assert name, "无法跳转到名字为空的聊天窗口"
        if self.is_qt_window:
            return self.__goto_chat_box_qt(name=name)
        self.wx_window.SendKeys(text='{Ctrl}F', waitTime=Interval.BASE_INTERVAL)
        self.wx_window.SendKeys(text='{Ctrl}A', waitTime=Interval.BASE_INTERVAL)
        self.wx_window.SendKey(key=auto.SpecialKeyNames['DELETE'])
        auto.SetClipboardText(text=name)
        time.sleep(Interval.BASE_INTERVAL)
        self.wx_window.SendKeys(text='{Ctrl}V', waitTime=Interval.BASE_INTERVAL)
        search_window = auto.WindowControl(ClassName=WeChat.SEARCH_WINDOW_CLASSNAME)
        if not search_window.Exists(Interval.MAX_SEARCH_SECOND,
                                    searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL):
            self.wx_window.SendKeys(text='{Esc}', waitTime=Interval.BASE_INTERVAL)
            return False

        search_edit = search_window.EditControl(ClassName='mmui::XValidatorTextEdit')
        search_list = search_window.ListControl(AutomationId=WeChat.SEARCH_LIST_AUTOMATION_ID)
        deadline = time.time() + 2
        while time.time() < deadline:
            if (search_edit.Exists(Interval.MAX_SEARCH_SECOND,
                                   searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL) and
                    search_edit.GetValuePattern().Value == name and
                    search_list.Exists(Interval.MAX_SEARCH_SECOND,
                                       searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL)):
                # 只考虑全匹配, 不考虑好友昵称重名, 不考虑好友昵称与群聊重名
                for node in search_list.GetChildren():
                    if node.Name == name:
                        node.Click(simulateMove=False)
                        time.sleep(Interval.BASE_INTERVAL * 2)
                        return True
            time.sleep(Interval.BASE_INTERVAL)

        # 无匹配用户, 取消搜索框
        self.wx_window.SendKeys(text='{Esc}', waitTime=Interval.BASE_INTERVAL)
        return False

    def at_at_everyone(self, group_chat_name: str):
        """
        @全部人的操作
        Args:
            group_chat_name(str): 群聊名称

        """
        if self.is_qt_window:
            self.__click_chat_input()
            self.wx_window.SendKeys(text='{Shift}2', waitTime=Interval.BASE_INTERVAL)
            time.sleep(Interval.BASE_INTERVAL * 5)
            auto.SetClipboardText(text='所有人')
            self.wx_window.SendKeys(text='{Ctrl}v', waitTime=Interval.BASE_INTERVAL)
            time.sleep(Interval.BASE_INTERVAL * 5)
            self.wx_window.SendKey(key=auto.SpecialKeyNames['ENTER'], waitTime=Interval.BASE_INTERVAL)
            self.wx_window.SendKey(key=auto.SpecialKeyNames['ENTER'], waitTime=Interval.BASE_INTERVAL)
            return
        # 个人 定位 聊天框，取 foundIndex=2，因为左侧聊天List 也可以匹配到foundIndex=1
        # 群聊 定位 聊天框 需要带上群人数，故会匹配失败，所以匹配失败的就是群聊
        result = self.wx_window.TextControl(Name=group_chat_name, foundIndex=2)
        # 只要匹配不上，说明这是个群聊窗口
        if not result.Exists(Interval.MAX_SEARCH_SECOND, searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL):
            # 寻找是否有 @所有人 的选项
            self.input_edit.SendKeys(text='{Shift}2', waitTime=Interval.BASE_INTERVAL)
            everyone = self.wx_window.ListItemControl(Name='所有人')
            if not everyone.Exists(Interval.MAX_SEARCH_SECOND, searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL):
                self.input_edit.SendKeys(text='{Ctrl}A', waitTime=Interval.BASE_INTERVAL)
                self.input_edit.SendKeys(text='{Delete}', waitTime=Interval.BASE_INTERVAL)
                return
            self.input_edit.SendKeys(text='{Up}', waitTime=Interval.BASE_INTERVAL)
            self.input_edit.SendKeys(text='{Enter}', waitTime=Interval.BASE_INTERVAL)
            self.input_edit.SendKeys(text='{Enter}', waitTime=Interval.BASE_INTERVAL)

    def __send_text(self, *msgs, wait_time, send_shortcut) -> None:
        """
        发送文本.

        Args:
            input_name(str): 必选参数, 为输入框
            *msgs(str): 必选参数，为发送的文本
            wait_time(float): 必选参数，为动态等待时间
            send_shortcut(str): 必选参数，为发送快捷键

        Returns:
            None
        """

        for msg in msgs:
            assert msg, "发送的文本内容为空"
            if self.is_qt_window:
                self.__click_chat_input()
                self.wx_window.SendKeys(text='{Ctrl}a', waitTime=wait_time)
                self.wx_window.SendKey(key=auto.SpecialKeyNames['DELETE'], waitTime=wait_time)
            else:
                self.input_edit.SendKeys(text='{Ctrl}a', waitTime=wait_time)
                self.input_edit.SendKey(key=auto.SpecialKeyNames['DELETE'], waitTime=wait_time)
                self.input_edit.SendKeys(text='{Ctrl}a', waitTime=wait_time)
                self.input_edit.SendKey(key=auto.SpecialKeyNames['DELETE'], waitTime=wait_time)

            # Clipboard paste keeps Chinese text and punctuation intact across WeChat versions.
            auto.SetClipboardText(text=msg)
            time.sleep(wait_time * 2.5)
            if self.is_qt_window:
                self.wx_window.SendKeys(text='{Ctrl}v', waitTime=wait_time * 2)
            else:
                self.input_edit.SendKeys(text='{Ctrl}v', waitTime=wait_time * 2)

            # 设置到剪切板再黏贴到输入框
            self.wx_window.SendKeys(text=f'{send_shortcut}', waitTime=wait_time * 2)

    def __send_file(self, *file_paths, wait_time, send_shortcut) -> None:
        """
        发送文件.

        Args:
            *file_paths(str): 必选参数，为文件的路径
            wait_time(float): 必选参数，为动态等待时间
            send_shortcut(str): 必选参数，为发送快捷键

        Returns:
            None
        """
        # 复制文件到剪切板
        if copy_files_to_clipboard(file_paths=file_paths):
            # 粘贴到输入框
            if self.is_qt_window:
                self.__click_chat_input()
                self.wx_window.SendKeys(text='{Ctrl}v', waitTime=wait_time)
            else:
                self.input_edit.SendKeys(text='{Ctrl}V', waitTime=wait_time)
            # 按下回车键
            self.wx_window.SendKeys(text=f'{send_shortcut}', waitTime=wait_time / 2)

            time.sleep(wait_time)  # 等待发送动作完成

    def get_friend_list(self, tag: str = None) -> list:
        """
        获取微信好友名称.

        Args:
            tag(str): 可选参数，如不指定，则获取所有好友

        Returns:
            list
        """
        # 定位到微信窗口
        self.locate_wechat_window()
        if self.is_qt_window:
            raise NotImplementedError('当前微信版本暂不支持导出通讯录')
        # 取消微信窗口置顶
        self.wx_window.SetTopmost(isTopmost=False)
        # 点击 通讯录管理
        self.wx_window.ButtonControl(Name="通讯录").Click(simulateMove=False)
        self.wx_window.ListControl(Name="联系人").ButtonControl(Name="通讯录管理").Click(simulateMove=False)
        # 切换到通讯录管理，相当于切换到弹出来的页面
        contacts_window = auto.GetForegroundControl()
        contacts_window.ButtonControl(Name='最大化').Click(simulateMove=False)

        if tag:
            try:
                contacts_window.ButtonControl(Name="标签").Click(simulateMove=False)
                contacts_window.PaneControl(Name=tag).Click(simulateMove=False)
                time.sleep(Interval.BASE_INTERVAL * 2)
            except LookupError:
                contacts_window.SendKey(auto.SpecialKeyNames['ESC'])
                raise LookupError(f'找不到 {tag} 标签')

        name_list = list()
        last_names = None
        while True:
            # TODO 修改成使用 foundIndex 的方式
            try:
                nodes = contacts_window.ListControl(foundIndex=2).GetChildren()
            except LookupError:
                nodes = contacts_window.ListControl().GetChildren()
            cur_names = [node.TextControl().Name for node in nodes]

            # 如果滚动前后名单未变，认为到达底部
            if cur_names == last_names:
                break
            last_names = cur_names
            # 处理当前页的名单
            for node in nodes:
                # TODO 如果有需要, 可以处理成导出为两列的csv格式
                nick_name = node.TextControl().Name  # 用户名
                remark_name = node.ButtonControl(foundIndex=2).Name  # 用户备注名，索引1会错位，索引2是备注名，索引3是标签名
                name_list.append(remark_name if remark_name else nick_name)
            # 向下滚动页面
            contacts_window.WheelDown(wheelTimes=8, waitTime=Interval.BASE_INTERVAL / 2)
        # 结束时候关闭 "通讯录管理" 窗口
        contacts_window.SendKey(auto.SpecialKeyNames['ESC'])
        # 简单去重，但是存在误判（如果存在同名的好友), 保持获取时候的顺序
        return list(dict.fromkeys(name_list))

    def get_chat_group_name_list(self, ):
        """
        获取微信群聊名称列表.

        Returns:
            list
        """
        # 定位到微信窗口
        self.locate_wechat_window()
        if self.is_qt_window:
            return self.__get_chat_group_name_list_qt()
        # 取消微信窗口置顶
        self.wx_window.SetTopmost(isTopmost=False)
        # 点击 通讯录管理
        self.wx_window.ButtonControl(Name="通讯录").Click(simulateMove=False)
        self.wx_window.ListControl(Name="联系人").ButtonControl(Name="通讯录管理").Click(simulateMove=False)
        # 切换到通讯录管理，相当于切换到弹出来的页面
        contacts_window = auto.GetForegroundControl()
        contacts_window.ButtonControl(Name='最大化').Click(simulateMove=False)

        contacts_window.ButtonControl(Name="最近群聊").Click(simulateMove=False)
        time.sleep(Interval.BASE_INTERVAL * 2)

        chat_group_name_list = list()
        last_chat_group_names = None
        #

        while True:
            names: list[str] = [
                _.TextControl().Name for _ in contacts_window.PaneControl(foundIndex=4).ListControl().GetChildren()
            ]
            # 如果滚动前后名单未变，认为到达底部
            if names == last_chat_group_names:
                break
            last_chat_group_names = names
            # 处理当前页的名单
            chat_group_name_list.extend(__iterable=names)
            # 向下滑动
            contacts_window.PaneControl(foundIndex=5).WheelDown(wheelTimes=8, waitTime=Interval.BASE_INTERVAL / 2)
        # 结束时候关闭 "通讯录管理" 窗口
        contacts_window.SendKey(auto.SpecialKeyNames['ESC'])
        # 简单去重，但是存在误判（如果存在同名的好友), 保持获取时候的顺序
        return list(dict.fromkeys(chat_group_name_list))

    def __ensure_contact_manager_qt(self) -> tuple[int, bool]:
        existing = find_visible_window(
            window_name=WeChat.CONTACT_MANAGER_WINDOW_NAME,
            window_class_name='',
            class_name_prefix=WeChat.QT_WINDOW_CLASSNAME_PREFIX
        )
        if existing:
            return existing, False

        left, top, right, bottom = win32gui.GetWindowRect(self.window_handle)
        scale = ctypes.windll.user32.GetDpiForWindow(self.window_handle) / 96
        auto.Click(
            x=left + int(WeChat.CONTACT_TAB_X * scale),
            y=top + int(WeChat.CONTACT_TAB_Y * scale)
        )
        time.sleep(Interval.BASE_INTERVAL * 8)
        auto.Click(
            x=left + int(WeChat.CONTACT_MANAGER_BUTTON_X * scale),
            y=top + int(WeChat.CONTACT_MANAGER_BUTTON_Y * scale)
        )
        deadline = time.time() + WeChat.WINDOW_LAUNCH_SECOND
        while time.time() < deadline:
            handle = find_visible_window(
                window_name=WeChat.CONTACT_MANAGER_WINDOW_NAME,
                window_class_name='',
                class_name_prefix=WeChat.QT_WINDOW_CLASSNAME_PREFIX
            )
            if handle:
                return handle, True
            time.sleep(WeChat.WINDOW_LAUNCH_INTERVAL)
        raise LookupError('无法打开微信通讯录管理窗口')

    @staticmethod
    def __parse_group_name(text: str) -> str:
        compact = ''.join(text.split())
        compact = re.sub(r'[（(]\d+[）)]$', '', compact)
        compact = re.sub(r'^[0O○Q](?=[\u4e00-\u9fff])', '', compact)
        return compact

    def __read_group_names_qt(self, window_handle: int) -> list[str]:
        lines = read_window_text_lines(
            window_handle=window_handle,
            crop_left_fraction=WeChat.GROUP_LIST_CROP_LEFT,
            crop_top_fraction=WeChat.GROUP_LIST_CROP_TOP,
            crop_width_fraction=WeChat.GROUP_LIST_CROP_WIDTH,
            crop_height_fraction=WeChat.GROUP_LIST_CROP_HEIGHT,
            allow_empty=True
        )
        names = list()
        ignored = {'通讯录管理', '全部', '朋友权限', '标签', '最近群聊', '筛选'}
        for line in lines:
            name = self.__parse_group_name(line.text)
            if not name or name in ignored:
                continue
            if re.fullmatch(r'[0-9O○Q]+', name):
                continue
            names.append(name)
        return list(dict.fromkeys(names))

    def __get_chat_group_name_list_qt(self) -> list:
        manager_handle, created = self.__ensure_contact_manager_qt()
        win32gui.SetWindowPos(
            manager_handle,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
        win32gui.ShowWindow(manager_handle, win32con.SW_RESTORE)
        try:
            win32gui.SetForegroundWindow(manager_handle)
        except Exception:
            pass
        time.sleep(Interval.BASE_INTERVAL * 5)

        group_names = self.__read_group_names_qt(window_handle=manager_handle)
        if not group_names:
            left, top, right, bottom = win32gui.GetWindowRect(manager_handle)
            scale = ctypes.windll.user32.GetDpiForWindow(manager_handle) / 96
            auto.Click(
                x=left + int(WeChat.RECENT_GROUPS_BUTTON_X * scale),
                y=top + int(WeChat.RECENT_GROUPS_BUTTON_Y * scale)
            )
            time.sleep(Interval.BASE_INTERVAL * 8)
            group_names = self.__read_group_names_qt(window_handle=manager_handle)

        all_names = list()
        last_page = None
        scroll_count = 0
        while scroll_count < WeChat.GROUP_LIST_MAX_SCROLL:
            page_names = self.__read_group_names_qt(window_handle=manager_handle)
            if page_names == last_page:
                break
            last_page = page_names
            all_names.extend(page_names)
            left, top, right, bottom = win32gui.GetWindowRect(manager_handle)
            win32api.SetCursorPos((
                left + int((right - left) * 0.15),
                top + int((bottom - top) * 0.75)
            ))
            auto.WheelDown(
                wheelTimes=WeChat.GROUP_LIST_SCROLL_TIMES,
                interval=Interval.BASE_INTERVAL,
                waitTime=Interval.BASE_INTERVAL * 2
            )
            scroll_count += 1

        win32gui.SetWindowPos(
            manager_handle,
            win32con.HWND_NOTOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
        if created:
            win32gui.PostMessage(manager_handle, win32con.WM_CLOSE, 0, 0)
        self.wx_window.SetTopmost(isTopmost=False)
        return list(dict.fromkeys(all_names))

    def get_group_chat_list(self) -> list:
        """获取群聊通讯录中的用户名称"""
        self.locate_wechat_window()
        if self.is_qt_window:
            raise NotImplementedError('当前微信版本暂不支持导出群聊成员')
        name_list = list()
        auto.ButtonControl(Name='聊天信息').Click()
        time.sleep(0.5)
        chat_members_win = self.wx_window.ListControl(Name='聊天成员')
        if not chat_members_win.Exists():
            return list()
        self.wx_window.ButtonControl(Name='查看更多').Click()
        for item in chat_members_win.GetChildren():
            name_list.append(item.ButtonControl().Name)
        return name_list

    def send_msg(self, name, msgs=None, file_paths=None, add_remark_name=False, at_everyone=False,
                 text_interval=Interval.SEND_TEXT_INTERVAL, file_interval=Interval.SEND_FILE_INTERVAL,
                 send_shortcut='{Enter}') -> None:
        """
        发送消息，可同时发送文本和文件（至少选一项

        Args:
            name(str):必选参数，接收消息的好友名称, 可以单发
            msgs(Iterable[str], Optional): 可选参数，发送的文本消息
            file_paths(Iterable[str], Optional):可选参数，发送的文件路径
            add_remark_name(bool): 可选参数，是否添加备注名称发送
            at_everyone(bool): 可选参数，是否@全部人
            text_interval(float): 可选参数，默认为0.05
            file_interval(float): 可选参数，默认为0.5
            send_shortcut(str): 可选参数，默认为 Enter

        Raises:
            ValueError: 如果用户名为空或发送的消息和文件同时为空时抛出异常
            TypeError: 如果发送的文本消息或文件路径类型不是列表或元组时抛出异常
        """

        # 定位到微信窗口
        self.locate_wechat_window()

        if not name:
            raise ValueError("用户名不能为空")

        if not any([msgs, file_paths]):
            raise ValueError("发送的消息和文件不可同时为空")

        if msgs and not isinstance(msgs, Iterable):
            raise TypeError("发送的文本消息必须是可迭代的")

        if file_paths and not isinstance(file_paths, Iterable):
            raise TypeError("发送的文件路径必须是可迭代的")

        # 如果当前面板已经是需发送好友, 则无需再次搜索跳转
        if not self.__match_nickname(name=name):
            if not self.__goto_chat_box(name=name):
                raise NameError('昵称不匹配')

        # 设置输入框为当前焦点
        if not self.is_qt_window:
            self.input_edit = self.wx_window.EditControl(
                AutomationId=WeChat.INPUT_AUTOMATION_ID,
                ClassName=WeChat.INPUT_CLASS_NAME
            )
            if not self.input_edit.Exists(Interval.MAX_SEARCH_SECOND,
                                          searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL):
                self.input_edit = self.wx_window.EditControl(
                    AutomationId=WeChat.INPUT_AUTOMATION_ID
                )
            if not self.input_edit.Exists(Interval.MAX_SEARCH_SECOND,
                                          searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL):
                self.input_edit = self.wx_window.EditControl(Name=name)
            if not self.input_edit.Exists(Interval.MAX_SEARCH_SECOND,
                                          searchIntervalSeconds=Interval.MAX_SEARCH_INTERVAL):
                raise LookupError('找不到微信聊天输入框')
            self.input_edit.SetFocus()

        # @所有人
        if at_everyone:
            auto.SetGlobalSearchTimeout(Interval.BASE_INTERVAL)
            self.at_at_everyone(group_chat_name=name)
            auto.SetGlobalSearchTimeout(Interval.BASE_INTERVAL * 25)

        # TODO
        #  添加备注可以多做一个选项，添加到每条消息的前面，如xxx，早上好
        if msgs and add_remark_name:
            new_msgs = deepcopy(list(msgs))
            new_msgs.insert(0, name)
            self.__send_text(*new_msgs, wait_time=text_interval, send_shortcut=send_shortcut)
        elif msgs:
            self.__send_text(*msgs, wait_time=text_interval, send_shortcut=send_shortcut)
        if file_paths:
            self.__send_file(*file_paths, wait_time=file_interval, send_shortcut=send_shortcut)

        # 取消微信窗口置顶
        self.wx_window.SetTopmost(isTopmost=False)


if __name__ == '__main__':
    wx = WxOperation()
    data = wx.get_chat_group_name_list()
    print(data)
