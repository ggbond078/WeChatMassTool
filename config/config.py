# -*- coding: utf-8 -*-
# Name:         config.py
# Date:         2024/3/22 15:19
# Description:

TUTORIAL_LINK = 'https://www.bilibili.com/video/BV1rz421B7Uw/'


class AnimateConfig:
    SECTION = 'DEFAULT'
    OPTION = 'animate_on_startup'


class WeChatUpdateConfig:
    SECTION = 'WeChat'
    OPTION = 'disable_auto_update'


class WeChatConfig:
    WeChat_PROCESS_NAME = 'Weixin.exe'
    LEGACY_PROCESS_NAME = 'WeChat.exe'
    # WeChat_PROCESS_NAME = 'WeChat.exe'
    APP_NAME = 'WeChatMassTool'
    APP_PROCESS_NAME = 'WeChatMassTool.exe'
    APP_LOCK_NAME = 'WeChatMassTool.lock'
    MIN_SUPPORTED_VERSION = (4, 0, 0, 0)
    DOWNLOAD_LINK = 'https://pc.weixin.qq.com/'
    WINDOW_NAME = '微信'
    WINDOW_CLASSNAME = 'mmui::MainWindow'
    QT_WINDOW_CLASSNAME_PREFIX = 'Qt'
    CONTACT_MANAGER_WINDOW_NAME = '通讯录管理'
    CHAT_TAB_X = 35
    CHAT_TAB_Y = 110
    CHAT_FOCUS_X = 200
    CHAT_FOCUS_Y = 150
    CONTACT_TAB_X = 35
    CONTACT_TAB_Y = 153
    CONTACT_MANAGER_BUTTON_X = 150
    CONTACT_MANAGER_BUTTON_Y = 98
    RECENT_GROUPS_BUTTON_X = 52
    RECENT_GROUPS_BUTTON_Y = 216
    # WeChat 4.x fixed UI chrome in 96-DPI logical pixels. These values describe
    # the client layout itself, so they stay valid for any window size or screen
    # resolution and must always be multiplied by the window DPI scale.
    SIDEBAR_WIDTH = 50
    SESSION_LIST_WIDTH = 256
    MESSAGE_AREA_LEFT = 306
    CHAT_TITLE_HEIGHT = 80
    GROUP_LIST_LEFT = 240
    GROUP_LIST_TOP = 90
    GROUP_LIST_RIGHT_MARGIN = 10
    GROUP_LIST_BOTTOM_MARGIN = 10
    GROUP_LIST_SCROLL_TIMES = 5
    GROUP_LIST_MAX_SCROLL = 50
    SEARCH_BOX_X = 165
    SEARCH_BOX_Y = 53
    SEARCH_CONTACT_ROW_X = 290
    SEARCH_CONTACT_ROW_Y = 145
    SEARCH_WINDOW_CLASSNAME = 'mmui::SearchContentPopover'
    SEARCH_LIST_AUTOMATION_ID = 'search_list'
    INPUT_AUTOMATION_ID = 'chat_input_field'
    INPUT_CLASS_NAME = 'mmui::ChatInputField'
    WINDOW_LAUNCH_SECOND = 10
    WINDOW_LAUNCH_INTERVAL = 0.25


class ViewConfig:
    # APP SETTINGS
    MENU_WIDTH = 224
    MENU_COLLAPSED_WIDTH = 72
    LEFT_BOX_WIDTH = 360
    RIGHT_BOX_WIDTH = 0
    TIME_ANIMATION = 500


class DarkConfig:
    QSS_FILE = 'views/resources/themes/py_dracula_dark.qss'

    # BTNS LEFT AND RIGHT BOX COLORS
    BTN_LEFT_BOX_COLOR = "background-color: #12291D;"
    BTN_RIGHT_BOX_COLOR = "background-color: #22C55E;"

    # MENU SELECTED STYLESHEET
    MENU_SELECTED_STYLESHEET = """
        background-color: #12291D;
        border: 1px solid #1F4D36;
        border-left: 3px solid #22C55E;
        color: #4ADE80;
        """

    # MANUAL STYLES
    MANUAL_STYLES = {}


class LightConfig:
    QSS_FILE = 'views/resources/themes/py_dracula_light.qss'

    # BTNS LEFT AND RIGHT BOX COLORS
    BTN_LEFT_BOX_COLOR = "background-color: #F0FDF4;"
    BTN_RIGHT_BOX_COLOR = "background-color: #16A34A;"

    # MENU SELECTED STYLESHEET
    MENU_SELECTED_STYLESHEET = """
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 3px solid #16A34A;
        color: #15803D;
        """

    # MANUAL STYLES
    MANUAL_STYLES = {}


class IntervalConfig:
    BASE_INTERVAL = 0.1  # 基础间隔（秒）
    SEND_TEXT_INTERVAL = 0.05  # 发送文本间隔（秒）
    SEND_FILE_INTERVAL = 0.25  # 发送文件间隔（秒）
    MAX_SEARCH_SECOND = 0.1
    MAX_SEARCH_INTERVAL = 0.05
