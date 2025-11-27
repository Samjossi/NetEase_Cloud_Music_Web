#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统主模块
提供统一的日志配置和接口
"""

import os
import sys
import logging
import logging.config
import traceback
import time
from typing import Optional, Dict, Any
from pathlib import Path

from .formatters import ColoredFormatter, DetailedFormatter, SimpleFormatter, JSONFormatter
from .handlers import (
    AsyncFileHandler, SmartRotatingFileHandler, MultiFileHandler,
    ContextFilter, LoginDataFilter, WebViewFilter, ErrorFilter, PerformanceFilter
)


class NetEaseLogger:
    """网易云音乐专用日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.multi_handler = MultiFileHandler(str(self.log_dir))
        self._initialized = False
        self._startup_time = time.time()
        
    def setup_logging(self, 
                     level: str = "INFO",
                     console_output: bool = True,
                     file_output: bool = True,
                     json_output: bool = False) -> None:
        """设置日志系统"""
        
        if self._initialized:
            return
        
        # 设置根日志级别
        root_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(root_level)
        
        # 清除现有处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        colored_formatter = ColoredFormatter()
        detailed_formatter = DetailedFormatter()
        simple_formatter = SimpleFormatter()
        json_formatter = JSONFormatter() if json_output else None
        
        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(colored_formatter)
            console_handler.setLevel(root_level)
            console_handler.addFilter(ContextFilter("NetEaseMusic"))
            root_logger.addHandler(console_handler)
        
        # 主应用日志文件
        if file_output:
            app_handler = self.multi_handler.get_handler(
                "app", 
                handler_type="rotating",
                formatter=detailed_formatter,
                maxBytes=20*1024*1024,  # 20MB
                backupCount=10
            )
            app_handler.setLevel(root_level)
            app_handler.addFilter(ContextFilter("NetEaseMusic"))
            root_logger.addHandler(app_handler)
            
            # 错误日志单独记录
            error_handler = self.multi_handler.get_handler(
                "error",
                handler_type="rotating", 
                formatter=simple_formatter,
                maxBytes=10*1024*1024,
                backupCount=5
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.addFilter(ErrorFilter())
            error_handler.addFilter(ContextFilter("NetEaseMusic"))
            root_logger.addHandler(error_handler)
            
            # 登录相关日志
            login_handler = self.multi_handler.get_handler(
                "login",
                handler_type="rotating",
                formatter=simple_formatter,
                maxBytes=5*1024*1024,
                backupCount=3
            )
            login_handler.setLevel(logging.DEBUG)
            login_handler.addFilter(LoginDataFilter())
            login_handler.addFilter(ContextFilter("NetEaseMusic"))
            root_logger.addHandler(login_handler)
            
            # WebView相关日志
            webview_handler = self.multi_handler.get_handler(
                "webview",
                handler_type="rotating",
                formatter=simple_formatter,
                maxBytes=10*1024*1024,
                backupCount=5
            )
            webview_handler.setLevel(logging.DEBUG)
            webview_handler.addFilter(WebViewFilter())
            webview_handler.addFilter(ContextFilter("NetEaseMusic"))
            root_logger.addHandler(webview_handler)
            
            # 性能日志
            perf_handler = self.multi_handler.get_handler(
                "performance",
                handler_type="rotating",
                formatter=json_formatter or detailed_formatter,
                maxBytes=5*1024*1024,
                backupCount=3
            )
            perf_handler.setLevel(logging.INFO)
            perf_handler.addFilter(PerformanceFilter())
            perf_handler.addFilter(ContextFilter("NetEaseMusic"))
            root_logger.addHandler(perf_handler)
        
        # 设置全局异常处理器
        self._setup_exception_handler()
        
        self._initialized = True
        
        # 记录启动信息
        logger = self.get_logger("system")
        logger.info("=== 网易云音乐桌面版启动 ===")
        logger.info(f"日志系统初始化完成，级别: {level}")
        logger.info(f"日志目录: {self.log_dir.absolute()}")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"工作目录: {os.getcwd()}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        return logging.getLogger(f"NetEaseMusic.{name}")
    
    def _setup_exception_handler(self):
        """设置全局异常处理器"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            logger = self.get_logger("exception")
            logger.critical(
                "未捕获的异常",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # 同时记录到错误文件
            error_logger = logging.getLogger("NetEaseMusic.error")
            error_logger.critical(
                "未捕获的异常",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
        
        sys.excepthook = handle_exception
    
    def log_startup_performance(self):
        """记录启动性能"""
        startup_time = time.time() - self._startup_time
        logger = self.get_logger("performance")
        logger.info(f"应用启动耗时: {startup_time:.3f}秒", extra={'extra_data': {
            'startup_time': startup_time,
            'event': 'app_startup_complete'
        }})
    
    def log_login_data_operation(self, operation: str, path: str, success: bool, details: str = ""):
        """记录登录数据操作"""
        logger = self.get_logger("login")
        if success:
            logger.info(f"登录数据操作成功: {operation}", extra={'extra_data': {
                'operation': operation,
                'path': path,
                'details': details
            }})
        else:
            logger.error(f"登录数据操作失败: {operation}", extra={'extra_data': {
                'operation': operation,
                'path': path,
                'error': details
            }})
    
    def log_webview_event(self, event: str, url: str = "", success: bool = True, details: str = ""):
        """记录WebView事件"""
        logger = self.get_logger("webview")
        if success:
            logger.info(f"WebView事件: {event}", extra={'extra_data': {
                'event': event,
                'url': url,
                'details': details
            }})
        else:
            logger.error(f"WebView事件失败: {event}", extra={'extra_data': {
                'event': event,
                'url': url,
                'error': details
            }})
    
    def close(self):
        """关闭日志系统"""
        self.multi_handler.close_all()
        self._initialized = False


# 全局日志管理器实例
_logger_manager = None


def init_logging(log_dir: str = "logs", 
                level: str = "INFO",
                console_output: bool = True,
                file_output: bool = True,
                json_output: bool = False) -> NetEaseLogger:
    """初始化日志系统"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = NetEaseLogger(log_dir)
        _logger_manager.setup_logging(level, console_output, file_output, json_output)
    return _logger_manager


def get_logger(name: str = "main") -> logging.Logger:
    """获取日志器"""
    global _logger_manager
    if _logger_manager is None:
        # 如果未初始化，使用基本配置
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)
    return _logger_manager.get_logger(name)


def cleanup_logging():
    """清理日志系统"""
    global _logger_manager
    if _logger_manager:
        _logger_manager.close()
        _logger_manager = None


# 便捷函数
def log_login_operation(operation: str, path: str, success: bool, details: str = ""):
    """记录登录操作的便捷函数"""
    global _logger_manager
    if _logger_manager:
        _logger_manager.log_login_data_operation(operation, path, success, details)


def log_webview_event(event: str, url: str = "", success: bool = True, details: str = ""):
    """记录WebView事件的便捷函数"""
    global _logger_manager
    if _logger_manager:
        _logger_manager.log_webview_event(event, url, success, details)


def log_startup_performance():
    """记录启动性能的便捷函数"""
    global _logger_manager
    if _logger_manager:
        _logger_manager.log_startup_performance()
