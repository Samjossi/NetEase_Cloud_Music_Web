# -*- mode: python ; coding: utf-8 -*-

"""
网易云音乐桌面版 - PyInstaller规格文件 v2.0
专注于兼容性和可靠性
自动生成于: build_spec.py
生成时间: 1764320360.5962744
"""

import os
import sys
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path("/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web")
PACKAGING_DIR = Path("/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/packaging_02")

# 分析主脚本
a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[
        str(PROJECT_ROOT),
        str(PROJECT_ROOT / "gui"),
        str(PROJECT_ROOT / "logger"),
    ],
    binaries=[],
    datas=[
        # 数据文件
        ('/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/icon/icon_128x128.png', 'icon'),
        ('/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/icon/icon_48x48.png', 'icon'),
        ('/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/icon/icon_256x256.png', 'icon'),
        ('/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/icon/icon_32x32.png', 'icon'),
        ('/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/icon/icon_16x16.png', 'icon'),
        ('/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/icon/icon_64x64.png', 'icon'),
        ('/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/icon/icon_24x24.png', 'icon'),
        ('/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/config/*', 'config'),
    ],
    hiddenimports=[
        # 隐藏导入
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtNetwork",
        "PySide6.QtPrintSupport",
        "PySide6.QtSvg",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "json",
        "os",
        "sys",
        "pathlib",
        "logging",
        "datetime",
        "threading",
        "subprocess",
        "time",
        "base64",
        "shutil",
        "tempfile",
        "traceback",
        "inspect",
        "types",
        "collections",
        "itertools",
        "functools",
        "re",
        "urllib",
        "urllib.parse",
        "urllib.request",
        "http.client",
        "socket",
        "ssl",
        "hashlib",
        "hmac",
        "secrets",
        "socketserver",
        "http.server",
        "email",
        "email.mime",
        "email.mime.text",
        "email.mime.multipart",
        "certifi",
        "idna",
    ],
    hookspath=[],
    hooksconfig={
        # PySide6特定钩子配置
        "PySide6": {
            "use-dependency-manifest": True,
            "collect-submodules": True,
            "collect-data": True,
        }
    },
    runtime_hooks=[
        # 运行时钩子，确保正确初始化
    ],
    excludes=[
        # 排除不需要的模块以减小大小
        "tkinter",
        "matplotlib",
        "scipy",
        "pandas",
        "notebook",
        "jupyter",
        "IPython",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 处理PYZ文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建可执行文件（单文件模式，确保最大兼容性）
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,     # 包含所有二进制文件
    a.zipfiles,      # 包含所有压缩文件
    a.datas,         # 包含所有数据文件
    [],
    name="NetEaseMusicDesktop",
    debug=False,     # 不包含调试信息
    bootloader_ignore_signals=False,
    strip=False,     # 不剥离符号（有助于调试）
    upx=True,        # 使用UPX压缩
    console=False,   # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Linux特定配置
    icon=None,       # 图标通过代码内部设置
    # 确保包含所有必要的库
    exclude_binaries=False,
)

# 单文件模式 - 不使用COLLECT，直接使用EXE
# 所有的datas和binaries都包含在EXE中，确保最大的兼容性
