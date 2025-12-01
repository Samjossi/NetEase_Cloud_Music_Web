#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrayManager PipeWire功能测试脚本
用于测试TrayManager的PipeWire时间跟踪和智能重启功能
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit
from PySide6.QtCore import QObject

# 导入我们的模块
from tray_manager import TrayManager
from logger import init_logging, get_logger


class TrayManagerTestWindow(QWidget):
    """TrayManager PipeWire功能测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("tray_manager_test")
        self.init_ui()
        self.setup_tray_manager()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("TrayManager PipeWire功能测试")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("正在初始化...")
        layout.addWidget(self.status_label)
        
        # 测试按钮行
        button_layout1 = QVBoxLayout()
        
        self.test_song_change_btn = QPushButton("模拟歌曲变化")
        self.test_song_change_btn.clicked.connect(self.test_song_change)
        button_layout1.addWidget(self.test_song_change_btn)
        
        self.test_pause_btn = QPushButton("模拟播放暂停")
        self.test_pause_btn.clicked.connect(self.test_playback_paused)
        button_layout1.addWidget(self.test_pause_btn)
        
        self.test_resume_btn = QPushButton("模拟播放恢复")
        self.test_resume_btn.clicked.connect(self.test_playback_resumed)
        button_layout1.addWidget(self.test_resume_btn)
        
        self.test_activity_btn = QPushButton("模拟用户活动")
        self.test_activity_btn.clicked.connect(self.test_user_activity)
        button_layout1.addWidget(self.test_activity_btn)
        
        layout.addLayout(button_layout1)
        
        # 信息显示按钮行
        button_layout2 = QVBoxLayout()
        
        self.show_countdown_btn = QPushButton("显示重启倒计时")
        self.show_countdown_btn.clicked.connect(self.show_restart_countdown)
        button_layout2.addWidget(self.show_countdown_btn)
        
        self.check_restart_btn = QPushButton("检查重启时机")
        self.check_restart_btn.clicked.connect(self.check_restart_timing)
        button_layout2.addWidget(self.check_restart_btn)
        
        layout.addLayout(button_layout2)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        
    def setup_tray_manager(self):
        """设置TrayManager"""
        self.tray_manager = TrayManager(self)
        self.log_message("TrayManager初始化完成")
        
        # 更新状态
        if self.tray_manager.is_visible:
            self.status_label.setText("TrayManager状态: 正常运行")
        else:
            self.status_label.setText("TrayManager状态: 初始化失败")
        
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.logger.info(message)
        
    def test_song_change(self):
        """测试歌曲变化"""
        self.log_message("模拟歌曲变化...")
        self.tray_manager.on_song_changed()
        
    def test_playback_paused(self):
        """测试播放暂停"""
        self.log_message("模拟播放暂停...")
        self.tray_manager.on_playback_paused()
        
    def test_playback_resumed(self):
        """测试播放恢复"""
        self.log_message("模拟播放恢复...")
        self.tray_manager.on_playback_resumed()
        
    def test_user_activity(self):
        """测试用户活动"""
        self.log_message("模拟用户活动...")
        self.tray_manager.update_user_activity()
        
    def show_restart_countdown(self):
        """显示重启倒计时"""
        countdown = self.tray_manager.get_next_restart_countdown()
        self.log_message(f"下次PipeWire重启倒计时: {countdown}")
        
    def check_restart_timing(self):
        """检查重启时机"""
        self.log_message("检查当前是否是PipeWire重启的好时机...")
        
        # 获取当前状态
        current_time = time.time()
        last_song_change = self.tray_manager.last_song_change_time
        is_paused = self.tray_manager.is_song_paused
        last_activity = self.tray_manager.last_user_activity
        
        self.log_message(f"当前时间: {current_time}")
        self.log_message(f"上次歌曲变化: {last_song_change}")
        self.log_message(f"播放状态: {'暂停' if is_paused else '播放中'}")
        self.log_message(f"上次用户活动: {last_activity}")
        
        # 检查各种条件
        if is_paused:
            self.log_message("✅ 条件满足: 播放暂停")
        
        if last_song_change > 0 and current_time - last_song_change <= 5:
            self.log_message("✅ 条件满足: 歌曲切换间隙（5秒内）")
        
        if current_time - last_activity >= 30:
            self.log_message("✅ 条件满足: 用户空闲（30秒以上）")
        
        # 检查是否是好的重启时机
        is_good_time = self.tray_manager._is_good_restart_time()
        self.log_message(f"重启时机判断: {'好时机' if is_good_time else '不是好时机'}")


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
    window = TrayManagerTestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
