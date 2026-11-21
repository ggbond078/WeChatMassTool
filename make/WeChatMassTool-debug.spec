# -*- mode: python ; coding: utf-8 -*-

import glob
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs


def collect_runtime_dlls():
    """Collect CPython runtime dependencies that conda ships under non-standard names."""
    patterns = (
        'ffi*.dll',
        'vcruntime*.dll',
        'msvcp140*.dll',
        'concrt140.dll',
        'vcomp140.dll',
        'mfc140*.dll',
    )
    collected = dict()
    for base in (
        os.path.join(sys.prefix, 'Library', 'bin'),
        os.path.join(sys.prefix, 'DLLs')
    ):
        for pattern in patterns:
            for candidate in glob.glob(os.path.join(base, pattern)):
                collected[os.path.basename(candidate)] = candidate
    return [(path, '.') for path in collected.values()]


binaries = collect_runtime_dlls()
binaries += collect_dynamic_libs('onnxruntime')
binaries += collect_dynamic_libs('shapely')
binaries += collect_dynamic_libs('numpy')
binaries += collect_dynamic_libs('cv2')
binaries += collect_dynamic_libs('pyclipper')

ocr_datas = collect_data_files('rapidocr_onnxruntime')

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=binaries,
    datas=[('../views/resources', 'views/resources')] + ocr_datas,
    hiddenimports=['rapidocr_onnxruntime', 'onnxruntime', 'shapely', 'pyclipper'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WeChatMassTool-debug',
    icon='../views/resources/images/favicon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
