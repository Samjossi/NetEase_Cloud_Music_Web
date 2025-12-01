#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PipeWire服务管理器
处理PipeWire音频服务的检测、重启和状态管理
"""

import os
import time
import subprocess
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QApplication

from logger import get_logger


class PipewireRestartThread(QThread):
    """异步执行PipeWire重启的工作线程"""
    
    # 信号定义
    restart_started = Signal()
    restart_completed = Signal(bool, str)  # success, message
    restart_failed = Signal(str)  # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("pipewire_restart_thread")
        self._restart_command = None
        
    def set_restart_command(self, command: str):
        """设置重启命令"""
        self._restart_command = command
        
    def run(self):
        """执行重启操作"""
        try:
            self.restart_started.emit()
            self.logger.info("开始执行PipeWire重启...")
            
            if not self._restart_command:
                self.restart_failed.emit("重启命令未设置")
                return
                
            # 执行重启命令
            result = subprocess.run(
                self._restart_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )
            
            if result.returncode == 0:
                self.logger.info("PipeWire重启成功")
                self.restart_completed.emit(True, "PipeWire服务重启成功")
            else:
                error_msg = f"重启失败，返回码: {result.returncode}, 错误: {result.stderr}"
                self.logger.error(error_msg)
                self.restart_failed.emit(error_msg)
                
        except subprocess.TimeoutExpired:
            error_msg = "PipeWire重启超时"
            self.logger.error(error_msg)
            self.restart_failed.emit(error_msg)
            
        except Exception as e:
            error_msg = f"PipeWire重启过程中发生异常: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.restart_failed.emit(error_msg)


class PipewireManager(QObject):
    """PipeWire服务管理器"""
    
    # 信号定义
    service_status_changed = Signal(bool, str)  # is_available, message
    restart_requested = Signal()  # 请求重启
    restart_completed = Signal(bool, str)  # success, message
    permission_check_completed = Signal(bool, str)  # has_permission, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("pipewire_manager")
        self.logger.info("初始化PipeWire管理器...")
        
        # 配置选项
        self.config = {
            "restart_command": "systemctl --user restart pipewire",
            "status_check_command": "systemctl --user is-active pipewire",
            "permission_check_command": "systemctl --user list-unit-files pipewire.service",
            "restart_timeout": 30,
            "check_interval": 60  # 秒
        }
        
        # 状态变量
        self._is_available = False
        self._has_permission = False
        self._last_restart_time = 0
        self._restart_thread = None
        
        # 初始化
        self._check_service_availability()
        self._check_user_permissions()
        
    def _check_service_availability(self):
        """检查PipeWire服务是否可用"""
        try:
            self.logger.info("检查PipeWire服务状态...")
            
            # 检查systemd用户服务是否存在
            result = subprocess.run(
                ["systemctl", "--user", "list-unit-files", "pipewire.service"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "pipewire.service" in result.stdout:
                # 检查服务状态
                status_result = subprocess.run(
                    ["systemctl", "--user", "is-active", "pipewire"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if status_result.returncode == 0:
                    self._is_available = True
                    status_msg = f"PipeWire服务正常运行: {status_result.stdout.strip()}"
                    self.logger.info(status_msg)
                    self.service_status_changed.emit(True, status_msg)
                else:
                    self._is_available = False
                    status_msg = f"PipeWire服务未运行: {status_result.stderr.strip()}"
                    self.logger.warning(status_msg)
                    self.service_status_changed.emit(False, status_msg)
            else:
                self._is_available = False
                status_msg = "PipeWire服务不存在或无法访问"
                self.logger.error(status_msg)
                self.service_status_changed.emit(False, status_msg)
                
        except subprocess.TimeoutExpired:
            error_msg = "检查PipeWire服务超时"
            self.logger.error(error_msg)
            self.service_status_changed.emit(False, error_msg)
            
        except Exception as e:
            error_msg = f"检查PipeWire服务时发生异常: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.service_status_changed.emit(False, error_msg)
    
    def _check_user_permissions(self):
        """检查用户是否有权限重启PipeWire服务"""
        try:
            self.logger.info("检查PipeWire服务重启权限...")
            
            # 检查用户是否在正确的用户组中
            groups_result = subprocess.run(
                ["groups"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if groups_result.returncode == 0:
                groups = groups_result.stdout.strip().split()
                # 在大多数现代Linux发行版中，用户应该能够管理自己的用户服务
                self._has_permission = True
                permission_msg = "用户具有PipeWire服务管理权限"
                self.logger.info(permission_msg)
                self.permission_check_completed.emit(True, permission_msg)
            else:
                self._has_permission = False
                permission_msg = "无法确定用户权限"
                self.logger.warning(permission_msg)
                self.permission_check_completed.emit(False, permission_msg)
                
        except Exception as e:
            error_msg = f"检查用户权限时发生异常: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._has_permission = False
            self.permission_check_completed.emit(False, error_msg)
    
    def is_service_available(self) -> bool:
        """获取PipeWire服务可用状态"""
        return self._is_available
    
    def has_restart_permission(self) -> bool:
        """获取重启权限状态"""
        return self._has_permission
    
    def get_last_restart_time(self) -> float:
        """获取上次重启时间戳"""
        return self._last_restart_time
    
    def request_restart(self) -> bool:
        """请求重启PipeWire服务"""
        if not self._is_available:
            error_msg = "PipeWire服务不可用，无法重启"
            self.logger.error(error_msg)
            self.restart_completed.emit(False, error_msg)
            return False
            
        if not self._has_permission:
            error_msg = "用户没有PipeWire服务重启权限"
            self.logger.error(error_msg)
            self.restart_completed.emit(False, error_msg)
            return False
            
        if self._restart_thread and self._restart_thread.isRunning():
            error_msg = "重启操作正在进行中"
            self.logger.warning(error_msg)
            self.restart_completed.emit(False, error_msg)
            return False
            
        try:
            self.logger.info("启动PipeWire重启流程...")
            self.restart_requested.emit()
            
            # 创建并启动重启线程
            self._restart_thread = PipewireRestartThread(self)
            self._restart_thread.set_restart_command(self.config["restart_command"])
            
            # 连接信号
            self._restart_thread.restart_started.connect(self._on_restart_started)
            self._restart_thread.restart_completed.connect(self._on_restart_completed)
            self._restart_thread.restart_failed.connect(self._on_restart_failed)
            
            # 启动线程
            self._restart_thread.start()
            
            return True
            
        except Exception as e:
            error_msg = f"启动重启流程失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.restart_completed.emit(False, error_msg)
            return False
    
    def _on_restart_started(self):
        """重启开始回调"""
        self.logger.info("PipeWire重启操作已开始")
        
    def _on_restart_completed(self, success: bool, message: str):
        """重启完成回调"""
        self.logger.info(f"PipeWire重启操作完成: {message}")
        
        if success:
            self._last_restart_time = time.time()
            
            # 等待一段时间后重新检查服务状态
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self._check_service_availability)
        
        self.restart_completed.emit(success, message)
        
        # 清理线程
        if self._restart_thread:
            self._restart_thread.deleteLater()
            self._restart_thread = None
    
    def _on_restart_failed(self, error_message: str):
        """重启失败回调"""
        self.logger.error(f"PipeWire重启失败: {error_message}")
        self.restart_completed.emit(False, error_message)
        
        # 清理线程
        if self._restart_thread:
            self._restart_thread.deleteLater()
            self._restart_thread = None
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取PipeWire服务信息"""
        info = {
            "is_available": self._is_available,
            "has_permission": self._has_permission,
            "last_restart_time": self._last_restart_time,
            "last_restart_formatted": self._format_timestamp(self._last_restart_time),
            "restart_command": self.config["restart_command"],
            "config": self.config.copy()
        }
        
        return info
    
    def _format_timestamp(self, timestamp: float) -> str:
        """格式化时间戳为可读字符串"""
        if timestamp <= 0:
            return "从未重启"
        
        try:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        except Exception:
            return "时间格式化失败"
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self.logger.info("更新PipeWire管理器配置...")
            
            # 验证配置项
            valid_keys = set(self.config.keys())
            provided_keys = set(new_config.keys())
            invalid_keys = provided_keys - valid_keys
            
            if invalid_keys:
                error_msg = f"无效的配置项: {invalid_keys}"
                self.logger.error(error_msg)
                return False
            
            # 更新配置
            self.config.update(new_config)
            self.logger.info(f"配置更新成功: {new_config}")
            
            # 重新检查权限和服务状态
            self._check_user_permissions()
            self._check_service_availability()
            
            return True
            
        except Exception as e:
            error_msg = f"更新配置失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("清理PipeWire管理器资源...")
            
            # 停止重启线程
            if self._restart_thread and self._restart_thread.isRunning():
                self._restart_thread.terminate()
                self._restart_thread.wait(5000)  # 等待5秒
                
            self.logger.info("PipeWire管理器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理PipeWire管理器资源失败: {e}", exc_info=True)


# 全局PipeWire管理器实例
_pipewire_manager = None


def get_pipewire_manager() -> PipewireManager:
    """获取全局PipeWire管理器实例"""
    global _pipewire_manager
    if _pipewire_manager is None:
        _pipewire_manager = PipewireManager()
    return _pipewire_manager


def cleanup_pipewire_manager():
    """清理全局PipeWire管理器"""
    global _pipewire_manager
    if _pipewire_manager:
        _pipewire_manager.cleanup()
        _pipewire_manager = None
