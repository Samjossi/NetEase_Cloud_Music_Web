#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐一键打包工具
直接运行此文件即可启动打包GUI

使用方法:
    python3 pack.py
    
或者设置可执行权限后直接运行:
    chmod +x pack.py
    ./pack.py
"""

import sys
import os
from pathlib import Path

def main():
    """启动打包GUI"""
    print("🎵 网易云音乐桌面版 - 一键打包工具")
    print("=" * 50)
    
    # 获取项目根目录和打包GUI脚本路径
    project_root = Path(__file__).parent
    gui_script = project_root / "packaging" / "scripts" / "packaging_gui.py"
    
    # 检查GUI脚本是否存在
    if not gui_script.exists():
        print(f"❌ 错误: 找不到打包GUI脚本")
        print(f"   期望路径: {gui_script}")
        print(f"   请确保packaging目录完整")
        return 1
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print(f"❌ 错误: Python版本过低")
        print(f"   当前版本: {sys.version}")
        print(f"   需要版本: Python 3.8+")
        return 1
    
    # 添加脚本目录到Python路径
    sys.path.insert(0, str(gui_script.parent))
    
    print(f"✅ 项目根目录: {project_root}")
    print(f"✅ 打包脚本: {gui_script}")
    print(f"✅ Python版本: {sys.version.split()[0]}")
    
    try:
        # 导入并运行GUI
        print("\n🚀 正在启动打包GUI...")
        from packaging_gui import main as gui_main
        gui_main()
        
    except ImportError as e:
        print(f"❌ 导入GUI模块失败: {e}")
        print("   可能的解决方案:")
        print("   1. 检查packaging/scripts目录是否存在")
        print("   2. 检查packaging_gui.py文件是否完整")
        print("   3. 安装缺失的Python模块: pip install tkinter")
        return 1
        
    except Exception as e:
        print(f"❌ 启动GUI失败: {e}")
        print("   可能的解决方案:")
        print("   1. 检查系统是否支持GUI (X11/Wayland)")
        print("   2. 检查tkinter模块是否安装")
        print("   3. 尝试在终端中直接运行: python3 packaging/scripts/packaging_gui.py")
        return 1
    
    return 0

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    missing_deps = []
    
    # 检查tkinter
    try:
        import tkinter
        print("   ✅ tkinter - GUI框架")
    except ImportError:
        missing_deps.append("tkinter")
        print("   ❌ tkinter - GUI框架 (缺失)")
    
    # 检查pathlib (Python 3.4+ 内置)
    try:
        from pathlib import Path
        print("   ✅ pathlib - 路径处理")
    except ImportError:
        missing_deps.append("pathlib")
        print("   ❌ pathlib - 路径处理 (缺失)")
    
    # 检查subprocess (Python 内置)
    try:
        import subprocess
        print("   ✅ subprocess - 进程管理")
    except ImportError:
        missing_deps.append("subprocess")
        print("   ❌ subprocess - 进程管理 (缺失)")
    
    # 检查threading (Python 内置)
    try:
        import threading
        print("   ✅ threading - 多线程支持")
    except ImportError:
        missing_deps.append("threading")
        print("   ❌ threading - 多线程支持 (缺失)")
    
    if missing_deps:
        print(f"\n❌ 发现 {len(missing_deps)} 个缺失的依赖项")
        print("解决方案:")
        
        if "tkinter" in missing_deps:
            print("   • Ubuntu/Debian: sudo apt-get install python3-tk")
            print("   • CentOS/RHEL:   sudo yum install tkinter")
            print("   • Fedora:        sudo dnf install python3-tkinter")
        
        return False
    else:
        print("   🎉 所有依赖项检查通过!")
        return True

if __name__ == "__main__":
    print("正在检查系统环境...")
    
    # 检查依赖项
    if not check_dependencies():
        print("\n⚠️  依赖项检查失败，但仍然尝试启动GUI...")
        print("   如果GUI启动失败，请根据上述提示安装缺失的依赖项\n")
    
    # 启动GUI
    exit_code = main()
    
    if exit_code == 0:
        print("\n👋 感谢使用网易云音乐打包工具!")
    else:
        print(f"\n💥 程序异常退出，退出码: {exit_code}")
    
    sys.exit(exit_code)
