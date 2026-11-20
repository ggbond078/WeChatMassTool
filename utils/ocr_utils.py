# -*- coding: utf-8 -*-
"""Window capture and local OCR helpers for the WeChat 4.x Qt client."""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import NamedTuple

import uiautomation as auto
import win32con
import win32gui
from PIL import Image

from config import WeChat
from utils.log_utils import log_event
from utils.window_utils import get_window_dpi_scale

logger = logging.getLogger(__name__)

CAPTURE_TIMEOUT_SECOND = 25
OCR_MIN_CONFIDENCE = 0.5
OCR_UPSCALE_BELOW_PIXELS = 80
OCR_UPSCALE_FACTOR = 2

auto.SetProcessDpiAwareness(auto.ProcessDpiAwareness.PerMonitorDpiAware)

_OCR_ENGINE = None


class OcrLine(NamedTuple):
    text: str
    left: int
    top: int
    width: int
    height: int


def _build_capture_script(window_handle: int, image_path: str, report_path: str) -> str:
    return f"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WmtCapture {{
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {{ public int Left; public int Top; public int Right; public int Bottom; }}
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
}}
"@
$hwnd = [IntPtr]{window_handle}
$rect = New-Object WmtCapture+RECT
[void][WmtCapture]::GetWindowRect($hwnd, [ref]$rect)
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) {{ throw "invalid window rect $width x $height" }}

function Get-ColorCount($bitmap) {{
    $colors = New-Object 'System.Collections.Generic.HashSet[string]'
    $stepX = [Math]::Max(1, [int]($bitmap.Width / 40))
    $stepY = [Math]::Max(1, [int]($bitmap.Height / 40))
    for ($x = 0; $x -lt $bitmap.Width; $x += $stepX) {{
        for ($y = 0; $y -lt $bitmap.Height; $y += $stepY) {{
            $pixel = $bitmap.GetPixel($x, $y)
            [void]$colors.Add("$($pixel.R),$($pixel.G),$($pixel.B)")
        }}
    }}
    return $colors.Count
}}

$attempts = New-Object System.Collections.ArrayList
$saved = $null
$chosen = ''
foreach ($strategy in @('copy_from_screen', 'print_window_full', 'print_window_plain')) {{
    $bitmap = New-Object System.Drawing.Bitmap $width, $height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $captured = $false
    $detail = ''
    try {{
        if ($strategy -eq 'copy_from_screen') {{
            $size = New-Object System.Drawing.Size $width, $height
            $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $size)
            $captured = $true
        }} else {{
            $flags = if ($strategy -eq 'print_window_full') {{ 2 }} else {{ 0 }}
            $deviceContext = $graphics.GetHdc()
            try {{
                $captured = [WmtCapture]::PrintWindow($hwnd, $deviceContext, [uint32]$flags)
            }} finally {{
                $graphics.ReleaseHdc($deviceContext)
            }}
            $detail = "flags=$flags"
        }}
    }} catch {{
        $captured = $false
        $detail = $_.Exception.Message
    }}
    $graphics.Dispose()
    $colorCount = 0
    if ($captured) {{
        $colorCount = Get-ColorCount $bitmap
    }}
    [void]$attempts.Add(@{{ strategy = $strategy; captured = $captured; color_count = $colorCount; detail = $detail }})
    if ($colorCount -gt 1) {{
        $saved = $bitmap
        $chosen = $strategy
        break
    }}
    $bitmap.Dispose()
}}

