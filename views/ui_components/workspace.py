from __future__ import annotations

from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide2.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from version import __version__


PAGE_META = {
    'btn_page_home': ('工作台', '群发任务总览与快速开始'),
    'btn_page_pending': ('通讯录', '联系人名单与导入导出'),
    'btn_page_msg': ('群发消息', '编辑消息、附件与发送目标'),
}


def _label(text: str, object_name: str = '', wrap: bool = False) -> QLabel:
    label = QLabel(text)
    if object_name:
        label.setObjectName(object_name)
    label.setWordWrap(wrap)
    return label


def _button(text: str, role: str, on_click=None) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName({
        'primary': 'PrimaryButton',
        'secondary': 'SecondaryButton',
        'ghost': 'GhostButton',
    }[role])
    button.setProperty('role', role)
    button.setCursor(Qt.PointingHandCursor)
    button.setMinimumHeight(40)
    if on_click:
        button.clicked.connect(on_click)
    return button


def _option_chip(text: str, object_name: str) -> QCheckBox:
    chip = QCheckBox(text)
    chip.setObjectName(object_name)
    chip.setProperty('role', 'chip')
    chip.setCursor(Qt.PointingHandCursor)
    chip.setMinimumHeight(32)
    return chip


def _tinted_icon(resource: str, color: str) -> QIcon:
    pixmap = QPixmap(resource)
    if pixmap.isNull():
        return QIcon()
    tinted = QPixmap(pixmap.size())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(color))
    painter.end()
    return QIcon(tinted)


def _apply_workspace_icons(window, dark: bool) -> None:
    nav_color = '#CBD5E1' if dark else '#475569'
    nav_icons = {
        'btn_page_home': ':/icons/icons/cil-home.png',
        'btn_page_pending': ':/icons/icons/friend.png',
        'btn_page_msg': ':/icons/icons/cli-msg.png',
        'toggleTheme': ':/icons/icons/cli-switch-theme-1.png',
        'toggleLeftBox': ':/icons/icons/icon_settings.png',
        'toggleButton': ':/icons/icons/icon_menu.png',
    }
    for name, resource in nav_icons.items():
        button = getattr(window, name)
        button.setIcon(_tinted_icon(resource, nav_color))
        button.setIconSize(QSize(18, 18))

    window_color = '#CBD5E1' if dark else '#475569'
    window.minimizeAppBtn.setIcon(_tinted_icon(':/icons/icons/icon_minimize.png', window_color))
    maximize_icon = ':/icons/icons/icon_restore.png' if window.is_maximum_size else ':/icons/icons/icon_maximize.png'
    window.maximizeRestoreAppBtn.setIcon(_tinted_icon(maximize_icon, window_color))
    window.closeAppBtn.setIcon(_tinted_icon(':/icons/icons/icon_close.png', '#EF4444'))
    window.extraCloseColumnBtn.setIcon(_tinted_icon(':/icons/icons/icon_close.png', window_color))


def apply_workspace_icons(window) -> None:
    _apply_workspace_icons(window, window.dark_theme)


def _set_role(widget: QWidget, role: str) -> None:
    widget.setProperty('role', role)


def _card(title: str, hint: str = '') -> tuple[QFrame, QVBoxLayout, QHBoxLayout]:
    card = QFrame()
    card.setObjectName('Card')
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(10)
    header = QHBoxLayout()
    header.setSpacing(12)
    header.addWidget(_label(title, 'CardTitle'))
    header.addStretch(1)
    if hint:
        header.addWidget(_label(hint, 'CardHint'))
    layout.addLayout(header)
    body = QVBoxLayout()
    body.setSpacing(10)
    layout.addLayout(body, 1)
    return card, body, header


def _settings_section(title: str, hint: str = '') -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName('SettingsSection')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0, 16, 0, 14)
    layout.setSpacing(10)
    header = QHBoxLayout()
    header.setSpacing(8)
    header.addWidget(_label(title, 'CardTitle'))
    header.addStretch(1)
    if hint:
        header.addWidget(_label(hint, 'CardHint'))
    layout.addLayout(header)
    body = QVBoxLayout()
    body.setSpacing(10)
    layout.addLayout(body)
    return frame, body


def _settings_divider() -> QFrame:
    divider = QFrame()
    divider.setObjectName('SettingsDivider')
    divider.setFixedHeight(1)
    return divider


