#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置对话框
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QGroupBox, QRadioButton,
    QButtonGroup, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from logger import get_logger


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("settings_dialog")
        self.logger.debug("初始化设置对话框")
        
        # 对话框结果
        self.settings_changed = False
        
        self.init_ui()
        self.setup_style()
        self.load_current_settings()
        
    def init_ui(self):
        """初始化用户界面"""
        try:
            self.setWindowTitle("设置")
            self.setModal(True)
            self.setFixedSize(500, 450)
            
            # 主布局
            layout = QVBoxLayout()
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 标题
            title_label = QLabel("应用程序设置")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)
            
            # PipeWire设置组
            pipewire_group = QGroupBox("PipeWire自动重启")
            pipewire_layout = QVBoxLayout()
            
            # 重启间隔设置
            interval_layout = QHBoxLayout()
            interval_label = QLabel("重启间隔：")
            interval_layout.addWidget(interval_label)
            
            self.interval_combo = QComboBox()
            self.interval_combo.addItems(["60分钟", "90分钟", "120分钟", "从不重启"])
            self.interval_combo.setCurrentText("90分钟")
            interval_layout.addWidget(self.interval_combo)
            interval_layout.addStretch()
            
            pipewire_layout.addLayout(interval_layout)
            
            # 通知设置
            self.notification_checkbox = QCheckBox("显示重启通知")
            self.notification_checkbox.setChecked(True)
            pipewire_layout.addWidget(self.notification_checkbox)
            
            pipewire_group.setLayout(pipewire_layout)
            layout.addWidget(pipewire_group)
            
            # 关闭行为设置组
            close_group = QGroupBox("关闭行为")
            close_layout = QVBoxLayout()
            
            # 说明文本
            info_label = QLabel("选择点击关闭按钮时的默认行为：")
            info_label.setFont(QFont("", 10))
            close_layout.addWidget(info_label)
            
            # 单选按钮组
            self.close_button_group = QButtonGroup(self)
            
            # 询问选项
            self.ask_radio = QRadioButton("每次询问关闭方式")
            self.ask_radio.setChecked(True)
            self.close_button_group.addButton(self.ask_radio, 0)
            close_layout.addWidget(self.ask_radio)
            
            # 最小化到托盘选项
            self.minimize_radio = QRadioButton("最小化到系统托盘")
            self.close_button_group.addButton(self.minimize_radio, 1)
            close_layout.addWidget(self.minimize_radio)
            
            # 退出程序选项
            self.exit_radio = QRadioButton("直接退出程序")
            self.close_button_group.addButton(self.exit_radio, 2)
            close_layout.addWidget(self.exit_radio)
            
            close_group.setLayout(close_layout)
            layout.addWidget(close_group)
            
            # 重置设置按钮
            reset_layout = QHBoxLayout()
            reset_layout.addStretch()
            
            self.reset_button = QPushButton("重置为默认设置")
            self.reset_button.clicked.connect(self.reset_to_default)
            reset_layout.addWidget(self.reset_button)
            
            layout.addLayout(reset_layout)
            
            # 按钮布局
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # 取消按钮
            self.cancel_button = QPushButton("取消")
            self.cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(self.cancel_button)
            
            # 确定按钮
            self.ok_button = QPushButton("确定")
            self.ok_button.clicked.connect(self.accept_changes)
            button_layout.addWidget(self.ok_button)
            
            layout.addLayout(button_layout)
            
            self.setLayout(layout)
            
            self.logger.debug("设置对话框UI初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化设置对话框UI失败: {e}", exc_info=True)
            raise
    
    def setup_style(self):
        """设置样式"""
        try:
            # 设置窗口样式
            self.setStyleSheet("""
                QDialog {
                    background-color: #f8f9fa;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QLabel {
                    color: #333333;
                }
                QRadioButton {
                    color: #333333;
                    spacing: 8px;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #cccccc;
                    border-radius: 8px;
                    background-color: white;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #007bff;
                    background-color: #007bff;
                }
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
                QPushButton#reset_button {
                    background-color: #6c757d;
                }
                QPushButton#reset_button:hover {
                    background-color: #5a6268;
                }
                QPushButton#cancel_button {
                    background-color: #6c757d;
                }
                QPushButton#cancel_button:hover {
                    background-color: #5a6268;
                }
                QPushButton#ok_button {
                    background-color: #28a745;
                }
                QPushButton#ok_button:hover {
                    background-color: #218838;
                }
            """)
            
            # 设置按钮对象名称
            self.reset_button.setObjectName("reset_button")
            self.cancel_button.setObjectName("cancel_button")
            self.ok_button.setObjectName("ok_button")
            
            self.logger.debug("对话框样式设置完成")
            
        except Exception as e:
            self.logger.warning(f"设置对话框样式失败: {e}")
    
    def load_current_settings(self):
        """加载当前设置"""
        try:
            if hasattr(self.parent(), 'profile_manager') and self.parent().profile_manager:
                # 加载关闭行为设置
                close_behavior = self.parent().profile_manager.get_close_behavior()
                action = close_behavior.get("action", "ask")
                
                self.logger.debug(f"加载当前关闭行为设置: {action}")
                
                # 设置对应的单选按钮
                if action == "ask":
                    self.ask_radio.setChecked(True)
                elif action == "minimize_to_tray":
                    self.minimize_radio.setChecked(True)
                elif action == "exit_program":
                    self.exit_radio.setChecked(True)
                else:
                    # 默认选择询问
                    self.ask_radio.setChecked(True)
                
                # 加载PipeWire设置
                pipewire_config = self.parent().profile_manager.load_pipewire_config()
                auto_restart_enabled = pipewire_config.get("auto_restart_enabled", False)
                restart_interval = pipewire_config.get("restart_interval_minutes", 90)
                show_notifications = pipewire_config.get("show_notifications", True)
                
                self.logger.debug(f"加载PipeWire设置: 启用={auto_restart_enabled}, 间隔={restart_interval}分钟, 通知={show_notifications}")
                
                # 设置通知选项
                self.notification_checkbox.setChecked(show_notifications)
                
                # 设置重启间隔（根据auto_restart_enabled状态来决定显示什么）
                if not auto_restart_enabled:
                    self.interval_combo.setCurrentText("从不重启")
                elif restart_interval == 60:
                    self.interval_combo.setCurrentText("60分钟")
                elif restart_interval == 90:
                    self.interval_combo.setCurrentText("90分钟")
                elif restart_interval == 120:
                    self.interval_combo.setCurrentText("120分钟")
                else:
                    # 如果间隔无效但启用状态为true，使用默认值
                    self.interval_combo.setCurrentText("90分钟")
                    
            else:
                self.logger.warning("无法访问Profile管理器，使用默认设置")
                # 设置默认值
                self.ask_radio.setChecked(True)
                self.interval_combo.setCurrentText("从不重启")
                self.notification_checkbox.setChecked(True)
                
        except Exception as e:
            self.logger.error(f"加载当前设置失败: {e}")
            # 设置默认值
            self.ask_radio.setChecked(True)
            self.interval_combo.setCurrentText("从不重启")
            self.notification_checkbox.setChecked(True)
    
    def get_selected_action(self) -> str:
        """获取用户选择的关闭行为"""
        checked_id = self.close_button_group.checkedId()
        
        if checked_id == 0:
            return "ask"
        elif checked_id == 1:
            return "minimize_to_tray"
        elif checked_id == 2:
            return "exit_program"
        else:
            return "ask"  # 默认值
    
    def accept_changes(self):
        """接受设置更改"""
        try:
            selected_action = self.get_selected_action()
            self.logger.info(f"用户选择关闭行为: {selected_action}")
            
            # 获取PipeWire设置
            interval_text = self.interval_combo.currentText()
            show_notifications = self.notification_checkbox.isChecked()
            
            # 根据下拉框选择自动判断是否启用重启和间隔
            if interval_text == "60分钟":
                pipewire_enabled = True
                restart_interval = 60
            elif interval_text == "90分钟":
                pipewire_enabled = True
                restart_interval = 90
            elif interval_text == "120分钟":
                pipewire_enabled = True
                restart_interval = 120
            else:  # "从不重启"
                pipewire_enabled = False
                restart_interval = 0
            
            self.logger.info(f"用户选择PipeWire设置: 启用={pipewire_enabled}, 间隔={restart_interval}分钟, 通知={show_notifications}")
            
            if hasattr(self.parent(), 'profile_manager') and self.parent().profile_manager:
                # 保存关闭行为设置
                close_success = self.parent().profile_manager.update_close_behavior(
                    selected_action, 
                    remember_choice=False  # 不记住选择，让用户下次仍然可以更改
                )
                
                # 保存PipeWire设置
                pipewire_success = self.parent().profile_manager.save_pipewire_config({
                    "auto_restart_enabled": pipewire_enabled,
                    "restart_interval_minutes": restart_interval,
                    "show_notifications": show_notifications,
                    "restart_command": "systemctl --user restart pipewire"
                })
                
                if close_success and pipewire_success:
                    self.logger.info("设置保存成功")
                    self.settings_changed = True
                    self.accept()
                else:
                    self.logger.error("设置保存失败")
                    QMessageBox.warning(self, "错误", "保存设置失败，请重试。")
            else:
                self.logger.error("无法访问Profile管理器")
                QMessageBox.warning(self, "错误", "无法保存设置，请重试。")
                
        except Exception as e:
            self.logger.error(f"接受设置更改失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置时发生错误：{e}")
    
    def reset_to_default(self):
        """重置为默认设置"""
        try:
            self.logger.info("用户请求重置为默认设置")
            
            reply = QMessageBox.question(
                self, 
                "确认重置", 
                "确定要重置所有设置为默认值吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if hasattr(self.parent(), 'profile_manager') and self.parent().profile_manager:
                    # 重置为默认设置
                    success = self.parent().profile_manager.update_close_behavior("ask", False)
                    
                    if success:
                        self.logger.info("设置重置成功")
                        # 重新加载设置
                        self.load_current_settings()
                        QMessageBox.information(self, "成功", "设置已重置为默认值。")
                    else:
                        self.logger.error("设置重置失败")
                        QMessageBox.warning(self, "错误", "重置设置失败，请重试。")
                else:
                    self.logger.error("无法访问Profile管理器")
                    QMessageBox.warning(self, "错误", "无法重置设置，请重试。")
                    
        except Exception as e:
            self.logger.error(f"重置设置失败: {e}")
            QMessageBox.critical(self, "错误", f"重置设置时发生错误：{e}")
    
    @staticmethod
    def show_settings_dialog(parent=None) -> bool:
        """显示设置对话框的静态方法"""
        try:
            dialog = SettingsDialog(parent)
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                return dialog.settings_changed
            else:
                return False
                
        except Exception as e:
            logger = get_logger("settings_dialog")
            logger.error(f"显示设置对话框失败: {e}", exc_info=True)
            return False


def show_settings_dialog(parent=None) -> bool:
    """显示设置对话框的便捷函数"""
    return SettingsDialog.show_settings_dialog(parent)
