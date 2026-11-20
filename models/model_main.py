# -*- coding: utf-8 -*-
# Name:         model_main.py
# Date:         2024/4/1 00:00
# Description:

import logging
import time
from typing import Dict
from collections import defaultdict

import uiautomation as auto
from PySide2.QtCore import (QObject, QRunnable, QThreadPool, Slot, Signal)

from utils import (WxOperation, write_file, log_event, log_exception)
from models import RecordGeneratorModel

logger = logging.getLogger(__name__)


class TaskRunnable(QRunnable):
    def __init__(self, func, task_id, *args, **kwargs):
        super().__init__()
        self.func = func
        self.task_id = task_id
        self.args = args
        self.kwargs = kwargs
        self.toggleTaskStatusSignal = kwargs.get('toggleTaskStatusSignal')

    def run(self):
        started = time.monotonic()
        log_event(logger, logging.INFO, 'task_started', task_id=self.task_id)
        try:
            with auto.UIAutomationInitializerInThread():
                self.execute_task()
        except Exception as e:
            self.handle_error(e)
        finally:
            self.toggleTaskStatusSignal.emit(self.task_id)
            log_event(
                logger,
                logging.INFO,
                'task_finished',
                task_id=self.task_id,
                elapsed_seconds=round(time.monotonic() - started, 3)
            )

    def execute_task(self):
        # 将由子类实现具体任务
        pass

    def handle_error(self, error):
        log_exception(
            logger,
            'task_failed',
            task_id=self.task_id,
            error_type=type(error).__name__,
            error=str(error)
        )


class SendMessageTask(TaskRunnable):
    def handle_error(self, error):
        super().handle_error(error)
        show_info_bar = self.kwargs.get('showInfoBarSignal')
        if show_info_bar:
            show_info_bar.emit(False, f'发送任务异常: {error}')

    def execute_task(self):
        # 实现发送消息的逻辑
        message_info = self.kwargs.get('message_info')
        check_pause = self.kwargs.get('check_pause')
        updatedProgressSignal = self.kwargs.get('updatedProgressSignal')
        recordExecInfoSignal = self.kwargs.get('recordExecInfoSignal')
        showInfoBarSignal = self.kwargs.get('showInfoBarSignal')
        cacheProgressSignal = self.kwargs.get('cacheProgressSignal')
        deleteCacheProgressSignal = self.kwargs.get('deleteCacheProgressSignal')
        #
        name_list = message_info.pop('name_list')
        cache_index = int(message_info.pop('cache_index', int(0)))
        text_name_list_count = int(message_info.pop('text_name_list_count', int(0)))
        #
        texts = '\n'.join(message_info.get('msgs', str()))
        files = '\n'.join(message_info.get('file_paths', str()))
        #
        success_count = 0
        failure_count = 0
        log_event(
            logger,
            logging.INFO,
            'send_batch_started',
            total=len(name_list),
            cache_index=cache_index,
            text_name_list_count=text_name_list_count,
            text_count=len(message_info.get('msgs', list())),
            file_count=len(message_info.get('file_paths', list())),
            add_remark_name=message_info.get('add_remark_name'),
            at_everyone=message_info.get('at_everyone'),
            text_interval=message_info.get('text_interval'),
            file_interval=message_info.get('file_interval'),
            send_shortcut=message_info.get('send_shortcut')
        )
        # 首先更新 progress 进度条
        updatedProgressSignal.emit(0, len(name_list))
        #
        for idx, name in enumerate(name_list):
            # 不满足 (不存在缓存进度索引 和 当前索引小于进度索引) 就往下执行, 用于跳过以发送的用户
            if not (cache_index and idx <= cache_index):
                check_pause()  # 检查程序是否暂停
                started = time.monotonic()
                exec_info_map = {'昵称': name, '文本': texts, '文件': files}
                try:
                    self.func(name, **message_info)
                    exec_info_map.update({'状态': '成功'})
                    infobar_info = [True, f'{name[:8]} 发送成功']
                    success_count += 1
                    log_event(
                        logger,
                        logging.INFO,
                        'message_send_succeeded',
                        recipient=name,
                        index=idx,
                        elapsed_seconds=round(time.monotonic() - started, 3)
                    )
                except Exception as e:
                    exec_info_map.update({'状态': '失败', '备注': f'{type(e).__name__}: {e}'})
                    infobar_info = [False, f'{name[:8]} {str(e)}']
                    failure_count += 1
                    log_exception(
                        logger,
                        'message_send_failed',
                        recipient=name,
                        index=idx,
                        elapsed_seconds=round(time.monotonic() - started, 3)
                    )
                finally:
                    recordExecInfoSignal.emit(exec_info_map)
                    showInfoBarSignal.emit(*infobar_info)
                    # 触发缓存文件保存文件操作
                    if text_name_list_count > (idx + 1):
                        cacheProgressSignal.emit(str(idx))
                    # 触发删除缓存进度索引文件
                    if text_name_list_count == (idx + 1):
                        deleteCacheProgressSignal.emit(True)
            else:
                log_event(
                    logger,
                    logging.DEBUG,
                    'message_send_skipped_by_cache',
                    recipient=name,
                    index=idx,
                    cache_index=cache_index
                )
            # 通知更新进度条
            updatedProgressSignal.emit(idx + 1, len(name_list))  # 通知控制器任务完成
        log_event(
            logger,
            logging.INFO,
            'send_batch_finished',
            total=len(name_list),
            success=success_count,
            failed=failure_count
        )
        summary = f'发送结束：成功 {success_count} 位，失败 {failure_count} 位'
        if failure_count:
            summary = f'{summary}，可在设置中打开日志目录查看原因'
        showInfoBarSignal.emit(failure_count == 0, summary)


