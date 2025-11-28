#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的系统托盘功能测试
验证托盘管理器的基本功能（不启动GUI）
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tray_imports():
    """测试托盘模块导入"""
    try:
        print("🔍 测试托盘模块导入...")
        
        # 测试基础导入
        from tray_manager import TrayManager, is_tray_supported, get_tray_backend
        print("✅ 托盘模块导入成功")
        
        # 测试系统支持检测
        supported = is_tray_supported()
        backend = get_tray_backend()
        print(f"✅ 系统托盘支持状态: {supported}")
        print(f"✅ 托盘后端: {backend}")
        
        # 测试依赖导入
        print("\n🔍 测试依赖导入...")
        
        # 测试PySide6
        try:
            from PySide6.QtWidgets import QSystemTrayIcon, QMenu
            from PySide6.QtCore import QObject, Signal, QTimer
            from PySide6.QtGui import QIcon, QAction
            print("✅ PySide6导入成功")
        except ImportError as e:
            print(f"❌ PySide6导入失败: {e}")
            return False
        
        # 测试AppIndicator3
        try:
            import gi
            gi.require_version('AppIndicator3', '0.1')
            from gi.repository import AppIndicator3 as appindicator
            from gi.repository import Gtk as gtk
            print("✅ AppIndicator3导入成功")
        except (ImportError, ValueError) as e:
            print(f"⚠️  AppIndicator3不可用: {e}")
            print("   这是正常的，将使用Qt备用方案")
        
        # 测试日志系统
        try:
            from logger import init_logging, get_logger
            print("✅ 日志系统导入成功")
        except ImportError as e:
            print(f"❌ 日志系统导入失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 导入测试失败: {e}")
        return False

def test_tray_class_structure():
    """测试托盘类结构"""
    try:
        print("\n🔍 测试托盘类结构...")
        
        from tray_manager import TrayManager
        
        # 检查类方法
        methods = [
            '__init__',
            '_init_tray',
            '_init_appindicator',
            '_init_qt_tray',
            'setup_system_tray',
            'set_webview',
            'cleanup',
            'show_window',
            'exit_application'
        ]
        
        for method in methods:
            if hasattr(TrayManager, method):
                print(f"✅ 方法存在: {method}")
            else:
                print(f"❌ 方法缺失: {method}")
                return False
        
        # 检查信号
        if hasattr(TrayManager, 'show_window_requested'):
            print("✅ 信号存在: show_window_requested")
        else:
            print("❌ 信号缺失: show_window_requested")
            return False
            
        if hasattr(TrayManager, 'exit_requested'):
            print("✅ 信号存在: exit_requested")
        else:
            print("❌ 信号缺失: exit_requested")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 类结构测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    try:
        print("\n🔍 测试项目文件结构...")
        
        required_files = [
            'tray_manager.py',
            'main.py',
            'requirements.txt'
        ]
        
        for file in required_files:
            if os.path.exists(file):
                print(f"✅ 文件存在: {file}")
            else:
                print(f"❌ 文件缺失: {file}")
                return False
        
        # 检查requirements.txt内容
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'PySide6' in content:
                print("✅ requirements.txt包含PySide6")
            else:
                print("❌ requirements.txt缺少PySide6")
                return False
                
            if 'PyGObject' in content:
                print("✅ requirements.txt包含PyGObject")
            else:
                print("❌ requirements.txt缺少PyGObject")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 文件结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 系统托盘功能简单测试 ===\n")
    
    tests = [
        ("文件结构测试", test_file_structure),
        ("模块导入测试", test_tray_imports),
        ("类结构测试", test_tray_class_structure),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 执行 {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} 通过")
                passed += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！系统托盘功能实现完成！")
        print("\n📝 使用说明:")
        print("1. 确保安装了所有依赖: pip install -r requirements.txt")
        print("2. 安装系统依赖 (Ubuntu/Debian): sudo apt-get install libappindicator3-1 gir1.2-appindicator3-0.1")
        print("3. 运行主程序: python main.py")
        print("4. 关闭窗口时会最小化到系统托盘")
        print("5. 右键托盘图标可以退出程序")
        return True
    else:
        print("❌ 部分测试失败，请检查实现")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
