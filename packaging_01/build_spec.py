#!/usr/bin/env python3
"""
PyInstaller规格文件生成器
为网易云音乐桌面版生成合适的.spec文件
"""

import os
import sys
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
PACKAGING_DIR = Path(__file__).parent

def create_spec_file():
    """创建PyInstaller规格文件"""
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

"""
网易云音乐桌面版 - PyInstaller规格文件
自动生成于: {Path(__file__).name}
"""

import os
import sys
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path("{PROJECT_ROOT}")
PACKAGING_DIR = Path("{PACKAGING_DIR}")

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
    hooksconfig={{}},
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
'''

    # 写入规格文件
    spec_file = PACKAGING_DIR / "netease_music.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ PyInstaller规格文件已生成: {spec_file}")
    return spec_file

def main():
    """主函数"""
    print("=== PyInstaller规格文件生成器 ===")
    
    # 检查项目结构
    if not PROJECT_ROOT.exists():
        print(f"错误: 项目根目录不存在: {PROJECT_ROOT}")
        sys.exit(1)
    
    main_py = PROJECT_ROOT / "main.py"
    if not main_py.exists():
        print(f"错误: 主脚本不存在: {main_py}")
        sys.exit(1)
    
    icon_dir = PROJECT_ROOT / "icon"
    if not icon_dir.exists():
        print(f"警告: 图标目录不存在: {icon_dir}")
    
    # 创建规格文件
    spec_file = create_spec_file()
    
    print(f"✓ 规格文件生成完成: {spec_file}")
    print("✓ 可以运行PyInstaller进行打包了")

if __name__ == "__main__":
    main()