class GetNameListTask(TaskRunnable):
    def handle_error(self, error):
        super().handle_error(error)
        export_signal = self.kwargs.get('exportNameListSignal')
        if export_signal:
            export_signal.emit(False, f'导出失败: {error}')

    def execute_task(self):
        tag = self.kwargs.get('tag')
        file_path = self.kwargs.get('file_path')
        exportNameListSignal = self.kwargs.get('exportNameListSignal')
        try:
            result = self.func(tag)
            write_file(file_path, data=result)
            exportNameListSignal.emit(True, '文件导出成功')
        except LookupError:
            log_exception(logger, 'name_list_export_failed', tag=tag, file_path=file_path)
            exportNameListSignal.emit(False, f'找不到 {tag} 标签')


class GetChatGroupNameListTask(TaskRunnable):
    def execute_task(self):
        file_path = self.kwargs.get('file_path')
        exportChatGroupNameListSignal = self.kwargs.get('exportChatGroupNameListSignal')
        try:
            result = self.func()
            write_file(file_path, data=result)
            exportChatGroupNameListSignal.emit(True, '文件导出成功')
        except Exception as error:
            exportChatGroupNameListSignal.emit(False, f'导出失败: {error}')
            raise


class ModelMain(QObject):
    toggleTaskStatusSignal = Signal(str)
    recordExecInfoSignal = Signal(dict)
    exportNameListSignal = Signal(bool, str)
    exportChatGroupNameListSignal = Signal(bool, str)
    showInfoBarSignal = Signal(bool, str)
    cacheProgressSignal = Signal(str)
    deleteCacheProgressSignal = Signal(bool)

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)
        #
        self.record = RecordGeneratorModel()
        self.wx = WxOperation()
        #
        self.task_status_map: Dict[str, bool] = defaultdict()  # 用于存放不同任务的状态
        self.toggleTaskStatusSignal.connect(self.change_task_status)
        self.recordExecInfoSignal.connect(self.record_exec_info)

    def export_name_list(self, tag, file_path):
        """导出标签好友名单"""
        task_id = 'name_list'
        if self.task_status_map.get(task_id):
            log_event(logger, logging.WARNING, 'task_already_running', task_id=task_id)
            return
        log_event(logger, logging.INFO, 'name_list_export_requested', tag=tag, file_path=file_path)
        self.toggleTaskStatusSignal.emit(task_id)

        runnable = GetNameListTask(
            self.wx.get_friend_list,
            task_id=task_id,
            tag=None if tag == '全部' else tag,
            file_path=file_path,
            toggleTaskStatusSignal=self.toggleTaskStatusSignal,
            exportNameListSignal=self.exportNameListSignal
        )
        self.thread_pool.start(runnable)

    def export_chat_group_name_list(self, file_path):
        """导出群聊名单"""
        task_id = 'chat_group_name_list'
        if self.task_status_map.get(task_id):
            log_event(logger, logging.WARNING, 'task_already_running', task_id=task_id)
            return
        log_event(logger, logging.INFO, 'chat_group_list_export_requested', file_path=file_path)
        self.toggleTaskStatusSignal.emit(task_id)

        runnable = GetChatGroupNameListTask(
            self.wx.get_chat_group_name_list,
            task_id=task_id,
            file_path=file_path,
            toggleTaskStatusSignal=self.toggleTaskStatusSignal,
            exportChatGroupNameListSignal=self.exportChatGroupNameListSignal
        )
        self.thread_pool.start(runnable)

    def send_wechat_message(self, message_info: dict, check_pause, updatedProgressSignal):
        """发送微信消息"""
        task_id = 'send_msg'
        if self.task_status_map.get(task_id):
            log_event(logger, logging.WARNING, 'task_already_running', task_id=task_id)
            return
        log_event(
            logger,
            logging.INFO,
            'send_task_requested',
            name_count=len(message_info.get('name_list', list())),
            pasted_name_count=len(message_info.get('names', str()).split('\n')) if message_info.get('names') else 0,
            file_count=len(message_info.get('file_paths', list()))
        )
        self.toggleTaskStatusSignal.emit(task_id)

        runnable = SendMessageTask(
            self.wx.send_msg,
            task_id=task_id,
            check_pause=check_pause,
            message_info=self.process_message_info(message_info=message_info),
            updatedProgressSignal=updatedProgressSignal,
            toggleTaskStatusSignal=self.toggleTaskStatusSignal,
            recordExecInfoSignal=self.recordExecInfoSignal,
            showInfoBarSignal=self.showInfoBarSignal,
            cacheProgressSignal=self.cacheProgressSignal,
            deleteCacheProgressSignal=self.deleteCacheProgressSignal
        )
        self.thread_pool.start(runnable)

    @staticmethod
    def process_message_info(message_info):
        # 处理昵称，以换行符为分割
        if names := message_info.pop('names', list()):
            message_info['name_list'].extend(names.split('\n'))

        # 简单去重（导入名单和手动输入重复), 保持获取时候的顺序
        message_info['name_list'] = list(dict.fromkeys(message_info['name_list']))

        # 处理消息
        msg_list = list()
        if signal_text := message_info.pop('single_text', None):
            msg_list.extend(signal_text.split('\n'))
        if multi_text := message_info.pop('multi_text', None):
            msg_list.append(multi_text)

        message_info['msgs'] = msg_list
        return message_info

    @Slot(dict)
    def record_exec_info(self, item):
        self.record.record_exec_result(item)

    @Slot(bool)
    def change_task_status(self, task_id):
        self.task_status_map[task_id] = not self.task_status_map.get(task_id)
