#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘管理器
为网易云音乐桌面版提供纯Qt系统托盘功能
"""

import os
import time
from typing import Optional
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QIcon, QAction

# 导入日志系统
from logger import get_logger
# 导入PipeWire管理器
from pipewire_manager import get_pipewire_manager
# 导入Profile管理器
from profile_manager import get_profile_manager


class TrayManager(QObject):
    """系统托盘管理器 - 纯Qt实现"""
    
    # 信号定义
    show_window_requested = Signal()
    exit_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("tray_manager")
        self.logger.info("正在初始化系统托盘管理器...")
        
        # 托盘相关属性
        self.is_visible = False
        self.qt_tray = None
        
        # PipeWire相关属性
        self.pipewire_timer = None
        self.pipewire_manager = None
        self.profile_manager = None
        
        # 初始化PipeWire管理器
        self._init_pipewire_manager()
        
        # 初始化托盘
        self._init_tray()
        
        self.logger.info("系统托盘管理器初始化完成，使用: Qt QSystemTrayIcon")
    
    def _init_tray(self):
        """初始化Qt系统托盘"""
        try:
            # 检查系统是否支持托盘
            if not QSystemTrayIcon.isSystemTrayAvailable():
                raise RuntimeError("系统不支持系统托盘功能")
            
            self.qt_tray = QSystemTrayIcon(self.parent())
            
            # 设置图标
            icon = self._get_qt_icon()
            if icon:
                self.qt_tray.setIcon(icon)
                self.logger.debug("使用自定义图标")
            else:
                # 创建一个简单的默认图标
                from PySide6.QtWidgets import QApplication, QWidget
                app = QApplication.instance()
                if app:
                    widget = QWidget()
                    default_icon = widget.style().standardIcon(
                        widget.style().StandardPixmap.SP_MediaVolume
                    )
                    self.qt_tray.setIcon(default_icon)
                    widget.deleteLater()
                self.logger.debug("使用默认图标")
            
            # 创建菜单
            menu = self._create_qt_menu()
            self.qt_tray.setContextMenu(menu)
            
            # 设置工具提示
            self.qt_tray.setToolTip("网易云音乐")
            
            # 连接点击事件（左键显示/隐藏窗口）
            self.qt_tray.activated.connect(self._on_tray_activated)
            
            # 显示托盘
            self.qt_tray.show()
            self.is_visible = True
            
            self.logger.info("Qt系统托盘初始化成功")
            
        except Exception as e:
            self.logger.error(f"Qt系统托盘初始化失败: {e}", exc_info=True)
            raise
    
    def _get_qt_icon(self) -> Optional[QIcon]:
        """获取Qt图标对象"""
        # 处理PyInstaller打包后的路径
        import sys
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller打包环境
            base_path = sys._MEIPASS
            self.logger.debug(f"PyInstaller打包环境，使用临时路径: {base_path}")
        else:
            # 开发环境
            base_path = os.getcwd()
            self.logger.debug(f"开发环境，使用当前路径: {base_path}")
        
        # 优先使用适合托盘显示的图标尺寸，按推荐顺序排列
        icon_paths = [
            "icon/icon_32x32.png",    # 托盘图标推荐尺寸
            "icon/icon_24x24.png",    # 小尺寸托盘
            "icon/icon_64x64.png",    # 高DPI显示器
            "icon/icon_16x16.png",    # 极小尺寸托盘
            "icon/icon_128x128.png",  # 超高DPI
            "icon/icon_256x256.png"   # 超高分辨率
        ]
        
        for path in icon_paths:
            full_path = os.path.join(base_path, path)
            if os.path.exists(full_path):
                self.logger.debug(f"找到托盘图标: {full_path}")
                icon = QIcon(full_path)
                if not icon.isNull():
                    return icon
                else:
                    self.logger.warning(f"图标文件损坏或无效: {full_path}")
        
        self.logger.warning("未找到合适的托盘图标文件")
        return None
    
    def _create_qt_menu(self) -> QMenu:
        """创建Qt右键菜单 - 简化版本"""
        try:
            menu = QMenu()
            
            # 显示/隐藏窗口菜单项
            show_hide_action = QAction("显示/隐藏窗口", self)
            show_hide_action.triggered.connect(self._on_qt_show_hide)
            menu.addAction(show_hide_action)
            
            # 分隔线
            menu.addSeparator()
            
            # 手动重启PipeWire菜单项
            pipewire_restart_action = QAction("手动重启PipeWire", self)
            pipewire_restart_action.triggered.connect(self._on_qt_pipewire_restart)
            menu.addAction(pipewire_restart_action)
            
            # 分隔线
            menu.addSeparator()
            
            # 设置菜单项
            settings_action = QAction("设置", self)
            settings_action.triggered.connect(self._on_qt_settings)
            menu.addAction(settings_action)
            
            # 分隔线
            menu.addSeparator()
            
            # 退出程序菜单项
            exit_action = QAction("退出程序", self)
            exit_action.triggered.connect(self._on_qt_exit)
            menu.addAction(exit_action)
            
            return menu
            
        except Exception as e:
            self.logger.error(f"创建Qt菜单失败: {e}", exc_info=True)
            raise
    
    def _on_tray_activated(self, reason):
        """处理Qt托盘点击事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 左键点击
            self.show_window_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Context:  # 右键点击
            # 菜单会自动显示，无需额外处理
            pass
    
    def _on_qt_show_hide(self):
        """Qt显示/隐藏窗口回调"""
        self.show_window_requested.emit()
    
    
    def _on_qt_pipewire_restart(self):
        """Qt手动重启PipeWire回调"""
        try:
            if self.pipewire_manager:
                self.logger.info("用户请求手动重启PipeWire")
                self._execute_pipewire_restart()
            else:
                self.logger.warning("PipeWire管理器未初始化")
                self._show_info_dialog("错误", "PipeWire管理器未初始化")
        except Exception as e:
            self.logger.error(f"手动重启PipeWire失败: {e}", exc_info=True)
    
    def _show_info_dialog(self, title: str, message: str):
        """显示信息对话框"""
        try:
            from PySide6.QtWidgets import QMessageBox
            from PySide6.QtCore import QObject
            
            # 创建消息框
            msg_box = QMessageBox()
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setIcon(QMessageBox.Icon.Information)
            
            # 显示对话框
            msg_box.exec()
            
        except Exception as e:
            self.logger.error(f"显示信息对话框失败: {e}", exc_info=True)
    
    def _on_qt_settings(self):
        """Qt设置回调"""
        # 发送设置请求信号到主窗口
        parent = self.parent()
        if parent and hasattr(parent, 'show_settings_dialog'):
            parent.show_settings_dialog()
        else:
            self.logger.warning("主窗口不支持设置对话框")
    
    def _on_qt_exit(self):
        """Qt退出程序回调"""
        self.exit_requested.emit()
    
    
    def show_window(self):
        """显示窗口的公共方法"""
        self.show_window_requested.emit()
    
    def hide_window(self):
        """隐藏窗口的公共方法"""
        # 这个方法主要用于外部调用，实际的隐藏逻辑在主窗口中
        pass
    
    def exit_application(self):
        """退出应用程序的公共方法"""
        self.exit_requested.emit()
    
    def _init_pipewire_manager(self):
        """初始化PipeWire管理器"""
        try:
            self.pipewire_manager = get_pipewire_manager()
            self.profile_manager = get_profile_manager()
            
            # 连接PipeWire信号
            self.pipewire_manager.restart_completed.connect(self._on_pipewire_restart_completed)
            self.pipewire_manager.service_status_changed.connect(self._on_pipewire_status_changed)
            
            # 启动PipeWire检查定时器
            self._start_pipewire_timer()
            
            self.logger.info("PipeWire管理器初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化PipeWire管理器失败: {e}", exc_info=True)
    
    def _start_pipewire_timer(self):
        """启动PipeWire检查定时器"""
        try:
            if self.pipewire_timer:
                self.pipewire_timer.stop()
            
            self.pipewire_timer = QTimer()
            self.pipewire_timer.timeout.connect(self._check_pipewire_restart)
            self.pipewire_timer.start(60000)  # 每分钟检查一次
            
            self.logger.debug("PipeWire检查定时器已启动")
            
        except Exception as e:
            self.logger.error(f"启动PipeWire检查定时器失败: {e}", exc_info=True)
    
    def _check_pipewire_restart(self):
        """检查是否需要执行PipeWire重启 - 基于分钟间隔的简化版本"""
        try:
            # 检查管理器是否可用
            if not self.profile_manager or not self.pipewire_manager:
                return
            
            # 检查自动重启是否启用
            if not self.profile_manager.is_pipewire_auto_restart_enabled():
                return
            
            # 获取配置
            config = self.profile_manager.load_pipewire_config()
            restart_interval_minutes = config.get("restart_interval_minutes", 90)
            last_restart = config.get("last_restart_timestamp", 0.0)
            
            # 如果间隔为0，表示不重启
            if restart_interval_minutes == 0:
                return
            
            # 检查是否到了重启时间
            current_time = time.time()
            
            # 修复：如果last_restart为0，表示从未重启过，设置为当前时间
            if last_restart <= 0.0:
                self.logger.info("检测到首次运行，初始化重启时间戳")
                self.profile_manager.update_pipewire_restart_time(current_time)
                return
            
            elapsed_seconds = current_time - last_restart
            elapsed_minutes = elapsed_seconds / 60
            
            # 添加边界检查，防止异常大的时间差
            if elapsed_minutes > 100000:  # 如果超过10万分钟，说明有问题
                self.logger.warning(f"检测到异常时间差: {elapsed_minutes:.1f}分钟，重置时间戳")
                self.profile_manager.update_pipewire_restart_time(current_time)
                return
            
            if elapsed_minutes >= restart_interval_minutes:
                self.logger.info(f"PipeWire重启时间已到: 已过{elapsed_minutes:.1f}分钟，间隔{restart_interval_minutes}分钟")
                self._execute_pipewire_restart()
            else:
                self.logger.debug(f"PipeWire重启检查: 已过{elapsed_minutes:.1f}分钟，需要{restart_interval_minutes}分钟")
                
        except Exception as e:
            self.logger.error(f"检查PipeWire重启失败: {e}", exc_info=True)
    
    
    def _execute_pipewire_restart(self):
        """执行PipeWire重启"""
        try:
            # 检查管理器是否可用
            if not self.profile_manager or not self.pipewire_manager:
                return
                
            self.logger.info("开始执行PipeWire自动重启...")
            
            # 显示通知
            if self.profile_manager.get_pipewire_full_config().get("show_notifications", True):
                self._show_restart_notification("正在重启PipeWire音频服务...")
            
            # 请求重启
            success = self.pipewire_manager.request_restart()
            
            if not success:
                self.logger.error("PipeWire重启请求失败")
                self._show_restart_notification("PipeWire重启失败", error=True)
            else:
                self.logger.info("PipeWire重启请求已发送")
                
        except Exception as e:
            self.logger.error(f"执行PipeWire重启失败: {e}", exc_info=True)
    
    def _show_restart_notification(self, message: str, error: bool = False):
        """显示重启通知"""
        try:
            if not self.qt_tray:
                return
            
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QPixmap
            
            app = QApplication.instance()
            if app:
                if error:
                    icon = app.style().standardIcon(app.style().StandardPixmap.SP_MessageBoxCritical)
                else:
                    icon = app.style().standardIcon(app.style().StandardPixmap.SP_MessageBoxInformation)
                
                # 显示托盘通知
                self.qt_tray.showMessage(
                    "PipeWire音频服务",
                    message,
                    icon,
                    5000  # 显示5秒
                )
                
        except Exception as e:
            self.logger.error(f"显示重启通知失败: {e}", exc_info=True)
    
    def _on_pipewire_restart_completed(self, success: bool, message: str):
        """PipeWire重启完成回调"""
        try:
            # 检查管理器是否可用
            if not self.profile_manager:
                return
                
            if success:
                self.logger.info(f"PipeWire自动重启成功: {message}")
                
                # 更新重启时间
                current_time = time.time()
                self.profile_manager.update_pipewire_restart_time(current_time)
                
                # 显示成功通知
                if self.profile_manager.get_pipewire_full_config().get("show_notifications", True):
                    self._show_restart_notification("PipeWire音频服务重启成功")
                    
            else:
                self.logger.error(f"PipeWire自动重启失败: {message}")
                
                # 显示失败通知
                if self.profile_manager.get_pipewire_full_config().get("show_notifications", True):
                    self._show_restart_notification(f"PipeWire重启失败: {message}", error=True)
                    
        except Exception as e:
            self.logger.error(f"处理PipeWire重启完成回调失败: {e}", exc_info=True)
    
    def _on_pipewire_status_changed(self, is_available: bool, message: str):
        """PipeWire状态变化回调 - 简化版本：只记录日志"""
        try:
            if is_available:
                self.logger.info(f"PipeWire服务状态: {message}")
            else:
                self.logger.warning(f"PipeWire服务状态异常: {message}")
                
        except Exception as e:
            self.logger.error(f"处理PipeWire状态变化失败: {e}", exc_info=True)
    
    
    def get_next_restart_countdown(self) -> str:
        """获取下次重启倒计时 - 基于分钟间隔"""
        try:
            if not self.profile_manager:
                return "未知"
            
            config = self.profile_manager.load_pipewire_config()
            restart_interval_minutes = config.get("restart_interval_minutes", 90)
            last_restart = config.get("last_restart_timestamp", 0.0)
            
            if restart_interval_minutes == 0:
                return "已禁用"
            
            if last_restart == 0.0:
                return "未开始"
            
            current_time = time.time()
            elapsed_seconds = current_time - last_restart
            elapsed_minutes = elapsed_seconds / 60
            
            remaining_minutes = restart_interval_minutes - elapsed_minutes
            
            if remaining_minutes <= 0:
                return "即将重启"
            elif remaining_minutes < 1:
                return f"{int(remaining_minutes * 60)}秒"
            elif remaining_minutes < 60:
                return f"{int(remaining_minutes)}分钟"
            else:
                hours = int(remaining_minutes // 60)
                minutes = int(remaining_minutes % 60)
                if minutes > 0:
                    return f"{hours}小时{minutes}分钟"
                else:
                    return f"{hours}小时"
                    
        except Exception as e:
            self.logger.error(f"获取重启倒计时失败: {e}")
            return "未知"
    
    def _update_tray_display(self):
        """更新托盘显示信息 - 简化版本"""
        try:
            if not self.qt_tray:
                return
            
            # 构建工具提示文本
            tooltip = "网易云音乐"
            
            # 如果PipeWire自动重启启用，添加倒计时信息
            if self.profile_manager and self.profile_manager.is_pipewire_auto_restart_enabled():
                countdown = self.get_next_restart_countdown()
                if countdown and countdown != "未设置" and countdown != "已过期":
                    tooltip += f"\n下次PipeWire重启: {countdown}"
            
            self.qt_tray.setToolTip(tooltip)
                
        except Exception as e:
            self.logger.error(f"更新托盘显示失败: {e}", exc_info=True)
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理系统托盘资源...")
            
            # 停止定时器
            if self.pipewire_timer:
                self.pipewire_timer.stop()
                self.pipewire_timer = None
            
            # 清理Qt托盘
            if self.qt_tray:
                self.qt_tray.hide()
                self.qt_tray = None
            
            self.is_visible = False
            self.logger.info("系统托盘资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理系统托盘资源失败: {e}", exc_info=True)


def is_tray_supported() -> bool:
    """检查系统是否支持托盘功能"""
    return QSystemTrayIcon.isSystemTrayAvailable()


def get_tray_backend() -> str:
    """获取当前使用的托盘后端"""
    if QSystemTrayIcon.isSystemTrayAvailable():
        return "Qt QSystemTrayIcon"
    else:
        return "None"