$report = @{{
    window = @{{ left = $rect.Left; top = $rect.Top; width = $width; height = $height }}
    chosen = $chosen
    attempts = $attempts
}}
$json = $report | ConvertTo-Json -Depth 6 -Compress
[System.IO.File]::WriteAllText('{report_path}', $json, (New-Object System.Text.UTF8Encoding($false)))
if ($null -eq $saved) {{
    throw "all capture strategies returned a blank image"
}}
$saved.Save('{image_path}', [System.Drawing.Imaging.ImageFormat]::Png)
$saved.Dispose()
"""


def _read_capture_report(report_path: Path) -> dict:
    if not report_path.exists():
        return {}
    return json.loads(report_path.read_text(encoding='utf-8-sig'))


def _ensure_capture_ready(window_handle: int) -> None:
    """Restore and focus WeChat so a desktop capture sees its own pixels."""
    if win32gui.IsIconic(window_handle):
        win32gui.ShowWindow(window_handle, win32con.SW_RESTORE)
        time.sleep(0.4)
    foreground = win32gui.GetForegroundWindow()
    if foreground != window_handle:
        try:
            win32gui.SetForegroundWindow(window_handle)
        except Exception as error:
            log_event(
                logger,
                logging.WARNING,
                'set_foreground_failed',
                window_handle=window_handle,
                error=str(error)
            )
        time.sleep(0.3)
    log_event(
        logger,
        logging.INFO,
        'capture_ready',
        window_handle=window_handle,
        foreground=win32gui.GetForegroundWindow(),
        iconic=bool(win32gui.IsIconic(window_handle))
    )


def _capture_window_image(window_handle: int) -> tuple[Image.Image, dict]:
    """Capture the full window with the first strategy that yields real pixels."""
    _ensure_capture_ready(window_handle)
    image_path = Path(tempfile.gettempdir()) / 'wechat-mass-tool-window.png'
    report_path = Path(tempfile.gettempdir()) / 'wechat-mass-tool-window.json'
    script_path = Path(tempfile.gettempdir()) / 'wechat-mass-tool-capture.ps1'
    for stale in (image_path, report_path):
        if stale.exists():
            stale.unlink()
    script_path.write_text(
        _build_capture_script(
            window_handle=window_handle,
            image_path=str(image_path),
            report_path=str(report_path)
        ),
        encoding='utf-8-sig'
    )
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = subprocess.SW_HIDE
    result = subprocess.run(
        [
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy',
            'Bypass',
            '-File',
            str(script_path)
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=CAPTURE_TIMEOUT_SECOND,
        check=False,
        startupinfo=startup_info
    )
    report = _read_capture_report(report_path)
    if result.returncode != 0 or not image_path.exists():
        log_event(
            logger,
            logging.ERROR,
            'window_capture_failed',
            window_handle=window_handle,
            return_code=result.returncode,
            report=report,
            stderr=result.stderr.strip()
        )
        raise RuntimeError(
            f'微信窗口截图失败: hwnd={window_handle}, return_code={result.returncode}, '
            f'report={report}, stderr={result.stderr.strip()}'
        )
    log_event(
        logger,
        logging.INFO,
        'window_capture_succeeded',
        window_handle=window_handle,
        strategy=report.get('chosen', ''),
        attempts=report.get('attempts', [])
    )
    return Image.open(image_path).convert('RGB'), report


def _get_ocr_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR
        _OCR_ENGINE = RapidOCR()
        log_event(logger, logging.INFO, 'ocr_engine_loaded', engine='rapidocr_onnxruntime')
    return _OCR_ENGINE


def _recognize_lines(image: Image.Image) -> list[OcrLine]:
    """Run RapidOCR on an image and return lines in image-local coordinates."""
    scale = 1
    if image.height < OCR_UPSCALE_BELOW_PIXELS:
        scale = OCR_UPSCALE_FACTOR
        image = image.resize(
            (image.width * scale, image.height * scale),
            Image.LANCZOS
        )
    engine = _get_ocr_engine()
    result, elapsed = engine(image)
    lines: list[OcrLine] = []
    if not result:
        return lines
    for item in result:
        box = item[0]
        text = str(item[1])
        confidence = float(item[2])
        if confidence < OCR_MIN_CONFIDENCE:
            continue
        xs = [float(point[0]) for point in box]
        ys = [float(point[1]) for point in box]
        left = int(min(xs)) // scale
        top = int(min(ys)) // scale
        width = (int(max(xs)) - int(min(xs))) // scale
        height = (int(max(ys)) - int(min(ys))) // scale
        lines.append(OcrLine(text=text, left=left, top=top, width=width, height=height))
    log_event(
        logger,
        logging.DEBUG,
        'ocr_lines_recognized',
        line_count=len(lines),
        scale=scale,
        elapsed=elapsed
    )
    return lines


def _save_debug_crop(image: Image.Image, name: str) -> str:
    path = Path(tempfile.gettempdir()) / name
    try:
        image.save(path)
        return str(path)
    except OSError as error:
        log_event(logger, logging.WARNING, 'ocr_debug_save_failed', path=str(path), error=str(error))
        raise RuntimeError(f'无法保存 OCR 调试图: path={path}, error={error}') from error


def save_window_screenshot(window_handle: int, name: str) -> str:
    """Capture the whole window to a debug file and return its path."""
    image, report = _capture_window_image(window_handle)
    path = _save_debug_crop(image, name)
    log_event(
        logger,
        logging.INFO,
        'window_screenshot_saved',
        window_handle=window_handle,
        path=path,
        window_size=image.size,
        strategy=report.get('chosen', '')
    )
    return path


def read_window_region(
        window_handle: int,
        left: int,
        top: int,
        width: int,
        height: int,
        allow_empty: bool,
        debug_name: str
) -> list[OcrLine]:
    """Read OCR lines from a pixel region expressed in window-relative pixels."""
    image, report = _capture_window_image(window_handle)
    image_width, image_height = image.size
    right = min(left + width, image_width)
    bottom = min(top + height, image_height)
    if left < 0 or top < 0 or right <= left or bottom <= top:
        raise RuntimeError(
            f'OCR 区域无效: hwnd={window_handle}, region=({left},{top},{width},{height}), '
            f'image={image_width}x{image_height}'
        )
    crop = image.crop((left, top, right, bottom))
    debug_path = _save_debug_crop(crop, debug_name)
    lines = _recognize_lines(crop)
    log_event(
        logger,
        logging.INFO,
        'ocr_region',
        window_handle=window_handle,
        window_size=(image_width, image_height),
        region=(left, top, right - left, bottom - top),
        strategy=report.get('chosen', ''),
        line_count=len(lines),
        sample=[line.text for line in lines[:8]],
        debug_image=debug_path
    )
    if not lines and not allow_empty:
        raise RuntimeError(
            f'无法识别微信界面文字: hwnd={window_handle}, '
            f'region=({left},{top},{right - left},{bottom - top}), '
            f'window={image_width}x{image_height}, strategy={report.get("chosen", "")}'
        )
    return [
        OcrLine(
            text=line.text,
            left=left + line.left,
            top=top + line.top,
            width=line.width,
            height=line.height
        )
        for line in lines
    ]


def read_wechat_chat_title(window_handle: int) -> str:
    """Read the active chat title from the message pane header."""
    left, top, right, bottom = win32gui.GetWindowRect(window_handle)
    scale = get_window_dpi_scale(window_handle)
    message_left = int(WeChat.MESSAGE_AREA_LEFT * scale)
    title_height = int(WeChat.CHAT_TITLE_HEIGHT * scale)
    window_width = right - left
    window_height = bottom - top
    if window_width <= message_left + int(120 * scale):
        raise RuntimeError(
            f'微信窗口过窄，消息区不可用: width={window_width}, '
            f'message_left={message_left}, scale={scale:.3f}'
        )
    lines = read_window_region(
        window_handle=window_handle,
        left=message_left,
        top=0,
        width=window_width - message_left,
        height=min(title_height, window_height),
        allow_empty=True,
        debug_name='wechat-mass-tool-title-crop.png'
    )
    title = ' '.join(line.text for line in lines)
    log_event(
        logger,
        logging.INFO,
        'chat_title_ocr',
        window_size=(window_width, window_height),
        scale=round(scale, 3),
        message_left=message_left,
        title=title,
        line_count=len(lines)
    )
    if not title:
        raise RuntimeError(
            f'无法识别微信聊天标题，请确认微信窗口可见且未最小化: '
            f'window={window_width}x{window_height}, message_left={message_left}'
        )
    return title


def normalize_ocr_text(text: str) -> str:
    """Normalize OCR text for case-insensitive containment checks."""
    return ''.join(text.split()).lower()
