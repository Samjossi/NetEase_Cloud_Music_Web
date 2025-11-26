#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 运行网易云音乐桌面版
"""

import subprocess
import sys
import os

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import PySide6
        import PySide6.QtWebEngineWidgets
        print("✓ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请先运行: pip install -r requirements.txt")
        return False

def main():
    print("正在启动网易云音乐桌面版...")
    
    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...")
        return
    
    # 运行主程序
    try:
        from main import main as app_main
        app_main()
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
