#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志格式化器
提供不同场景的日志格式
"""

import logging
import time
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        if fmt is None:
            fmt = '%(asctime)s | %(levelname)-8s | %(name)-15s | %(funcName)-15s:%(lineno)-4d | %(message)s'
        if datefmt is None:
            datefmt = '%Y-%m-%d %H:%M:%S'
        super().__init__(fmt, datefmt)
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        # 格式化时间
        if self.datefmt:
            time_struct = self.formatTime(record)
            if isinstance(time_struct, time.struct_time):
                timestamp = time.strftime(self.datefmt, time_struct)
                record.asctime = timestamp
        
        return super().format(record)


class DetailedFormatter(logging.Formatter):
    """详细的文件日志格式化器"""
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        if fmt is None:
            fmt = ('%(asctime)s | %(levelname)-8s | %(name)-20s | '
                   '%(funcName)-20s:%(lineno)-4d | %(process)d | %(thread)d | '
                   '%(message)s')
        if datefmt is None:
            datefmt = '%Y-%m-%d %H:%M:%S.%f'
        super().__init__(fmt, datefmt)


class SimpleFormatter(logging.Formatter):
    """简单的日志格式化器"""
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        if fmt is None:
            fmt = '%(asctime)s | %(levelname)-8s | %(message)s'
        if datefmt is None:
            datefmt = '%H:%M:%S'
        super().__init__(fmt, datefmt)


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record):
        import json
        
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread,
            'message': record.getMessage(),
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 添加额外字段
        extra_data = getattr(record, 'extra_data', None)
        if extra_data is not None:
            log_entry['extra'] = extra_data
            
        return json.dumps(log_entry, ensure_ascii=False)
