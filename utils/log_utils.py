# -*- coding: utf-8 -*-
"""Application logging and crash diagnostics."""

from __future__ import annotations

import atexit
import faulthandler
import json
import logging
import os
import sys
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import TextIO

from utils.config_utils import get_user_config_dir

LOG_FILE_NAME = 'WeChatMassTool.log'
CRASH_LOG_FILE_NAME = 'crash.log'
LOG_DIR_NAME = 'logs'
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5
LOG_FORMAT = '%(asctime)s.%(msecs)03d %(levelname)-8s %(name)s %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

_configured = False
_crash_file: TextIO | None = None


class _FieldsFormatter(logging.Formatter):
    """Append structured fields to each log line."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        fields = getattr(record, 'fields', None)
        if not fields:
            return message
        return f'{message} | {json.dumps(fields, ensure_ascii=False, sort_keys=True, default=str)}'


def get_log_dir(app_name: str) -> str:
    """Return the directory that stores application logs."""
    return str(Path(get_user_config_dir(app_name)) / LOG_DIR_NAME)


def get_log_file_path(app_name: str) -> str:
    """Return the main application log file path."""
    return os.path.join(get_log_dir(app_name), LOG_FILE_NAME)


def log_event(logger: logging.Logger, level: int, event: str, **fields: object) -> None:
    """Log an event with structured fields instead of interpolated values."""
    logger.log(level, event, extra={'fields': fields})


def log_exception(logger: logging.Logger, event: str, **fields: object) -> None:
    """Log the active exception with structured context."""
    logger.exception(event, extra={'fields': fields})


def setup_logging(app_name: str) -> str:
    """Configure file logging, crash logging and uncaught exception hooks."""
    global _configured
    if _configured:
        return get_log_file_path(app_name=app_name)

    log_dir = get_log_dir(app_name=app_name)
    os.makedirs(log_dir, exist_ok=True)
    log_path = get_log_file_path(app_name=app_name)
    formatter = _FieldsFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    if sys.stderr is not None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _enable_crash_log(log_dir=log_dir)
    _install_exception_hooks()
    _configured = True
    log_event(
        logging.getLogger(__name__),
        logging.INFO,
        'logging_initialized',
        log_file=log_path,
        crash_log=os.path.join(log_dir, CRASH_LOG_FILE_NAME)
    )
    return log_path


def open_log_directory(app_name: str) -> None:
    """Open the log directory in Windows Explorer."""
    log_dir = get_log_dir(app_name=app_name)
    os.makedirs(log_dir, exist_ok=True)
    os.startfile(log_dir)


def _enable_crash_log(log_dir: str) -> None:
    """Enable faulthandler output for native crashes."""
    global _crash_file
    if _crash_file is not None:
        return
    crash_path = os.path.join(log_dir, CRASH_LOG_FILE_NAME)
    _crash_file = open(crash_path, mode='a', encoding='utf-8')
    _crash_file.write(f'\n=== crash log session {datetime.now():%Y-%m-%d %H:%M:%S} ===\n')
    _crash_file.flush()
    faulthandler.enable(file=_crash_file, all_threads=True)
    atexit.register(_close_crash_log)


def _close_crash_log() -> None:
    global _crash_file
    if _crash_file is None:
        return
    faulthandler.disable()
    _crash_file.close()
    _crash_file = None


def _install_exception_hooks() -> None:
    """Route uncaught main-thread and worker-thread exceptions to the log."""
    crash_logger = logging.getLogger('crash')
    previous_hook = sys.excepthook

    def handle_uncaught_exception(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_traceback: TracebackType | None
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            if sys.stderr is not None:
                previous_hook(exc_type, exc_value, exc_traceback)
            return
        crash_logger.critical(
            'uncaught_exception',
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={'fields': {'thread': threading.current_thread().name}}
        )
        if sys.stderr is not None:
            previous_hook(exc_type, exc_value, exc_traceback)

    def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
        thread_name = args.thread.name if args.thread else 'unknown'
        crash_logger.critical(
            'uncaught_thread_exception',
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            extra={'fields': {'thread': thread_name}}
        )

    sys.excepthook = handle_uncaught_exception
    threading.excepthook = handle_thread_exception
