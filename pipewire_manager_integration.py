#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PipeWire管理器集成模块
提供PipeWire自动重启功能，不包含托盘创建
"""

import os
import time
from typing import Optional
from PySide6.QtCore import QObject, Signal, QTimer

# 导入日志系统
from logger import get_logger
# 导入PipeWire管理器
from pipewire_manager import get_pipewire_manager
# 导入Profile管理器
from profile_manager import get_profile_manager


class PipeWireManagerIntegration(QObject):
    """PipeWire管理器集成类 - 专注于PipeWire功能，不创建托盘"""
    
    # 信号定义
    restart_notification_requested = Signal(str, bool)  # message, is_error
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("pipewire_integration")
        self.logger.info("正在初始化PipeWire管理器集成...")
        
        # PipeWire相关属性
        self.pipewire_timer = None
        self.pipewire_manager = None
        self.profile_manager = None
        self.last_song_change_time = 0
        self.is_song_paused = False
        self.user_idle_time = 0
        self.last_user_activity = time.time()
        
        # WebView引用（用于获取歌曲信息）
        self.web_view = None
        
        # 初始化PipeWire管理器
        self._init_pipewire_manager()
        
        self.logger.info("PipeWire管理器集成初始化完成")
    
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
        """判断是否是合适的重启时机"""
        try:
            # 检查管理器是否可用
            if not self.profile_manager:
                return False
            
            # 优先级1: 用户暂停播放时
            if self.is_song_paused:
                self.logger.debug("检测到播放暂停，这是重启的好时机")
                return True
            
            # 优先级2: 歌曲切换间隙（最近5秒内有歌曲变化）
            current_time = time.time()
            if (self.last_song_change_time > 0 and 
                current_time - self.last_song_change_time <= 5):
                self.logger.debug("检测到歌曲切换间隙，这是重启的好时机")
                return True
            
            # 优先级3: 用户空闲时间超过30秒
            if current_time - self.last_user_activity >= 30:
                self.logger.debug("检测到用户空闲，这是重启的好时机")
                return True
            
            # 优先级4: 如果重启时间已过期超过5分钟，强制重启
            next_restart_time = self.profile_manager.get_pipewire_next_restart_time()
            if (next_restart_time > 0 and 
                current_time - next_restart_time >= 300):
                self.logger.warning("重启时间已过期超过5分钟，强制执行重启")
                return True
            
            self.logger.debug("当前不是重启的好时机")
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
            
            # 发送通知信号
            if self.profile_manager.get_pipewire_full_config().get("show_notifications", True):
                self.restart_notification_requested.emit("正在重启PipeWire音频服务...", False)
            
            # 请求重启
            success = self.pipewire_manager.request_restart()
            
            if not success:
                self.logger.error("PipeWire重启请求失败")
                self.restart_notification_requested.emit("PipeWire重启失败", True)
            else:
                self.logger.info("PipeWire重启请求已发送")
                
        except Exception as e:
            self.logger.error(f"执行PipeWire重启失败: {e}", exc_info=True)
    
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
                
                # 发送成功通知信号
                if self.profile_manager.get_pipewire_full_config().get("show_notifications", True):
                    self.restart_notification_requested.emit("PipeWire音频服务重启成功", False)
                    
            else:
                self.logger.error(f"PipeWire自动重启失败: {message}")
                
                # 发送失败通知信号
                if self.profile_manager.get_pipewire_full_config().get("show_notifications", True):
                    self.restart_notification_requested.emit(f"PipeWire重启失败: {message}", True)
                    
        except Exception as e:
            self.logger.error(f"处理PipeWire重启完成回调失败: {e}", exc_info=True)
    
    def _on_pipewire_status_changed(self, is_available: bool, message: str):
        """PipeWire状态变化回调"""
        try:
            if is_available:
                self.logger.info(f"PipeWire服务状态: {message}")
            else:
                self.logger.warning(f"PipeWire服务状态异常: {message}")
                
        except Exception as e:
            self.logger.error(f"处理PipeWire状态变化失败: {e}", exc_info=True)
    
    def set_webview(self, web_view):
        """设置WebView实例用于获取歌曲信息"""
        self.web_view = web_view
        self.logger.debug("WebView实例已设置")
        
        # 启动歌曲信息监控
        if self.web_view:
            self._start_song_monitoring()
    
    def _start_song_monitoring(self):
        """启动歌曲信息监控"""
        try:
            # 创建歌曲信息更新定时器
            self.song_update_timer = QTimer()
            self.song_update_timer.timeout.connect(self._update_song_info)
            self.song_update_timer.start(3000)  # 每3秒更新一次
            
            self.logger.debug("歌曲信息监控已启动")
            
        except Exception as e:
            self.logger.error(f"启动歌曲信息监控失败: {e}", exc_info=True)
    
    def _update_song_info(self):
        """更新歌曲信息"""
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
            self.logger.error(f"更新歌曲信息失败: {e}", exc_info=True)
    
    def _on_song_info_result(self, result):
        """处理歌曲信息提取结果"""
        try:
            if result and isinstance(result, dict):
                if result.get("success"):
                    new_info = result.get("displayInfo", "网易云音乐")
                    if new_info != self.current_song_info:
                        self.current_song_info = new_info
                        self.on_song_changed()  # 通知歌曲变化
                        self.logger.info(f"歌曲信息更新: {self.current_song_info}")
                else:
                    self.logger.debug(f"歌曲信息提取失败: {result.get('error', '未知错误')}")
                    
        except Exception as e:
            self.logger.error(f"处理歌曲信息结果失败: {e}", exc_info=True)
    
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
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理PipeWire管理器集成资源...")
            
            # 停止定时器
            if hasattr(self, 'song_update_timer') and self.song_update_timer:
                self.song_update_timer.stop()
                self.song_update_timer = None
            
            if self.pipewire_timer:
                self.pipewire_timer.stop()
                self.pipewire_timer = None
            
            self.logger.info("PipeWire管理器集成资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理PipeWire管理器集成资源失败: {e}", exc_info=True)
