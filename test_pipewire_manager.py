#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PipeWire管理器测试脚本
用于测试PipeWire服务管理器的基本功能
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit
from PySide6.QtCore import QObject

# 导入我们的模块
from pipewire_manager import get_pipewire_manager
from logger import init_logging, get_logger


class PipewireTestWindow(QWidget):
    """PipeWire管理器测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("pipewire_test")
        self.init_ui()
        self.setup_pipewire_manager()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("PipeWire管理器测试")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("正在初始化...")
        layout.addWidget(self.status_label)
        
        # 按钮
        self.check_service_btn = QPushButton("检查服务状态")
        self.check_service_btn.clicked.connect(self.check_service_status)
        layout.addWidget(self.check_service_btn)
        
        self.check_permission_btn = QPushButton("检查权限")
        self.check_permission_btn.clicked.connect(self.check_permissions)
        layout.addWidget(self.check_permission_btn)
        
        self.restart_btn = QPushButton("重启PipeWire")
        self.restart_btn.clicked.connect(self.restart_pipewire)
        layout.addWidget(self.restart_btn)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        
    def setup_pipewire_manager(self):
        """设置PipeWire管理器"""
        self.pipewire_manager = get_pipewire_manager()
        
        # 连接信号
        self.pipewire_manager.service_status_changed.connect(self.on_service_status_changed)
        self.pipewire_manager.permission_check_completed.connect(self.on_permission_check_completed)
        self.pipewire_manager.restart_requested.connect(self.on_restart_requested)
        self.pipewire_manager.restart_completed.connect(self.on_restart_completed)
        
        self.log_message("PipeWire管理器初始化完成")
        
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.logger.info(message)
        
    def check_service_status(self):
        """检查服务状态"""
        self.log_message("正在检查PipeWire服务状态...")
        self.pipewire_manager._check_service_availability()
        
    def check_permissions(self):
        """检查权限"""
        self.log_message("正在检查PipeWire重启权限...")
        self.pipewire_manager._check_user_permissions()
        
    def restart_pipewire(self):
        """重启PipeWire"""
        self.log_message("正在请求重启PipeWire服务...")
        success = self.pipewire_manager.request_restart()
        if not success:
            self.log_message("重启请求失败，请检查日志")
        
    def on_service_status_changed(self, is_available: bool, message: str):
        """服务状态变化回调"""
        status = "可用" if is_available else "不可用"
        self.status_label.setText(f"PipeWire服务状态: {status}")
        self.log_message(f"服务状态更新: {message}")
        
    def on_permission_check_completed(self, has_permission: bool, message: str):
        """权限检查完成回调"""
        permission = "有权限" if has_permission else "无权限"
        self.log_message(f"权限检查结果: {permission} - {message}")
        
    def on_restart_requested(self):
        """重启请求回调"""
        self.log_message("PipeWire重启请求已发出")
        self.restart_btn.setEnabled(False)
        
    def on_restart_completed(self, success: bool, message: str):
        """重启完成回调"""
        result = "成功" if success else "失败"
        self.log_message(f"PipeWire重启{result}: {message}")
        self.restart_btn.setEnabled(True)


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
    window = PipewireTestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
