#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义日志处理器
提供轮转、异步、过滤等高级功能
"""

import os
import logging
import logging.handlers
import threading
import queue
import time
from typing import Optional, Dict, Any
from pathlib import Path


class AsyncFileHandler(logging.Handler):
    """异步文件日志处理器"""
    
    def __init__(self, filename: str, mode: str = 'a', encoding: str = 'utf-8'):
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._write_worker, daemon=True)
        self.thread.start()
    
    def _write_worker(self):
        """后台写入线程"""
        while True:
            try:
                record = self.queue.get(timeout=1)
                if record is None:  # 停止信号
                    break
                
                # 写入文件
                with open(self.filename, self.mode, encoding=self.encoding) as f:
                    f.write(self.format(record) + '\n')
                    f.flush()
                
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # 避免日志记录错误导致无限循环
                print(f"AsyncFileHandler error: {e}")
    
    def emit(self, record):
        """发送记录到队列"""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # 队列满时丢弃旧记录
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(record)
            except queue.Empty:
                pass
    
    def close(self):
        """关闭处理器"""
        self.queue.put(None)  # 发送停止信号
        self.thread.join(timeout=5)
        super().close()


class SmartRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """智能轮转文件处理器"""
    
    def __init__(self, 
                 filename: str, 
                 mode: str = 'a', 
                 maxBytes: int = 10*1024*1024,  # 10MB
                 backupCount: int = 5,
                 encoding: str = 'utf-8'):
        
        # 确保目录存在
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(filename, mode, maxBytes, backupCount, encoding)
    
    def shouldRollover(self, record):
        """智能判断是否需要轮转"""
        # 检查文件大小
        if super().shouldRollover(record):
            return True
        
        # 检查是否是新的一天
        try:
            current_date = time.strftime('%Y-%m-%d')
            file_mtime = time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(self.baseFilename)))
            if current_date != file_mtime:
                return True
        except (OSError, IOError):
            pass
        
        return False


class ContextFilter(logging.Filter):
    """上下文过滤器，添加应用信息"""
    
    def __init__(self, app_name: str = "NetEaseMusic"):
        super().__init__()
        self.app_name = app_name
    
    def filter(self, record):
        # 添加应用信息
        record.app_name = self.app_name
        
        # 添加会话ID（如果有的话）
        if not hasattr(record, 'session_id'):
            record.session_id = threading.current_thread().name
        
        return True


class LoginDataFilter(logging.Filter):
    """登录数据专用过滤器"""
    
    def filter(self, record):
        # 只记录与登录数据相关的日志
        login_keywords = ['login', 'cookie', 'session', 'auth', 'persistent', 'storage']
        message_lower = record.getMessage().lower()
        
        # 如果消息包含登录相关关键词或日志器名称包含login，则记录
        return (any(keyword in message_lower for keyword in login_keywords) or 
                'login' in record.name.lower())


class WebViewFilter(logging.Filter):
    """WebView专用过滤器"""
    
    def filter(self, record):
        # 只记录WebView相关的日志
        webview_keywords = ['webview', 'webengine', 'profile', 'page', 'url', 'load']
        message_lower = record.getMessage().lower()
        
        return (any(keyword in message_lower for keyword in webview_keywords) or
                'webview' in record.name.lower() or
                'webengine' in record.name.lower())


class ErrorFilter(logging.Filter):
    """错误过滤器，只记录ERROR及以上级别的日志"""
    
    def filter(self, record):
        return record.levelno >= logging.ERROR


class PerformanceFilter(logging.Filter):
    """性能相关过滤器"""
    
    def filter(self, record):
        # 记录性能相关的日志
        perf_keywords = ['performance', 'memory', 'cpu', 'time', 'load', 'startup']
        message_lower = record.getMessage().lower()
        
        return any(keyword in message_lower for keyword in perf_keywords)


class MultiFileHandler:
    """多文件处理器管理器"""
    
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.handlers: Dict[str, logging.Handler] = {}
    
    def get_handler(self, 
                    name: str, 
                    handler_type: str = "rotating",
                    formatter: Optional[logging.Formatter] = None,
                    **kwargs) -> logging.Handler:
        """获取或创建处理器"""
        
        if name in self.handlers:
            return self.handlers[name]
        
        log_file = self.base_dir / f"{name}.log"
        
        if handler_type == "rotating":
            handler = SmartRotatingFileHandler(
                str(log_file),
                maxBytes=kwargs.get('maxBytes', 10*1024*1024),
                backupCount=kwargs.get('backupCount', 5)
            )
        elif handler_type == "async":
            handler = AsyncFileHandler(str(log_file))
        else:
            handler = logging.FileHandler(str(log_file))
        
        if formatter:
            handler.setFormatter(formatter)
        
        self.handlers[name] = handler
        return handler
    
    def close_all(self):
        """关闭所有处理器"""
        for handler in self.handlers.values():
            handler.close()
        self.handlers.clear()
