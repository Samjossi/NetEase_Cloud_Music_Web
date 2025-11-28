# -*- mode: python ; coding: utf-8 -*-

"""
网易云音乐桌面版 - PyInstaller规格文件
自动生成于: build_spec.py
"""

import os
import sys
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path("/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web")
PACKAGING_DIR = Path("/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/packaging_01")

# 分析主脚本
a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        # 包含图标文件
        (str(PROJECT_ROOT / "icon" / "*"), "icon"),
        # 包含配置文件
        (str(PROJECT_ROOT / "config" / "*"), "config"),
        # 如果有其他资源文件，也添加到这里
    ],
    hiddenimports=[
        # PySide6相关
        "PySide6.QtCore",
        "PySide6.QtGui", 
        "PySide6.QtWidgets",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtNetwork",
        # 应用模块
        "gui",
        "logger", 
        "profile_manager",
        "tray_manager",
        # 可能需要的其他模块
        "json",
        "os",
        "sys",
        "pathlib",
        "logging",
        "datetime",
        "threading",
        "subprocess",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 处理PYZ文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建可执行文件（单文件模式）
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # 包含所有二进制文件
    a.zipfiles,   # 包含所有压缩文件
    a.datas,     # 包含所有数据文件（包括图标文件）
    [],
    name="NetEaseMusicDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 设置为False，这样就不会显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    # 移除Windows和macOS特定配置，专注于Linux环境
    # 注意：在Linux上，图标显示主要通过代码中的路径解析和设置来确保
)

# 单文件模式 - 不使用COLLECT，直接使用EXE
# 所有的datas和binaries都包含在EXE中