def _replace_page(window, attribute: str) -> QWidget:
    old_page = getattr(window, attribute)
    index = window.stackedWidget.indexOf(old_page)
    new_page = QWidget()
    new_page.setObjectName(old_page.objectName())
    window.stackedWidget.insertWidget(index, new_page)
    window.stackedWidget.removeWidget(old_page)
    setattr(window, attribute, new_page)
    return old_page


def _stat_card(value_text: str, caption: str, value_object: str = '') -> QFrame:
    card = QFrame()
    card.setObjectName('StatCard')
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(2)
    value = _label(value_text, value_object or 'StatValue')
    layout.addWidget(value)
    layout.addWidget(_label(caption, 'StatCaption'))
    card.value_label = value
    return card


def _icon_badge(resource: str, size: int) -> QFrame:
    badge = QFrame()
    badge.setObjectName('ContactIcon')
    badge.setFixedSize(56, 56)
    layout = QVBoxLayout(badge)
    layout.setContentsMargins(0, 0, 0, 0)
    icon = QLabel()
    icon.setPixmap(QPixmap(resource).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    icon.setAlignment(Qt.AlignCenter)
    layout.addWidget(icon)
    return badge


def _action_row(
        resource: str,
        title: str,
        description: str,
        button_text: str,
        on_click,
) -> QFrame:
    row = QFrame()
    row.setObjectName('ContactActionRow')
    layout = QHBoxLayout(row)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(14)
    layout.addWidget(_icon_badge(resource, 22))
    text = QVBoxLayout()
    text.setSpacing(3)
    text.addWidget(_label(title, 'StepTitle'))
    text.addWidget(_label(description, 'StepText', True))
    layout.addLayout(text, 1)
    layout.addWidget(_button(button_text, 'secondary', on_click))
    return row


def update_header(window, page_key: str) -> None:
    title, subtitle = PAGE_META.get(page_key, PAGE_META['btn_page_home'])
    window.titleRightInfo.setText(
        f'<span style="font-size:14pt;font-weight:600;">{title}</span>'
        f'<br><span style="font-size:9pt;">{subtitle}</span>'
    )


def build_home_page(window) -> None:
    old_page = _replace_page(window, 'home')
    new_page = window.home
    root = QVBoxLayout(new_page)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(_build_home_content(window))
    old_page.deleteLater()


def _build_home_content(window) -> QWidget:
    page = QWidget()
    page.setObjectName('HomePage')
    root = QVBoxLayout(page)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(12)

    hero = QFrame()
    hero.setObjectName('HeroCard')
    hero.setMinimumHeight(180)
    hero_layout = QHBoxLayout(hero)
    hero_layout.setContentsMargins(24, 20, 24, 20)
    hero_layout.setSpacing(20)

    text_column = QVBoxLayout()
    text_column.setSpacing(10)
    text_column.addWidget(_label('WECHAT MASS WORKSPACE', 'Eyebrow'))
    text_column.addWidget(_label('群发工作台', 'HeroTitle'))
    text_column.addWidget(
        _label('把消息、附件与联系人整理进一条清晰的工作流，减少重复操作与误发。', 'HeroText', True)
    )
    hero_actions = QHBoxLayout()
    hero_actions.setSpacing(10)
    hero_actions.addWidget(_button('开始群发', 'primary', window.btn_page_msg.click))
    hero_actions.addWidget(_button('打开设置', 'secondary', window.toggleLeftBox.click))
    hero_actions.addStretch(1)
    text_column.addLayout(hero_actions)
    hero_layout.addLayout(text_column, 1)

    mark = QFrame()
    mark.setObjectName('HeroMark')
    mark.setFixedSize(150, 150)
    mark_layout = QVBoxLayout(mark)
    mark_layout.setContentsMargins(0, 0, 0, 0)
    mark_layout.setAlignment(Qt.AlignCenter)
    logo = QLabel()
    logo.setPixmap(QPixmap(':/images/images/WeChatMass.png').scaled(
        92, 92, Qt.KeepAspectRatio, Qt.SmoothTransformation
    ))
    logo.setAlignment(Qt.AlignCenter)
    mark_layout.addWidget(logo)
    hero_layout.addWidget(mark, 0, Qt.AlignVCenter)
    root.addWidget(hero)

    stats = QHBoxLayout()
    stats.setSpacing(12)
    window.home_pending_value = _stat_card('0', '待发送联系人', 'home_pending_value')
    window.home_progress_value = _stat_card('0%', '当前任务进度', 'home_progress_value')
    window.home_status_value = _stat_card('就绪', '工作台状态', 'home_status_value')
    stats.addWidget(window.home_pending_value)
    stats.addWidget(window.home_progress_value)
    stats.addWidget(window.home_status_value)
    root.addLayout(stats)

    root.addWidget(_label('三步完成一次群发', 'SectionTitle'))
    steps = QHBoxLayout()
    steps.setSpacing(12)
    step_data = (
        ('01', '准备名单', '在通讯录或群发页导入联系人，也可以直接粘贴昵称。'),
        ('02', '编辑内容', '逐条发送或合并发送，附件与消息可同时安排。'),
        ('03', '执行发送', '在右侧控制区启动任务，并随时查看进度与结果。'),
    )
    for number, title, description in step_data:
        card = QFrame()
        card.setObjectName('StepCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        layout.addWidget(_label(number, 'StepNumber'))
        layout.addWidget(_label(title, 'StepTitle'))
        layout.addWidget(_label(description, 'StepText', True))
        steps.addWidget(card, 1)
    root.addLayout(steps)

    check_card, check_body, _ = _card('发送前检查', '降低误发与格式问题')
    for item in (
        '确认联系人名单顺序与数量。',
        '检查文本内容，附件是否完整。',
        '根据微信响应速度调整发送间隔。',
    ):
        check_body.addWidget(_label('•  ' + item, 'StepText', True))
    window.home_check_card = check_card
    root.addWidget(check_card)
    root.addStretch(1)
    return page


def build_contacts_page(window) -> None:
    old_page = _replace_page(window, 'page_friend')
    new_page = window.page_friend
    root = QVBoxLayout(new_page)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(14)

    root.addWidget(_label('联系人名单', 'PageTitle'))
    root.addWidget(_label('导入常用联系人，或从设置面板导出已有名单。', 'PageHint'))

    import_panel = QFrame()
    import_panel.setObjectName('ContactImportPanel')
    import_layout = QHBoxLayout(import_panel)
    import_layout.setContentsMargins(24, 22, 24, 22)
    import_layout.setSpacing(18)
    import_layout.addWidget(_icon_badge(':/icons/icons/friend.png', 30))
    import_text = QVBoxLayout()
    import_text.setSpacing(4)
    import_text.addWidget(_label('导入好友名单', 'CardTitle'))
    import_text.addWidget(
        _label('支持 .txt 文本，每行一个昵称。导入后可继续在群发页补充。', 'StepText', True)
    )
    import_layout.addLayout(import_text, 1)
    import_actions = QVBoxLayout()
    import_actions.setSpacing(8)
    import_actions.addWidget(_button('选择文件', 'primary', window.btn_import_name_list.click))
    import_actions.addWidget(_button('去粘贴昵称', 'secondary', window.btn_page_msg.click))
    import_layout.addLayout(import_actions)
    root.addWidget(import_panel)

    root.addWidget(_label('更多名单操作', 'SectionTitle'))
    action_list = QFrame()
    action_list.setObjectName('ContactActionList')
    action_layout = QVBoxLayout(action_list)
    action_layout.setContentsMargins(0, 0, 0, 0)
    action_layout.setSpacing(0)
    action_layout.addWidget(_action_row(
        ':/icons/icons/export.png',
        '导出好友名单',
        '在设置面板中按标签或全部名单导出。',
        '打开设置',
        window.toggleLeftBox.click,
    ))
    divider = QFrame()
    divider.setObjectName('ContactDivider')
    divider.setFixedHeight(1)
    action_layout.addWidget(divider)
    action_layout.addWidget(_action_row(
        ':/icons/icons/export.png',
        '导出群聊名单',
        '导出最近群聊列表，便于整理发送目标。',
        '打开设置',
        window.toggleLeftBox.click,
    ))
    root.addWidget(action_list)
    root.addWidget(_label('小提示：导入名单后，可在群发页继续修改或粘贴额外昵称。', 'StepText', True))
    root.addStretch(1)


def build_message_page(window) -> None:
    old_page = _replace_page(window, 'wechat')
    for widget in (
        window.btn_clear_msg,
        window.btn_add_file,
        window.btn_clear_file,
        window.btn_clear_name,
        window.btn_send_msg,
        window.btn_pause_send,
        window.btn_export_result,
        window.btn_clear_all,
        window.task_label,
        window.task_progress_bar,
    ):
        widget.setStyleSheet('')
    for button in (window.btn_clear_msg, window.btn_clear_file, window.btn_clear_name):
        button.setIcon(QIcon())
        button.setMinimumWidth(110)
    window.task_progress_bar.setValue(0)
    window.task_progress_bar.setFormat('已完成 %p%')
    window.task_progress_bar.setInvertedAppearance(False)
    new_page = window.wechat
    root = QVBoxLayout(new_page)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(12)

    header = QHBoxLayout()
    header.setSpacing(12)
    header_text = QVBoxLayout()
    header_text.setSpacing(2)
    header_text.addWidget(_label('准备这次群发', 'PageTitle'))
    header_text.addWidget(_label('消息、附件与联系人都在同一页完成。', 'PageHint'))
    header.addLayout(header_text, 1)
    header.addWidget(_label('请检查内容后发送', 'InfoPill'), 0, Qt.AlignTop)
    root.addLayout(header)

    body = QHBoxLayout()
    body.setSpacing(14)
    left = QVBoxLayout()
    left.setSpacing(10)

    message_card, message_body, message_header = _card('消息内容')
    _set_role(window.btn_clear_msg, 'ghost')
    message_header.addWidget(window.btn_clear_msg)
    message_columns = QHBoxLayout()
    message_columns.setSpacing(12)
    for title, editor in (
        ('逐条消息', window.single_line_msg_text_edit),
        ('合并发送', window.multi_line_msg_text_edit),
    ):
        column = QVBoxLayout()
        column.setSpacing(6)
        column.addWidget(_label(title, 'FieldLabel'))
        editor.setMinimumHeight(92)
        editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        column.addWidget(editor)
        message_columns.addLayout(column, 1)
    message_body.addLayout(message_columns)
    left.addWidget(message_card, 3)

    file_card, file_body, file_header = _card('附件')
    _set_role(window.btn_add_file, 'secondary')
    _set_role(window.btn_clear_file, 'ghost')
    file_header.addWidget(window.btn_add_file)
    file_header.addWidget(window.btn_clear_file)
    window.file_list_widget.setMinimumHeight(64)
    file_body.addWidget(window.file_list_widget)
    left.addWidget(file_card, 2)

    name_card, name_body, name_header = _card('联系人')
    _set_role(window.btn_clear_name, 'ghost')
    name_header.addWidget(window.btn_clear_name)
    name_row = QVBoxLayout()
    name_row.setSpacing(8)
    window.name_text_edit.setMinimumHeight(64)
    window.name_text_edit.setPlaceholderText('输入好友昵称，一行一个')
    name_row.addWidget(window.name_text_edit)
    window.rb_at_everyone = _option_chip('@所有人', 'rb_at_everyone')
    window.rb_add_remark = _option_chip('添加备注', 'rb_add_remark')
    options = QHBoxLayout()
    options.setSpacing(22)
    options.addWidget(window.rb_at_everyone)
    options.addWidget(window.rb_add_remark)
    options.addStretch(1)
    name_row.addLayout(options)
    name_body.addLayout(name_row)
    left.addWidget(name_card, 2)
    body.addLayout(left, 1)

    control_panel = QWidget()
    control_panel.setObjectName('ControlPanel')
    control_panel.setMinimumWidth(240)
    control_panel.setMaximumWidth(300)
    control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    control_layout = QVBoxLayout(control_panel)
    control_layout.setContentsMargins(0, 0, 0, 0)
    control_layout.setSpacing(14)

    progress_card, progress_body, _ = _card('发送控制')
    window.task_label.setObjectName('CardTitle')
    progress_body.addWidget(window.task_label)
    window.task_progress_bar.setMinimumHeight(12)
    progress_body.addWidget(window.task_progress_bar)
    _set_role(window.btn_send_msg, 'primary')
    _set_role(window.btn_pause_send, 'secondary')
    progress_body.addWidget(window.btn_send_msg)
    progress_body.addWidget(window.btn_pause_send)
    control_layout.addWidget(progress_card)

    action_card, action_body, _ = _card('任务操作')
    _set_role(window.btn_export_result, 'secondary')
    _set_role(window.btn_clear_all, 'ghost')
    action_body.addWidget(window.btn_export_result)
    action_body.addWidget(window.btn_clear_all)
    action_body.addWidget(_label('发送前建议先导出或备份联系人名单。', 'CardHint', True))
    control_layout.addWidget(action_card)
    control_layout.addStretch(1)
    body.addWidget(control_panel)
    root.addLayout(body, 1)
    old_page.deleteLater()


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        child_layout = item.layout()
        if child_layout is not None:
            _clear_layout(child_layout)


def _field_row(label: QLabel, control: QWidget) -> QHBoxLayout:
    label.setObjectName('FieldLabel')
    row = QHBoxLayout()
    row.setSpacing(10)
    row.addWidget(label, 1)
    control.setMinimumHeight(36)
    row.addWidget(control, 1)
    return row


def build_settings_drawer(window) -> None:
    content = window.extraContent
    content_layout = content.layout()
    if content_layout is None:
        return

    drawer_layout = window.extraLeftBox.layout()
    drawer_layout.removeWidget(window.extraTopBg)
    drawer_layout.removeWidget(window.extraContent)
    drawer_layout.setContentsMargins(10, 10, 10, 10)
    drawer_layout.setSpacing(0)

    window.extraTopBg.setMinimumHeight(78)
    window.extraTopBg.setMaximumHeight(78)
    window.extraTopLayout.setContentsMargins(16, 10, 12, 10)
    window.extraTopLayout.setHorizontalSpacing(10)
    window.extraTopLayout.setVerticalSpacing(2)
    window.extraLabel.setText('设置')
    subtitle = _label('发送节奏、快捷键与名单偏好', 'SettingsSubtitle')
    window.extraTopLayout.addWidget(subtitle, 1, 1, 1, 1)

    sheet = QFrame()
    sheet.setObjectName('SettingsSheet')
    sheet_layout = QVBoxLayout(sheet)
    sheet_layout.setContentsMargins(0, 0, 0, 0)
    sheet_layout.setSpacing(0)
    sheet_layout.addWidget(window.extraTopBg)
    sheet_layout.addWidget(window.extraContent, 1)
    drawer_layout.addWidget(sheet)

    controls = [
        window.label_3, window.cb_text_interval,
        window.label_4, window.cb_file_interval,
        window.label_5, window.radio_btn_animate_true, window.radio_btn_animate_false,
        window.label_7, window.radio_btn_enter, window.radio_btn_ctrl_enter,
        window.label_2, window.import_name_list_line_edit, window.btn_import_name_list,
        window.label_6, window.export_tag_name_list_line_edit, window.btn_export_name_list,
        window.label_8, window.export_chat_group_name_list_line_edit, window.btn_export_chat_group_name_list,
        window.textEdit,
    ]

    scroll = QScrollArea()
    scroll.setObjectName('SettingsScroll')
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    panel = QWidget()
    panel.setObjectName('SettingsPanel')
    for control in controls:
        control.setParent(panel)
    _clear_layout(content_layout)
    panel_layout = QVBoxLayout(panel)
    panel_layout.setContentsMargins(20, 8, 20, 20)
    panel_layout.setSpacing(0)

    rhythm_card, rhythm_body = _settings_section('发送节奏')
    rhythm_body.addWidget(_label('根据网络与微信响应速度调整，避免操作过快。', 'CardHint', True))
    rhythm_body.addLayout(_field_row(window.label_3, window.cb_text_interval))
    rhythm_body.addLayout(_field_row(window.label_4, window.cb_file_interval))
    panel_layout.addWidget(rhythm_card)
    panel_layout.addWidget(_settings_divider())

    mode_card, mode_body = _settings_section('发送方式')
    mode_rows = QHBoxLayout()
    mode_rows.setSpacing(12)
    animate_column = QVBoxLayout()
    animate_column.setSpacing(8)
    animate_column.addWidget(window.label_5)
    animate_column.addWidget(window.radio_btn_animate_true)
    animate_column.addWidget(window.radio_btn_animate_false)
    mode_rows.addLayout(animate_column, 1)
    shortcut_column = QVBoxLayout()
    shortcut_column.setSpacing(8)
    shortcut_column.addWidget(window.label_7)
    shortcut_column.addWidget(window.radio_btn_enter)
    shortcut_column.addWidget(window.radio_btn_ctrl_enter)
    mode_rows.addLayout(shortcut_column, 1)
    mode_body.addLayout(mode_rows)
    panel_layout.addWidget(mode_card)
    panel_layout.addWidget(_settings_divider())

    update_card, update_body = _settings_section('微信兼容性')
    update_body.addWidget(
        _label('关闭后锁定当前微信版本，避免自动更新导致群发功能失效。', 'CardHint', True)
    )
    window.chk_disable_wechat_update = _option_chip('关闭微信自动更新', 'chk_disable_wechat_update')
    window.chk_disable_wechat_update.setToolTip(
        '关闭后需要修改微信安装目录中的更新程序，权限不足时请以管理员身份运行本工具'
    )
    update_row = QHBoxLayout()
    update_row.setSpacing(8)
    update_row.addWidget(window.chk_disable_wechat_update)
    update_row.addStretch(1)
    update_body.addLayout(update_row)
    panel_layout.addWidget(update_card)
    panel_layout.addWidget(_settings_divider())

    list_card, list_body = _settings_section('名单管理')
    window.label_2.setObjectName('FieldLabel')
    list_body.addWidget(window.label_2)
    import_row = QHBoxLayout()
    import_row.setSpacing(8)
    import_row.addWidget(window.import_name_list_line_edit, 1)
    _set_role(window.btn_import_name_list, 'secondary')
    import_row.addWidget(window.btn_import_name_list)
    list_body.addLayout(import_row)

    window.label_6.setObjectName('FieldLabel')
    list_body.addWidget(window.label_6)
    export_friend_row = QHBoxLayout()
    export_friend_row.setSpacing(8)
    export_friend_row.addWidget(window.export_tag_name_list_line_edit, 1)
    _set_role(window.btn_export_name_list, 'ghost')
    export_friend_row.addWidget(window.btn_export_name_list)
    list_body.addLayout(export_friend_row)

    window.label_8.setObjectName('FieldLabel')
    list_body.addWidget(window.label_8)
    export_group_row = QHBoxLayout()
    export_group_row.setSpacing(8)
    export_group_row.addWidget(window.export_chat_group_name_list_line_edit, 1)
    _set_role(window.btn_export_chat_group_name_list, 'ghost')
    export_group_row.addWidget(window.btn_export_chat_group_name_list)
    list_body.addLayout(export_group_row)
    panel_layout.addWidget(list_card)
    panel_layout.addWidget(_settings_divider())

    help_card, help_body = _settings_section('使用帮助')
    window.textEdit.setStyleSheet('background: transparent; border: none;')
    window.textEdit.setMaximumHeight(170)
    window.textEdit.setHtml(
        '<p style="color:#94A3B8; line-height:150%;">'
        '1. 在「群发消息」页填写内容与联系人。<br>'
        '2. 发送前检查附件与发送快捷键。<br>'
        '3. 双击此区域可以打开视频教程。<br>'
        '4. 发送失败时打开日志目录查看详细原因。'
        '</p>'
    )
    help_body.addWidget(window.textEdit)
    window.btn_open_log_dir = _button('打开日志目录', 'ghost')
    window.btn_open_log_dir.setToolTip('日志文件保存在用户目录的 AppData\\Local\\WeChatMassTool\\logs 下')
    help_body.addWidget(window.btn_open_log_dir)
    panel_layout.addWidget(help_card)
    panel_layout.addStretch(1)

    scroll.setWidget(panel)
    content_layout.addWidget(scroll)


def _configure_sidebar(window) -> None:
    window.leftMenuBg.setMinimumWidth(224)
    window.leftMenuBg.setMaximumWidth(224)
    window.stackedWidget.setStyleSheet('')
    window.topLogoInfo.setMinimumHeight(72)
    window.topLogoInfo.setMaximumHeight(72)
    window.topLogo.setGeometry(16, 16, 40, 40)
    window.titleLeftApp.setGeometry(68, 14, 142, 24)
    window.titleLeftDescription.setGeometry(68, 40, 142, 18)
    window.titleLeftApp.setText('WeChatMass')
    window.titleLeftDescription.setText('消息群发工作台')

    top_menu_layout = window.topMenu.layout()
    top_menu_layout.setContentsMargins(12, 8, 12, 8)
    top_menu_layout.setSpacing(6)
    bottom_menu_layout = window.bottomMenu.layout()
    bottom_menu_layout.setContentsMargins(12, 8, 12, 8)
    bottom_menu_layout.setSpacing(6)

    nav_texts = {
        'btn_page_home': '工作台',
        'btn_page_pending': '通讯录',
        'btn_page_msg': '群发消息',
        'toggleTheme': '外观',
        'toggleLeftBox': '设置',
    }
    for name, text in nav_texts.items():
        button = getattr(window, name)
        button.setMinimumHeight(44)
        button.setProperty('fullText', text)
        button.setText(text)
        button.setStyleSheet('')
    window.toggleButton.setText('收起菜单')
    window.toggleButton.setProperty('fullText', '收起菜单')
    window.toggleButton.setMinimumHeight(48)
    window.toggleButton.setStyleSheet('')


def _configure_shell(window) -> None:
    window.setWindowTitle('WeChatMassTool')
    window.resize(1280, 800)
    window.setMinimumSize(1200, 720)
    window.contentTopBg.setMinimumHeight(64)
    window.contentTopBg.setMaximumHeight(64)
    window.horizontalLayout.setContentsMargins(24, 0, 14, 0)
    window.titleRightInfo.setMaximumHeight(64)
    window.pagesContainer.layout().setContentsMargins(24, 18, 24, 16)
    window.bottomBar.setMinimumHeight(30)
    window.bottomBar.setMaximumHeight(30)
    window.creditsLabel.setText('本地工作台')
    window.version.setText(f'v{__version__}')
    window.settingsTopBtn.hide()
    window.extraRightBox.hide()
    window.extraRightBox.setMaximumWidth(0)


def set_sidebar_compact(window, compact: bool) -> None:
    window.titleLeftApp.setVisible(not compact)
    window.titleLeftDescription.setVisible(not compact)
    window.topLogo.move(16, 16)
    tooltips = {
        'btn_page_home': '工作台',
        'btn_page_pending': '通讯录',
        'btn_page_msg': '群发消息',
        'toggleTheme': '切换主题',
        'toggleLeftBox': '打开设置',
        'toggleButton': '展开菜单',
    }
    for name in ('btn_page_home', 'btn_page_pending', 'btn_page_msg', 'toggleTheme', 'toggleLeftBox', 'toggleButton'):
        button = getattr(window, name)
        full_text = button.property('fullText') or ''
        button.setText('' if compact else full_text)
        button.setProperty('compact', compact)
        button.setToolTip(tooltips[name] if compact else '')
        button.style().unpolish(button)
        button.style().polish(button)


def apply_workspace_theme(window, dark: bool) -> None:
    """Synchronize explicit button surfaces for reliable Qt rendering."""
    help_color = '#94A3B8' if dark else '#64748B'
    _apply_workspace_icons(window, dark)
    window.textEdit.setHtml(
        f'<p style="color:{help_color}; line-height:150%;">'
        '1. 在「群发消息」页填写内容与联系人。<br>'
        '2. 发送前检查附件与发送快捷键。<br>'
        '3. 双击此区域可以打开视频教程。<br>'
        '4. 发送失败时打开日志目录查看详细原因。'
        '</p>'
    )
    if dark:
        styles = {
            'primary': (
                'background: #22C55E; color: #052E16; border: 1px solid #22C55E;',
                'background: #34D399; color: #052E16; border: 1px solid #34D399;',
                'background: #16A34A; color: #052E16; border: 1px solid #16A34A;',
            ),
            'secondary': (
                'background: transparent; color: #CBD5E1; border: 1px solid #334155;',
                'background: #162033; color: #E2E8F0; border: 1px solid #475569;',
                'background: #1B2940; color: #E2E8F0; border: 1px solid #475569;',
            ),
            'ghost': (
                'background: transparent; color: #94A3B8; border: 1px solid transparent;',
                'background: #162033; color: #E2E8F0; border: 1px solid transparent;',
                'background: #1B2940; color: #E2E8F0; border: 1px solid transparent;',
            ),
        }
    else:
        styles = {
            'primary': (
                'background: #16A34A; color: #FFFFFF; border: 1px solid #16A34A;',
                'background: #15803D; color: #FFFFFF; border: 1px solid #15803D;',
                'background: #166534; color: #FFFFFF; border: 1px solid #166534;',
            ),
            'secondary': (
                'background: #FFFFFF; color: #334155; border: 1px solid #E2E8F0;',
                'background: #F8FAFC; color: #0F172A; border: 1px solid #CBD5E1;',
                'background: #F1F5F9; color: #0F172A; border: 1px solid #CBD5E1;',
            ),
            'ghost': (
                'background: transparent; color: #64748B; border: 1px solid transparent;',
                'background: #F1F5F9; color: #0F172A; border: 1px solid transparent;',
                'background: #E2E8F0; color: #0F172A; border: 1px solid transparent;',
            ),
        }
    role_names = {
        'primary': ('PrimaryButton', 'btn_send_msg'),
        'secondary': (
            'SecondaryButton', 'btn_pause_send', 'btn_export_result',
            'btn_add_file', 'btn_import_name_list',
        ),
        'ghost': (
            'GhostButton', 'btn_clear_msg', 'btn_clear_file', 'btn_clear_name',
            'btn_clear_all', 'btn_export_name_list', 'btn_export_chat_group_name_list',
        ),
    }
    for role, object_names in role_names.items():
        normal, hover, pressed = styles[role]
        for object_name in object_names:
            for button in window.findChildren(QPushButton, object_name):
                button.setStyleSheet(
                    f'QPushButton {{ {normal} border-radius: 6px; padding: 8px 14px; '
                    f'font-weight: 700; }}'
                    f'QPushButton:hover {{ {hover} }}'
                    f'QPushButton:pressed {{ {pressed} }}'
                )
    if dark:
        danger = (
            'background: transparent; color: #F87171; border: 1px solid transparent;',
            'background: #2A1519; color: #FCA5A5; border: 1px solid transparent;',
            'background: #3A1A1F; color: #FCA5A5; border: 1px solid transparent;',
        )
    else:
        danger = (
            'background: transparent; color: #B91C1C; border: 1px solid transparent;',
            'background: #FEE2E2; color: #991B1B; border: 1px solid transparent;',
            'background: #FECACA; color: #991B1B; border: 1px solid transparent;',
        )
    normal, hover, pressed = danger
    for button in window.findChildren(QPushButton, 'btn_clear_all'):
        button.setStyleSheet(
            f'QPushButton {{ {normal} border-radius: 6px; padding: 8px 14px; font-weight: 700; }}'
            f'QPushButton:hover {{ {hover} }}'
            f'QPushButton:pressed {{ {pressed} }}'
        )
    _apply_message_header_action_style(window, dark)


def _apply_message_header_action_style(window, dark: bool) -> None:
    if dark:
        secondary = (
            'background: transparent; color: #CBD5E1; border: 1px solid #334155;',
            'background: #162033; color: #E2E8F0; border: 1px solid #475569;',
        )
        ghost = (
            'background: transparent; color: #94A3B8; border: none;',
            'background: #162033; color: #E2E8F0; border: none;',
        )
    else:
        secondary = (
            'background: #FFFFFF; color: #334155; border: 1px solid #E2E8F0;',
            'background: #F8FAFC; color: #0F172A; border: 1px solid #CBD5E1;',
        )
        ghost = (
            'background: transparent; color: #64748B; border: none;',
            'background: #F1F5F9; color: #0F172A; border: none;',
        )
    normal, hover = secondary
    window.btn_add_file.setStyleSheet(
        f'QPushButton {{ {normal} border-radius: 6px; padding: 3px 10px; font-weight: 600; }}'
        f'QPushButton:hover {{ {hover} }}'
    )
    window.btn_add_file.setFixedHeight(30)
    normal, hover = ghost
    for button in (window.btn_clear_file, window.btn_clear_msg, window.btn_clear_name):
        button.setStyleSheet(
            f'QPushButton {{ {normal} border-radius: 6px; padding: 3px 10px; font-weight: 600; }}'
            f'QPushButton:hover {{ {hover} }}'
        )
        button.setFixedHeight(30)


def apply_workspace_ui(window) -> None:
    _configure_shell(window)
    _configure_sidebar(window)
    build_home_page(window)
    build_contacts_page(window)
    build_message_page(window)
    build_settings_drawer(window)
    window.stackedWidget.setCurrentWidget(window.home)
    update_header(window, 'btn_page_home')


def update_home_responsive_layout(window) -> None:
    if not hasattr(window, 'home_check_card'):
        return
    if window.home.width() <= 0 or window.home.height() <= 0:
        window.home_check_card.setVisible(True)
        return
    compact = window.home.width() < 680 and window.home.height() < 620
    window.home_check_card.setVisible(not compact)


def update_message_responsive_layout(window) -> None:
    if not hasattr(window, 'btn_add_file'):
        return
    compact = window.wechat.width() < 700
    labels = {
        window.btn_add_file: ('添加', '添加文件'),
        window.btn_clear_file: ('清空', '清空文件'),
        window.btn_clear_msg: ('清空', '清空输入'),
        window.btn_clear_name: ('清空', '清空输入'),
    }
    for button, (compact_text, full_text) in labels.items():
        text = compact_text if compact else full_text
        button.setText(text)
        button.setToolTip(full_text if compact else '')
        button.ensurePolished()
        metrics = button.fontMetrics()
        safety_width = 52
        minimum_width = 82 if compact else 128
        button.setMinimumWidth(max(minimum_width, metrics.horizontalAdvance(text) + safety_width))
        button.setFixedHeight(30)

