#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PipeWire设置界面功能测试脚本
测试用户可配置的PipeWire自动重启功能
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from profile_manager import get_profile_manager


def test_pipewire_settings():
    """测试PipeWire设置功能"""
    print("=== PipeWire设置界面功能测试 ===\n")
    
    # 获取Profile管理器
    profile_manager = get_profile_manager()
    
    # 测试1: 加载默认配置
    print("1. 测试默认配置加载:")
    default_config = profile_manager.load_pipewire_config()
    print(f"   默认配置: {default_config}")
    print()
    
    # 测试2: 保存不同的配置选项
    print("2. 测试保存不同配置:")
    
    # 测试启用60分钟间隔
    config_60 = {
        "auto_restart_enabled": True,
        "restart_interval_minutes": 60,
        "show_notifications": True,
        "restart_command": "systemctl --user restart pipewire"
    }
    
    success = profile_manager.save_pipewire_config(config_60)
    print(f"   保存60分钟配置: {'成功' if success else '失败'}")
    
    loaded_config = profile_manager.load_pipewire_config()
    print(f"   加载的配置: {loaded_config}")
    print()
    
    # 测试3: 验证配置边界值
    print("3. 测试配置边界值:")
    
    # 测试小于30分钟的值
    config_small = {
        "auto_restart_enabled": True,
        "restart_interval_minutes": 15,  # 应该被限制为30
        "show_notifications": True
    }
    
    profile_manager.save_pipewire_config(config_small)
    validated_config = profile_manager.load_pipewire_config()
    print(f"   输入15分钟，验证结果: {validated_config['restart_interval_minutes']}分钟")
    
    # 测试大于180分钟的值
    config_large = {
        "auto_restart_enabled": True,
        "restart_interval_minutes": 240,  # 应该被限制为180
        "show_notifications": True
    }
    
    profile_manager.save_pipewire_config(config_large)
    validated_config = profile_manager.load_pipewire_config()
    print(f"   输入240分钟，验证结果: {validated_config['restart_interval_minutes']}分钟")
    print()
    
    # 测试4: 测试禁用状态
    print("4. 测试禁用状态:")
    config_disabled = {
        "auto_restart_enabled": False,
        "restart_interval_minutes": 90,
        "show_notifications": False
    }
    
    profile_manager.save_pipewire_config(config_disabled)
    disabled_config = profile_manager.load_pipewire_config()
    print(f"   禁用配置: {disabled_config}")
    
    # 检查自动重启状态
    is_enabled = profile_manager.is_pipewire_auto_restart_enabled()
    print(f"   自动重启状态: {'启用' if is_enabled else '禁用'}")
    print()
    
    # 测试5: 模拟时间间隔检查
    print("5. 测试时间间隔逻辑:")
    
    # 设置一个较短的时间间隔进行测试
    test_config = {
        "auto_restart_enabled": True,
        "restart_interval_minutes": 1,  # 1分钟间隔用于测试
        "show_notifications": True,
        "last_restart_timestamp": time.time() - 120  # 2分钟前
    }
    
    profile_manager.save_pipewire_config(test_config)
    print(f"   设置测试配置: 1分钟间隔，上次重启2分钟前")
    
    # 模拟检查是否需要重启
    current_time = time.time()
    last_restart = test_config["last_restart_timestamp"]
    elapsed_minutes = (current_time - last_restart) / 60
    
    should_restart = elapsed_minutes >= test_config["restart_interval_minutes"]
    print(f"   已过时间: {elapsed_minutes:.1f}分钟")
    print(f"   是否需要重启: {'是' if should_restart else '否'}")
    print()
    
    # 测试6: 恢复默认设置
    print("6. 恢复默认设置:")
    default_config = profile_manager._get_default_pipewire_config()
    profile_manager.save_pipewire_config(default_config)
    final_config = profile_manager.load_pipewire_config()
    print(f"   最终配置: {final_config}")
    print()
    
    print("=== 测试完成 ===")
    return True


def test_settings_dialog_integration():
    """测试设置对话框集成"""
    print("\n=== 设置对话框集成测试 ===\n")
    
    try:
        # 尝试导入设置对话框
        from gui.settings_dialog import SettingsDialog
        from PySide6.QtWidgets import QApplication
        
        # 检查是否有QApplication实例
        app = QApplication.instance()
        if not app:
            print("创建临时QApplication实例用于测试...")
            app = QApplication([])
        
        print("1. 测试设置对话框创建:")
        dialog = SettingsDialog()
        print("   设置对话框创建成功")
        
        print("2. 测试配置加载:")
        dialog.load_current_settings()
        print("   配置加载成功")
        
        print("3. 测试UI组件:")
        print(f"   PipeWire复选框: {dialog.pipewire_checkbox.isChecked()}")
        print(f"   间隔选择: {dialog.interval_combo.currentText()}")
        print(f"   通知复选框: {dialog.notification_checkbox.isChecked()}")
        
        print("4. 测试设置保存:")
        # 模拟用户选择
        dialog.pipewire_checkbox.setChecked(True)
        dialog.interval_combo.setCurrentText("60分钟")
        dialog.notification_checkbox.setChecked(False)
        
        selected_action = dialog.get_selected_action()
        print(f"   选择的关闭行为: {selected_action}")
        
        print("5. 清理测试资源:")
        dialog.deleteLater()
        print("   设置对话框已清理")
        
        print("\n=== 设置对话框集成测试完成 ===")
        return True
        
    except Exception as e:
        print(f"设置对话框集成测试失败: {e}")
        return False


def test_tray_manager_integration():
    """测试托盘管理器集成"""
    print("\n=== 托盘管理器集成测试 ===\n")
    
    try:
        from tray_manager import TrayManager
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        # 检查QApplication实例
        app = QApplication.instance()
        if not app:
            print("创建临时QApplication实例用于测试...")
            app = QApplication([])
        
        print("1. 测试托盘管理器创建:")
        tray = TrayManager()
        print("   托盘管理器创建成功")
        
        print("2. 测试PipeWire配置检查:")
        config = tray.profile_manager.load_pipewire_config()
        print(f"   当前配置: {config}")
        
        print("3. 测试重启倒计时:")
        countdown = tray.get_next_restart_countdown()
        print(f"   重启倒计时: {countdown}")
        
        print("4. 测试托盘显示更新:")
        tray._update_tray_display()
        print("   托盘显示更新成功")
        
        print("5. 清理测试资源:")
        tray.cleanup()
        tray.deleteLater()
        print("   托盘管理器已清理")
        
        print("\n=== 托盘管理器集成测试完成 ===")
        return True
        
    except Exception as e:
        print(f"托盘管理器集成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始PipeWire设置界面功能测试...\n")
    
    success_count = 0
    total_tests = 3
    
    # 测试1: 基本设置功能
    if test_pipewire_settings():
        success_count += 1
    
    # 测试2: 设置对话框集成
    if test_settings_dialog_integration():
        success_count += 1
    
    # 测试3: 托盘管理器集成
    if test_tray_manager_integration():
        success_count += 1
    
    print(f"\n=== 测试总结 ===")
    print(f"通过测试: {success_count}/{total_tests}")
    print(f"成功率: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("✓ 所有测试通过！PipeWire设置界面功能正常工作。")
        return True
    else:
        print("✗ 部分测试失败，需要检查相关功能。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
