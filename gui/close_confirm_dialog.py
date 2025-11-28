#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关闭确认对话框
"""

from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from logger import get_logger


class CloseConfirmDialog(QDialog):
    """关闭确认对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("close_dialog")
        self.logger.debug("初始化关闭确认对话框")
        
        # 对话框结果
        self.user_action = None  # "minimize_to_tray" 或 "exit_program"
        self.remember_choice = False
        
        self.init_ui()
        self.setup_style()
        
    def init_ui(self):
        """初始化用户界面"""
        try:
            self.setWindowTitle("关闭程序")
            self.setModal(True)
            self.setFixedSize(400, 200)
            
            # 主布局
            layout = QVBoxLayout()
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 问题标签
            question_label = QLabel("是否要关闭程序？")
            question_font = QFont()
            question_font.setPointSize(14)
            question_font.setBold(True)
            question_label.setFont(question_font)
            question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(question_label)
            
            # 说明文本
            info_label = QLabel("选择关闭方式：")
            info_font = QFont()
            info_font.setPointSize(11)
            info_label.setFont(info_font)
            layout.addWidget(info_label)
            
            # 按钮布局
            button_layout = QHBoxLayout()
            button_layout.setSpacing(10)
            
            # 关闭程序按钮
            self.exit_button = QPushButton("关闭程序")
            self.exit_button.setMinimumHeight(35)
            self.exit_button.clicked.connect(self.on_exit_clicked)
            button_layout.addWidget(self.exit_button)
            
            # 最小化到托盘按钮
            self.minimize_button = QPushButton("最小化到托盘")
            self.minimize_button.setMinimumHeight(35)
            self.minimize_button.clicked.connect(self.on_minimize_clicked)
            button_layout.addWidget(self.minimize_button)
            
            layout.addLayout(button_layout)
            
            # 分隔线
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(line)
            
            # 记住选择复选框
            self.remember_checkbox = QCheckBox("下次做同样选择")
            self.remember_checkbox.setFont(QFont("", 10))
            layout.addWidget(self.remember_checkbox)
            
            self.setLayout(layout)
            
            self.logger.debug("关闭确认对话框UI初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化关闭确认对话框UI失败: {e}", exc_info=True)
            raise
    
    def setup_style(self):
        """设置样式"""
        try:
            # 设置窗口样式
            self.setStyleSheet("""
                QDialog {
                    background-color: #f8f9fa;
                }
                QLabel {
                    color: #333333;
                }
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
                QCheckBox {
                    color: #666666;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #cccccc;
                    background-color: white;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #007bff;
                    background-color: #007bff;
                    border-radius: 3px;
                }
            """)
            
            # 设置退出按钮为红色
            self.exit_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            
            # 设置最小化按钮为蓝色
            self.minimize_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)
            
            self.logger.debug("对话框样式设置完成")
            
        except Exception as e:
            self.logger.warning(f"设置对话框样式失败: {e}")
    
    def on_exit_clicked(self):
        """关闭程序按钮点击事件"""
        try:
            self.user_action = "exit_program"
            self.remember_choice = self.remember_checkbox.isChecked()
            self.accept()
            self.logger.debug(f"用户选择关闭程序，记住选择: {self.remember_choice}")
            
        except Exception as e:
            self.logger.error(f"处理关闭程序按钮点击失败: {e}")
            self.reject()
    
    def on_minimize_clicked(self):
        """最小化到托盘按钮点击事件"""
        try:
            self.user_action = "minimize_to_tray"
            self.remember_choice = self.remember_checkbox.isChecked()
            self.accept()
            self.logger.debug(f"用户选择最小化到托盘，记住选择: {self.remember_choice}")
            
        except Exception as e:
            self.logger.error(f"处理最小化按钮点击失败: {e}")
            self.reject()
    
    def get_user_choice(self) -> Tuple[Optional[str], bool]:
        """获取用户选择结果"""
        return self.user_action, self.remember_choice
    
    @staticmethod
    def show_close_dialog(parent=None) -> Tuple[Optional[str], bool]:
        """显示关闭确认对话框的静态方法"""
        try:
            dialog = CloseConfirmDialog(parent)
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                return dialog.get_user_choice()
            else:
                return None, False
                
        except Exception as e:
            logger = get_logger("close_dialog")
            logger.error(f"显示关闭确认对话框失败: {e}", exc_info=True)
            return None, False


def show_close_confirm_dialog(parent=None) -> Tuple[Optional[str], bool]:
    """显示关闭确认对话框的便捷函数"""
    return CloseConfirmDialog.show_close_dialog(parent)
