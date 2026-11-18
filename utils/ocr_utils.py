# -*- coding: utf-8 -*-
"""Windows OCR helpers for locating WeChat search results and chat titles."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple

import win32gui
import uiautomation as auto


OCR_TIMEOUT_SECOND = 15
OCR_RETRY_COUNT = 2

auto.SetProcessDpiAwareness(auto.ProcessDpiAwareness.PerMonitorDpiAware)


class OcrLine(NamedTuple):
    text: str
    left: int
    top: int
    width: int
    height: int


def _build_ocr_script(
        window_handle: int,
        window_left: int,
        window_top: int,
        window_width: int,
        window_height: int,
        image_path: str,
        crop_left_fraction: float,
        crop_top_fraction: float,
        crop_width_fraction: float,
        crop_height_fraction: float
) -> str:
    return f"""
$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Runtime.WindowsRuntime
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WeChatOcrWindow {{
    [DllImport("user32.dll")]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
}}
"@
$width = {window_width}
$height = {window_height}
$localCropX = [int]($width * {crop_left_fraction:.6f})
$localCropY = [int]($height * {crop_top_fraction:.6f})
$cropX = {window_left} + $localCropX
$cropY = {window_top} + $localCropY
$cropWidth = [Math]::Max(1, [int]($width * {crop_width_fraction:.6f}))
$cropHeight = [Math]::Max(1, [int]($height * {crop_height_fraction:.6f}))
$fullBitmap = New-Object System.Drawing.Bitmap $width, $height
$fullGraphics = [System.Drawing.Graphics]::FromImage($fullBitmap)
$fullHdc = $fullGraphics.GetHdc()
if (-not [WeChatOcrWindow]::PrintWindow([IntPtr]{window_handle}, $fullHdc, 2)) {{
    $fullGraphics.ReleaseHdc($fullHdc)
    $fullGraphics.Dispose()
    $fullBitmap.Dispose()
    throw 'PrintWindow failed'
}}
$fullGraphics.ReleaseHdc($fullHdc)
$fullGraphics.Dispose()
$bitmap = New-Object System.Drawing.Bitmap $cropWidth, $cropHeight
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$sourceRect = New-Object System.Drawing.Rectangle $localCropX, $localCropY, $cropWidth, $cropHeight
$targetRect = New-Object System.Drawing.Rectangle 0, 0, $cropWidth, $cropHeight
$graphics.DrawImage($fullBitmap, $targetRect, $sourceRect, [System.Drawing.GraphicsUnit]::Pixel)
$fullBitmap.Dispose()
$bitmap.Save('{image_path}', [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.FileAccessMode,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime] | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
}})[0]
function Await($operation, $resultType) {{
    $method = $asTaskGeneric.MakeGenericMethod($resultType)
    $task = $method.Invoke($null, @($operation))
    $task.Wait(-1) | Out-Null
    $task.Result
}}
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync('{image_path}')) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$softwareBitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$language = [Windows.Globalization.Language]::new('zh-Hans-CN')
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
if ($null -eq $engine) {{ throw 'Windows OCR zh-Hans-CN is unavailable' }}
$result = Await ($engine.RecognizeAsync($softwareBitmap)) ([Windows.Media.Ocr.OcrResult])
foreach ($line in $result.Lines) {{
    $minX = 999999
    $minY = 999999
    $maxX = 0
    $maxY = 0
    foreach ($word in $line.Words) {{
        $bounds = $word.BoundingRect
        if ($bounds.X -lt $minX) {{ $minX = $bounds.X }}
        if ($bounds.Y -lt $minY) {{ $minY = $bounds.Y }}
        if (($bounds.X + $bounds.Width) -gt $maxX) {{ $maxX = $bounds.X + $bounds.Width }}
        if (($bounds.Y + $bounds.Height) -gt $maxY) {{ $maxY = $bounds.Y + $bounds.Height }}
    }}
    "{{0}}`t{{1}}`t{{2}}`t{{3}}`t{{4}}" -f $line.Text, ($cropX + $minX), ($cropY + $minY), ($maxX - $minX), ($maxY - $minY)
}}
"""


def _read_ocr_lines(
        window_handle: int,
        crop_left_fraction: float,
        crop_top_fraction: float,
        crop_width_fraction: float,
        crop_height_fraction: float,
        allow_empty: bool
) -> list[OcrLine]:
    image_path = str(Path(tempfile.gettempdir()) / 'wechat-mass-tool-ocr.png')
    script_path = Path(tempfile.gettempdir()) / 'wechat-mass-tool-ocr.ps1'
    window_left, window_top, window_right, window_bottom = win32gui.GetWindowRect(window_handle)
    script = _build_ocr_script(
        window_handle=window_handle,
        window_left=window_left,
        window_top=window_top,
        window_width=window_right - window_left,
        window_height=window_bottom - window_top,
        image_path=image_path,
        crop_left_fraction=crop_left_fraction,
        crop_top_fraction=crop_top_fraction,
        crop_width_fraction=crop_width_fraction,
        crop_height_fraction=crop_height_fraction
    )
    script_path.write_text(script, encoding='utf-8-sig')
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = subprocess.SW_HIDE
    last_error = ''
    for attempt in range(OCR_RETRY_COUNT):
        try:
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
                timeout=OCR_TIMEOUT_SECOND,
                check=False,
                startupinfo=startup_info
            )
        except subprocess.TimeoutExpired as error:
            last_error = str(error)
            continue
        lines = list()
        for row in result.stdout.splitlines():
            columns = row.split('\t', 4)
            if len(columns) != 5:
                continue
            try:
                lines.append(OcrLine(
                    text=columns[0],
                    left=int(columns[1]),
                    top=int(columns[2]),
                    width=int(columns[3]),
                    height=int(columns[4])
                ))
            except ValueError:
                last_error = f'Invalid OCR row: {row}'
        if result.returncode == 0:
            if lines:
                return lines
            if allow_empty:
                return list()
        last_error = result.stderr.strip() or f'PowerShell exited with {result.returncode}'
        if attempt + 1 < OCR_RETRY_COUNT:
            print(f'OCR attempt {attempt + 1} failed: {last_error}')
    raise RuntimeError(f'无法识别微信界面文字: {last_error}')


def read_wechat_chat_title(window_handle: int) -> str:
    """Read the active chat title from the top-left area of the message pane."""
    lines = _read_ocr_lines(
        window_handle=window_handle,
        crop_left_fraction=0.20,
        crop_top_fraction=0.0,
        crop_width_fraction=0.40,
        crop_height_fraction=0.12,
        allow_empty=False
    )
    return ' '.join(line.text for line in lines)


def read_window_text_lines(
        window_handle: int,
        crop_left_fraction: float,
        crop_top_fraction: float,
        crop_width_fraction: float,
        crop_height_fraction: float,
        allow_empty: bool
) -> list[OcrLine]:
    """Read OCR lines from a fractional region of a window."""
    return _read_ocr_lines(
        window_handle=window_handle,
        crop_left_fraction=crop_left_fraction,
        crop_top_fraction=crop_top_fraction,
        crop_width_fraction=crop_width_fraction,
        crop_height_fraction=crop_height_fraction,
        allow_empty=allow_empty
    )


def normalize_ocr_text(text: str) -> str:
    """Normalize OCR text for case-insensitive containment checks."""
    return ''.join(text.split()).lower()
