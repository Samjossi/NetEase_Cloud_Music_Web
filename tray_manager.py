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
        self.song_update_timer = None
        self.current_song_info = "网易云音乐"
        
        # PipeWire相关属性
        self.pipewire_timer = None
        self.pipewire_manager = None
        self.profile_manager = None
        self.last_song_change_time = 0
        self.is_song_paused = False
        self.user_idle_time = 0
        self.last_user_activity = time.time()
        
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
            
            # 启动歌曲信息更新定时器
            self._start_song_update_timer()
            
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
        """创建Qt右键菜单"""
        try:
            menu = QMenu()
            
            # 显示/隐藏窗口菜单项
            show_hide_action = QAction("显示/隐藏窗口", self)
            show_hide_action.triggered.connect(self._on_qt_show_hide)
            menu.addAction(show_hide_action)
            
            # 分隔线
            menu.addSeparator()
            
            # PipeWire状态菜单项
            self.pipewire_status_action = QAction("PipeWire: 检查中...", self)
            self.pipewire_status_action.setEnabled(False)  # 初始状态禁用
            menu.addAction(self.pipewire_status_action)
            
            # PipeWire配置菜单项
            pipewire_config_action = QAction("PipeWire配置", self)
            pipewire_config_action.triggered.connect(self._on_qt_pipewire_config)
            menu.addAction(pipewire_config_action)
            
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
    
    def _on_qt_pipewire_config(self):
        """Qt PipeWire配置回调"""
        try:
            if self.profile_manager:
                config = self.profile_manager.get_pipewire_full_config()
                config_text = "PipeWire配置:\n\n"
                config_text += f"自动重启: {'启用' if config.get('auto_restart_enabled', False) else '禁用'}\n"
                config_text += f"重启间隔: {config.get('restart_interval_songs', 16)}首歌\n"
                config_text += f"显示通知: {'启用' if config.get('show_notifications', True) else '禁用'}\n"
                config_text += f"服务检查间隔: {config.get('service_check_interval', 30)}秒\n"
                config_text += f"重启超时: {config.get('restart_timeout', 10)}秒\n"
                
                if config.get('next_restart_countdown'):
                    config_text += f"\n下次重启倒计时: {config['next_restart_countdown']}"
                
                self._show_info_dialog("PipeWire配置", config_text)
            else:
                self.logger.warning("Profile管理器未初始化")
        except Exception as e:
            self.logger.error(f"显示PipeWire配置失败: {e}", exc_info=True)
    
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
    
    def _start_song_update_timer(self):
        """启动歌曲信息更新定时器"""
        try:
            if self.song_update_timer:
                self.song_update_timer.stop()
            
            self.song_update_timer = QTimer()
            self.song_update_timer.timeout.connect(self._update_song_info)
            self.song_update_timer.start(3000)  # 每3秒更新一次
            
            self.logger.debug("歌曲信息更新定时器已启动")
            
        except Exception as e:
            self.logger.error(f"启动歌曲更新定时器失败: {e}", exc_info=True)
    
    def _update_song_info(self):
        """更新歌曲信息显示"""
        try:
            # 这个方法需要从主窗口获取WebView实例来执行JavaScript
            # 我们将在主程序集成时提供WebView实例的引用
            if hasattr(self, 'web_view') and self.web_view:
                self._extract_song_info_from_webview()
            else:
                self.logger.debug("WebView未设置，跳过歌曲信息更新")
                
        except Exception as e:
            self.logger.error(f"更新歌曲信息失败: {e}", exc_info=True)
    
    def set_webview(self, web_view):
        """设置WebView实例用于获取歌曲信息"""
        self.web_view = web_view
        self.logger.debug("WebView实例已设置")
    
    def _extract_song_info_from_webview(self):
        """从WebView提取歌曲信息"""
        try:
            if not self.web_view:
                return
            
            # JavaScript代码提取歌曲信息
            js_code = """
            (function() {
                try {
                    // 多选择器匹配策略
                    var selectors = [
                        '.song-name',
                        '.current-song', 
                        '.music-name',
                        '.title',
                        '[class*="song"]',
                        '[class*="music"]',
                        '[class*="title"]',
                        '.player-song-name',
                        '.song-title',
                        '.music-title'
                    ];
                    
                    var songName = '';
                    var artistName = '';
                    
                    // 尝试获取歌曲名称
                    for (var i = 0; i < selectors.length; i++) {
                        var element = document.querySelector(selectors[i]);
                        if (element && element.textContent && element.textContent.trim()) {
                            songName = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 尝试获取艺术家名称
                    var artistSelectors = [
                        '.artist-name',
                        '.artist',
                        '.singer',
                        '[class*="artist"]',
                        '[class*="singer"]',
                        '.player-artist-name'
                    ];
                    
                    for (var i = 0; i < artistSelectors.length; i++) {
                        var element = document.querySelector(artistSelectors[i]);
                        if (element && element.textContent && element.textContent.trim()) {
                            artistName = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 组合显示信息
                    var displayInfo = '';
                    if (songName && artistName) {
                        displayInfo = songName + ' - ' + artistName;
                    } else if (songName) {
                        displayInfo = songName;
                    } else {
                        displayInfo = '网易云音乐';
                    }
                    
                    return {
                        success: true,
                        songName: songName,
                        artistName: artistName,
                        displayInfo: displayInfo,
                        url: window.location.href
                    };
                    
                } catch (e) {
                    return {
                        success: false,
                        error: e.message,
                        displayInfo: '网易云音乐'
                    };
                }
            })();
            """
            
            self.web_view.page().runJavaScript(js_code, self._on_song_info_result)
            
        except Exception as e:
            self.logger.error(f"提取歌曲信息失败: {e}", exc_info=True)
    
    def _on_song_info_result(self, result):
        """处理歌曲信息提取结果"""
        try:
            if result and isinstance(result, dict):
                if result.get("success"):
                    new_info = result.get("displayInfo", "网易云音乐")
                    if new_info != self.current_song_info:
                        self.current_song_info = new_info
                        self.on_song_changed()  # 通知歌曲变化
                        self._update_tray_display()
                        self.logger.info(f"歌曲信息更新: {self.current_song_info}")
                else:
                    self.logger.debug(f"歌曲信息提取失败: {result.get('error', '未知错误')}")
                    
        except Exception as e:
            self.logger.error(f"处理歌曲信息结果失败: {e}", exc_info=True)
    
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
        """检查是否需要执行PipeWire重启"""
        try:
            # 检查管理器是否可用
            if not self.profile_manager or not self.pipewire_manager:
                return
            
            # 检查自动重启是否启用
            if not self.profile_manager.is_pipewire_auto_restart_enabled():
                return
            
            # 检查是否应该跳过下次重启
            if self.profile_manager.should_skip_pipewire_restart():
                return
            
            # 检查是否到了重启时间
            if not self.profile_manager.is_pipewire_restart_due():
                return
            
            # 检查是否是合适的重启时机
            if self._is_good_restart_time():
                self._execute_pipewire_restart()
            else:
                self.logger.debug("当前不是PipeWire重启的合适时机")
                
        except Exception as e:
            self.logger.error(f"检查PipeWire重启失败: {e}", exc_info=True)
    
    def _is_good_restart_time(self) -> bool:
        """判断是否是合适的重启时机 - 简化版本：只检查歌曲切换间隙"""
        try:
            # 检查管理器是否可用
            if not self.profile_manager:
                return False
            
            # 只检查歌曲切换间隙（最近5秒内有歌曲变化）
            current_time = time.time()
            if (self.last_song_change_time > 0 and 
                current_time - self.last_song_change_time <= 5):
                self.logger.debug("检测到歌曲切换间隙，执行PipeWire重启")
                return True
            
            self.logger.debug("当前不是歌曲切换间隙，等待合适时机")
            return False
            
        except Exception as e:
            self.logger.error(f"判断重启时机失败: {e}", exc_info=True)
            return False
    
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
        """PipeWire状态变化回调"""
        try:
            # 更新托盘菜单中的PipeWire状态
            if hasattr(self, 'pipewire_status_action') and self.pipewire_status_action:
                if is_available:
                    status_text = f"PipeWire: 正常运行"
                    self.pipewire_status_action.setText(status_text)
                    self.logger.info(f"PipeWire服务状态: {message}")
                else:
                    status_text = f"PipeWire: 服务异常"
                    self.pipewire_status_action.setText(status_text)
                    self.logger.warning(f"PipeWire服务状态异常: {message}")
            else:
                if is_available:
                    self.logger.info(f"PipeWire服务状态: {message}")
                else:
                    self.logger.warning(f"PipeWire服务状态异常: {message}")
                
        except Exception as e:
            self.logger.error(f"处理PipeWire状态变化失败: {e}", exc_info=True)
    
    def update_user_activity(self):
        """更新用户活动时间"""
        self.last_user_activity = time.time()
    
    def on_song_changed(self):
        """歌曲变化回调"""
        self.last_song_change_time = time.time()
        self.logger.debug("检测到歌曲变化")
    
    def on_playback_paused(self):
        """播放暂停回调"""
        self.is_song_paused = True
        self.logger.debug("检测到播放暂停")
    
    def on_playback_resumed(self):
        """播放恢复回调"""
        self.is_song_paused = False
        self.logger.debug("检测到播放恢复")
    
    def get_next_restart_countdown(self) -> str:
        """获取下次重启倒计时"""
        try:
            if not self.profile_manager:
                return "未知"
            config = self.profile_manager.get_pipewire_full_config()
            return config.get("next_restart_countdown", "未设置")
        except Exception as e:
            self.logger.error(f"获取重启倒计时失败: {e}")
            return "未知"
    
    def _update_tray_display(self):
        """更新托盘显示信息"""
        try:
            if not self.qt_tray:
                return
            
            # 构建工具提示文本
            tooltip = self.current_song_info
            
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
            if self.song_update_timer:
                self.song_update_timer.stop()
                self.song_update_timer = None
            
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
