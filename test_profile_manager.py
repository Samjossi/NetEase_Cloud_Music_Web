#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ProfileManager PipeWire配置测试脚本
用于测试PipeWire相关配置的存储和管理功能
"""

import sys
import time
import json
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit, QComboBox
from PySide6.QtCore import QObject

# 导入我们的模块
from profile_manager import get_profile_manager
from logger import init_logging, get_logger


class ProfileManagerTestWindow(QWidget):
    """ProfileManager PipeWire配置测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("profile_manager_test")
        self.init_ui()
        self.setup_profile_manager()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("ProfileManager PipeWire配置测试")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("正在初始化...")
        layout.addWidget(self.status_label)
        
        # 测试按钮行
        button_layout1 = QVBoxLayout()
        
        self.load_config_btn = QPushButton("加载PipeWire配置")
        self.load_config_btn.clicked.connect(self.load_pipewire_config)
        button_layout1.addWidget(self.load_config_btn)
        
        self.save_default_config_btn = QPushButton("保存默认配置")
        self.save_default_config_btn.clicked.connect(self.save_default_config)
        button_layout1.addWidget(self.save_default_config_btn)
        
        self.check_restart_due_btn = QPushButton("检查重启时间")
        self.check_restart_due_btn.clicked.connect(self.check_restart_due)
        button_layout1.addWidget(self.check_restart_due_btn)
        
        layout.addLayout(button_layout1)
        
        # 配置修改按钮行
        button_layout2 = QVBoxLayout()
        
        self.toggle_auto_restart_btn = QPushButton("切换自动重启")
        self.toggle_auto_restart_btn.clicked.connect(self.toggle_auto_restart)
        button_layout2.addWidget(self.toggle_auto_restart_btn)
        
        self.update_interval_btn = QPushButton("更新重启间隔为2小时")
        self.update_interval_btn.clicked.connect(self.update_restart_interval)
        button_layout2.addWidget(self.update_interval_btn)
        
        self.simulate_restart_btn = QPushButton("模拟重启")
        self.simulate_restart_btn.clicked.connect(self.simulate_restart)
        button_layout2.addWidget(self.simulate_restart_btn)
        
        self.toggle_skip_btn = QPushButton("切换跳过下次重启")
        self.toggle_skip_btn.clicked.connect(self.toggle_skip_restart)
        button_layout2.addWidget(self.toggle_skip_btn)
        
        layout.addLayout(button_layout2)
        
        # 间隔选择
        interval_layout = QVBoxLayout()
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["0.5小时", "1小时", "2小时", "4小时", "8小时", "12小时", "24小时"])
        self.interval_combo.setCurrentIndex(1)  # 默认1小时
        self.interval_combo.currentTextChanged.connect(self.on_interval_changed)
        
        interval_layout.addWidget(QLabel("选择重启间隔:"))
        interval_layout.addWidget(self.interval_combo)
        layout.addLayout(interval_layout)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        
    def setup_profile_manager(self):
        """设置ProfileManager"""
        self.profile_manager = get_profile_manager()
        self.log_message("ProfileManager初始化完成")
        
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.logger.info(message)
        
    def load_pipewire_config(self):
        """加载PipeWire配置"""
        self.log_message("正在加载PipeWire配置...")
        
        try:
            config = self.profile_manager.get_pipewire_full_config()
            
            self.log_message("=== PipeWire配置信息 ===")
            self.log_message(f"自动重启启用: {config.get('auto_restart_enabled', '未知')}")
            self.log_message(f"重启间隔: {config.get('restart_interval_hours', '未知')}小时")
            self.log_message(f"显示通知: {config.get('show_notifications', '未知')}")
            self.log_message(f"上次重启: {config.get('last_restart_formatted', '未知')}")
            self.log_message(f"上次重启相对时间: {config.get('last_restart_relative', '未知')}")
            self.log_message(f"下次重启: {config.get('next_restart_formatted', '未知')}")
            self.log_message(f"下次重启倒计时: {config.get('next_restart_countdown', '未知')}")
            self.log_message(f"重启过期: {config.get('restart_overdue', '未知')}")
            self.log_message(f"跳过下次重启: {config.get('skip_next_restart', '未知')}")
            self.log_message(f"重启命令: {config.get('restart_command', '未知')}")
            
            # 更新状态标签
            status = "启用" if config.get('auto_restart_enabled', False) else "禁用"
            self.status_label.setText(f"PipeWire自动重启状态: {status}")
            
        except Exception as e:
            self.log_message(f"加载PipeWire配置失败: {e}")
            
    def save_default_config(self):
        """保存默认配置"""
        self.log_message("正在保存默认PipeWire配置...")
        
        try:
            default_config = self.profile_manager._get_default_pipewire_config()
            success = self.profile_manager.save_pipewire_config(default_config)
            
            if success:
                self.log_message("默认PipeWire配置保存成功")
            else:
                self.log_message("默认PipeWire配置保存失败")
                
        except Exception as e:
            self.log_message(f"保存默认配置失败: {e}")
            
    def check_restart_due(self):
        """检查是否到了重启时间"""
        self.log_message("检查PipeWire重启时间...")
        
        try:
            is_due = self.profile_manager.is_pipewire_restart_due()
            should_skip = self.profile_manager.should_skip_pipewire_restart()
            
            self.log_message(f"重启时间已到: {is_due}")
            self.log_message(f"跳过下次重启: {should_skip}")
            
            if is_due and not should_skip:
                self.log_message("✅ 应该执行PipeWire重启")
            elif is_due and should_skip:
                self.log_message("⏭️ 重启时间已到但跳过")
            else:
                self.log_message("⏰ 还未到重启时间")
                
        except Exception as e:
            self.log_message(f"检查重启时间失败: {e}")
            
    def toggle_auto_restart(self):
        """切换自动重启状态"""
        try:
            current_state = self.profile_manager.is_pipewire_auto_restart_enabled()
            new_state = not current_state
            
            success = self.profile_manager.enable_pipewire_auto_restart(new_state)
            
            if success:
                status = "启用" if new_state else "禁用"
                self.log_message(f"PipeWire自动重启已{status}")
                
                # 更新状态标签
                self.status_label.setText(f"PipeWire自动重启状态: {status}")
            else:
                self.log_message("切换自动重启状态失败")
                
        except Exception as e:
            self.log_message(f"切换自动重启状态失败: {e}")
            
    def update_restart_interval(self):
        """更新重启间隔"""
        self.log_message("更新重启间隔为2小时...")
        
        try:
            success = self.profile_manager.set_pipewire_restart_interval(2.0)
            
            if success:
                self.log_message("重启间隔已更新为2小时")
                
                # 检查新的下次重启时间
                next_time = self.profile_manager.get_pipewire_next_restart_time()
                if next_time > 0:
                    next_formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(next_time))
                    self.log_message(f"下次重启时间: {next_formatted}")
                else:
                    self.log_message("下次重启时间未设置")
            else:
                self.log_message("更新重启间隔失败")
                
        except Exception as e:
            self.log_message(f"更新重启间隔失败: {e}")
            
    def on_interval_changed(self, text: str):
        """间隔选择变化"""
        # 提取数字
        try:
            if "0.5小时" in text:
                interval = 0.5
            elif "1小时" in text:
                interval = 1.0
            elif "2小时" in text:
                interval = 2.0
            elif "4小时" in text:
                interval = 4.0
            elif "8小时" in text:
                interval = 8.0
            elif "12小时" in text:
                interval = 12.0
            elif "24小时" in text:
                interval = 24.0
            else:
                return
                
            success = self.profile_manager.set_pipewire_restart_interval(interval)
            
            if success:
                self.log_message(f"重启间隔已更新为{interval}小时")
            else:
                self.log_message("更新重启间隔失败")
                
        except Exception as e:
            self.log_message(f"更新重启间隔失败: {e}")
            
    def simulate_restart(self):
        """模拟重启"""
        self.log_message("模拟PipeWire重启...")
        
        try:
            current_time = time.time()
            success = self.profile_manager.update_pipewire_restart_time(current_time)
            
            if success:
                self.log_message(f"模拟重启时间已记录: {current_time}")
                
                # 显示更新后的配置
                config = self.profile_manager.get_pipewire_full_config()
                self.log_message(f"下次重启时间: {config.get('next_restart_formatted', '未知')}")
                self.log_message(f"下次重启倒计时: {config.get('next_restart_countdown', '未知')}")
            else:
                self.log_message("模拟重启失败")
                
        except Exception as e:
            self.log_message(f"模拟重启失败: {e}")
            
    def toggle_skip_restart(self):
        """切换跳过下次重启"""
        try:
            current_skip = self.profile_manager.should_skip_pipewire_restart()
            new_skip = not current_skip
            
            success = self.profile_manager.set_skip_pipewire_restart(new_skip)
            
            if success:
                status = "跳过" if new_skip else "不跳过"
                self.log_message(f"已设置下次重启{status}")
            else:
                self.log_message("设置跳过重启失败")
                
        except Exception as e:
            self.log_message(f"设置跳过重启失败: {e}")


def main():
    """主函数"""
    # 初始化日志系统
    logger_manager = init_logging(
        level="INFO",
        console_output=True,
        file_output=False,
        json_output=False
    )
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = ProfileManagerTestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
