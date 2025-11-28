#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘管理器
为网易云音乐桌面版提供纯Qt系统托盘功能
"""

import os
from typing import Optional
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QIcon, QAction

# 导入日志系统
from logger import get_logger


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
        # 尝试多种图标尺寸
        icon_paths = [
            "icon/icon_16x16.png",
            "icon/icon_24x24.png", 
            "icon/icon_32x32.png",
            "icon/icon_64x64.png",
            "NetEase_Music_icon.png"
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                self.logger.debug(f"找到托盘图标: {path}")
                return QIcon(path)
        
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
                        self._update_tray_display()
                        self.logger.info(f"歌曲信息更新: {self.current_song_info}")
                else:
                    self.logger.debug(f"歌曲信息提取失败: {result.get('error', '未知错误')}")
                    
        except Exception as e:
            self.logger.error(f"处理歌曲信息结果失败: {e}", exc_info=True)
    
    def _update_tray_display(self):
        """更新托盘显示信息"""
        try:
            if self.qt_tray:
                # Qt托盘更新工具提示
                self.qt_tray.setToolTip(self.current_song_info)
                
        except Exception as e:
            self.logger.error(f"更新托盘显示失败: {e}", exc_info=True)
    
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
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理系统托盘资源...")
            
            # 停止定时器
            if self.song_update_timer:
                self.song_update_timer.stop()
                self.song_update_timer = None
            
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
