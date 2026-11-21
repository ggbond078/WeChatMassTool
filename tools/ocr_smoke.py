# -*- coding: utf-8 -*-
"""Standalone smoke test for the packaged OCR stack."""

from __future__ import annotations

import traceback

from utils.ocr_utils import read_wechat_chat_title
from utils.window_utils import find_wechat_window


def main() -> None:
    try:
        window_handle = find_wechat_window('微信', '', 'Qt5')
        print(f'hwnd={window_handle}')
        if not window_handle:
            raise RuntimeError('WeChat Qt window not found')
        title = read_wechat_chat_title(window_handle)
        print(f'TITLE={title}')
    except Exception:
        traceback.print_exc()
        raise


main()
