# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# 获取项目根目录
project_root = '/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web'
icon_dir = os.path.join(project_root, 'icon')
config_dir = os.path.join(project_root, 'config')
logger_dir = os.path.join(project_root, 'logger')
gui_dir = os.path.join(project_root, 'gui')

# 数据文件配置
datas = [
    (icon_dir, 'icon'),
    (config_dir, 'config'),
    (logger_dir, 'logger'),
    (gui_dir, 'gui'),
]

# 隐藏导入
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore',
    'PySide6.QtNetwork',
    'logger',
    'logger.formatters',
    'logger.handlers',
    'gui.main_window',
    'gui.settings_dialog',
    'gui.close_confirm_dialog',
    'profile_manager',
    'tray_manager',
]

# 排除不必要的模块
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'PIL',
    'cv2',
]

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NetEaseCloudMusic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(icon_dir, 'icon_256x256.png'),
)
