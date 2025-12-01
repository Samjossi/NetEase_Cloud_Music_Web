#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终集成测试脚本
测试完整的PipeWire自动重启系统集成
"""

import sys
import time
import os
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit
from PySide6.QtCore import QTimer

# 导入我们的模块
from logger import init_logging, get_logger
from tray_manager import TrayManager
from profile_manager import get_profile_manager
from pipewire_manager import get_pipewire_manager


class FinalIntegrationTestWindow(QWidget):
    """最终集成测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("final_integration_test")
        self.init_ui()
        self.test_integration()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("PipeWire自动重启系统 - 最终集成测试")
        self.setGeometry(100, 100, 900, 700)
        
        layout = QVBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("正在测试系统集成...")
        layout.addWidget(self.status_label)
        
        # 测试结果区域
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # 手动测试按钮
        button_layout = QVBoxLayout()
        
        self.test_config_btn = QPushButton("测试配置系统")
        self.test_config_btn.clicked.connect(self.test_config_system)
        button_layout.addWidget(self.test_config_btn)
        
        self.test_pipewire_btn = QPushButton("测试PipeWire管理器")
        self.test_pipewire_btn.clicked.connect(self.test_pipewire_system)
        button_layout.addWidget(self.test_pipewire_btn)
        
        self.test_tray_btn = QPushButton("测试托盘管理器")
        self.test_tray_btn.clicked.connect(self.test_tray_system)
        button_layout.addWidget(self.test_tray_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def log_result(self, message: str, success: bool = True):
        """添加测试结果"""
        timestamp = time.strftime("%H:%M:%S")
        status = "✅" if success else "❌"
        self.results_text.append(f"[{timestamp}] {status} {message}")
        self.logger.info(message)
        
    def test_integration(self):
        """测试系统集成"""
        self.log_result("开始最终集成测试...")
        
        # 测试1: 配置系统
        try:
            profile_manager = get_profile_manager()
            config = profile_manager.get_pipewire_full_config()
            self.log_result(f"配置系统: 自动重启={config.get('auto_restart_enabled')}, 间隔={config.get('restart_interval_songs')}首歌")
        except Exception as e:
            self.log_result(f"配置系统测试失败: {e}", False)
        
        # 测试2: PipeWire管理器
        try:
            pipewire_manager = get_pipewire_manager()
            available = pipewire_manager._check_service_availability()
            self.log_result(f"PipeWire管理器: 服务可用={available}")
        except Exception as e:
            self.log_result(f"PipeWire管理器测试失败: {e}", False)
        
        # 测试3: 托盘管理器
        try:
            tray_manager = TrayManager(self)
            self.log_result(f"托盘管理器: 初始化成功={tray_manager.is_visible}")
            
            # 测试智能重启时机判断
            tray_manager.on_song_changed()
            is_good_time = tray_manager._is_good_restart_time()
            self.log_result(f"智能重启时机: 歌曲切换后判断={is_good_time}")
            
        except Exception as e:
            self.log_result(f"托盘管理器测试失败: {e}", False)
        
        self.status_label.setText("集成测试完成 - 查看下方结果")
        
    def test_config_system(self):
        """测试配置系统"""
        try:
            profile_manager = get_profile_manager()
            
            # 测试默认配置
            config = profile_manager._get_default_pipewire_config()
            self.log_result(f"默认配置: {config}")
            
            # 测试配置保存和加载
            success = profile_manager.save_pipewire_config(config)
            self.log_result(f"配置保存: {success}")
            
            loaded_config = profile_manager.load_pipewire_config()
            self.log_result(f"配置加载: 成功读取{len(loaded_config)}个配置项")
            
            # 测试时间格式化
            full_config = profile_manager.get_pipewire_full_config()
            self.log_result(f"完整配置: 下次重启={full_config.get('next_restart_countdown')}")
            
        except Exception as e:
            self.log_result(f"配置系统测试失败: {e}", False)
        
    def test_pipewire_system(self):
        """测试PipeWire系统"""
        try:
            pipewire_manager = get_pipewire_manager()
            
            # 测试服务检查
            available = pipewire_manager._check_service_availability()
            self.log_result(f"服务可用性检查: {available}")
            
            # 测试权限检查
            has_permission = pipewire_manager._check_user_permissions()
            self.log_result(f"用户权限检查: {has_permission}")
            
            # 测试重启命令（不执行）
            restart_cmd = "systemctl --user restart pipewire"
            self.log_result(f"重启命令: {restart_cmd}")
            
        except Exception as e:
            self.log_result(f"PipeWire系统测试失败: {e}", False)
        
    def test_tray_system(self):
        """测试托盘系统"""
        try:
            tray_manager = TrayManager(self)
            
            # 测试时间跟踪
            current_time = time.time()
            tray_manager.last_song_change_time = current_time
            tray_manager.on_playback_paused()
            
            self.log_result("模拟播放暂停和歌曲变化")
            
            # 检查重启时机
            is_good_time = tray_manager._is_good_restart_time()
            self.log_result(f"重启时机判断: {is_good_time}")
            
            # 测试倒计时
            countdown = tray_manager.get_next_restart_countdown()
            self.log_result(f"重启倒计时: {countdown}")
            
            # 测试用户活动更新
            tray_manager.update_user_activity()
            self.log_result("用户活动时间已更新")
            
        except Exception as e:
            self.log_result(f"托盘系统测试失败: {e}", False)


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
    window = FinalIntegrationTestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
