#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置管理
提供日志系统的配置选项和设置
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class LoggingConfig:
    """日志配置管理类"""
    
    DEFAULT_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": "logger.formatters.ColoredFormatter"
            },
            "detailed": {
                "()": "logger.formatters.DetailedFormatter"
            },
            "simple": {
                "()": "logger.formatters.SimpleFormatter"
            },
            "json": {
                "()": "logger.formatters.JSONFormatter"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "colored",
                "stream": "ext://sys.stdout"
            },
            "app_file": {
                "()": "logger.handlers.SmartRotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 20971520,  # 20MB
                "backupCount": 10,
                "encoding": "utf-8"
            },
            "error_file": {
                "()": "logger.handlers.SmartRotatingFileHandler",
                "level": "ERROR",
                "formatter": "simple",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "login_file": {
                "()": "logger.handlers.SmartRotatingFileHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "filename": "logs/login.log",
                "maxBytes": 5242880,  # 5MB
                "backupCount": 3,
                "encoding": "utf-8"
            },
            "webview_file": {
                "()": "logger.handlers.SmartRotatingFileHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "filename": "logs/webview.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "performance_file": {
                "()": "logger.handlers.SmartRotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/performance.log",
                "maxBytes": 5242880,  # 5MB
                "backupCount": 3,
                "encoding": "utf-8"
            }
        },
        "filters": {
            "context": {
                "()": "logger.handlers.ContextFilter",
                "app_name": "NetEaseMusic"
            },
            "login": {
                "()": "logger.handlers.LoginDataFilter"
            },
            "webview": {
                "()": "logger.handlers.WebViewFilter"
            },
            "error": {
                "()": "logger.handlers.ErrorFilter"
            },
            "performance": {
                "()": "logger.handlers.PerformanceFilter"
            }
        },
        "loggers": {
            "NetEaseMusic": {
                "level": "DEBUG",
                "handlers": ["console", "app_file"],
                "propagate": False
            },
            "NetEaseMusic.login": {
                "level": "DEBUG",
                "handlers": ["login_file"],
                "propagate": False
            },
            "NetEaseMusic.webview": {
                "level": "DEBUG",
                "handlers": ["webview_file"],
                "propagate": False
            },
            "NetEaseMusic.error": {
                "level": "ERROR",
                "handlers": ["error_file"],
                "propagate": False
            },
            "NetEaseMusic.performance": {
                "level": "INFO",
                "handlers": ["performance_file"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "app_file"]
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/logging.json"
        self.config_path = Path(self.config_file)
        self._config = self.DEFAULT_CONFIG.copy()
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置
                    self._merge_config(self._config, user_config)
                    print(f"已加载日志配置: {self.config_path}")
            except Exception as e:
                print(f"加载日志配置失败: {e}，使用默认配置")
        else:
            # 创建默认配置文件
            self.save_config()
            
        return self._config
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            print(f"已创建默认日志配置: {self.config_path}")
        except Exception as e:
            print(f"保存日志配置失败: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self._config.copy()
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        self._merge_config(self._config, updates)
    
    def _merge_config(self, base: Dict[str, Any], updates: Dict[str, Any]):
        """递归合并配置"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        return self._config.get("root", {}).get("level", "INFO")
    
    def set_log_level(self, level: str):
        """设置日志级别"""
        if "root" not in self._config:
            self._config["root"] = {}
        self._config["root"]["level"] = level.upper()
    
    def is_console_output_enabled(self) -> bool:
        """检查是否启用控制台输出"""
        console_handler = self._config.get("handlers", {}).get("console", {})
        return console_handler.get("level") != "DISABLED"
    
    def set_console_output(self, enabled: bool):
        """设置控制台输出"""
        if "handlers" not in self._config:
            self._config["handlers"] = {}
        
        if enabled:
            self._config["handlers"]["console"]["level"] = "DEBUG"
        else:
            self._config["handlers"]["console"]["level"] = "DISABLED"
    
    def get_file_rotation_config(self, handler_name: str) -> Dict[str, Any]:
        """获取文件轮转配置"""
        handler = self._config.get("handlers", {}).get(handler_name, {})
        return {
            "maxBytes": handler.get("maxBytes", 10*1024*1024),
            "backupCount": handler.get("backupCount", 5)
        }
    
    def set_file_rotation_config(self, handler_name: str, max_bytes: int, backup_count: int):
        """设置文件轮转配置"""
        if "handlers" not in self._config:
            self._config["handlers"] = {}
        
        if handler_name not in self._config["handlers"]:
            self._config["handlers"][handler_name] = {}
        
        self._config["handlers"][handler_name]["maxBytes"] = max_bytes
        self._config["handlers"][handler_name]["backupCount"] = backup_count


# 环境变量配置
class EnvConfig:
    """环境变量配置"""
    
    @staticmethod
    def get_log_level() -> str:
        """从环境变量获取日志级别"""
        return os.getenv("NETEASE_LOG_LEVEL", "INFO")
    
    @staticmethod
    def get_log_dir() -> str:
        """从环境变量获取日志目录"""
        return os.getenv("NETEASE_LOG_DIR", "logs")
    
    @staticmethod
    def get_console_output() -> bool:
        """从环境变量获取控制台输出设置"""
        return os.getenv("NETEASE_LOG_CONSOLE", "true").lower() == "true"
    
    @staticmethod
    def get_file_output() -> bool:
        """从环境变量获取文件输出设置"""
        return os.getenv("NETEASE_LOG_FILE", "true").lower() == "true"
    
    @staticmethod
    def get_json_output() -> bool:
        """从环境变量获取JSON输出设置"""
        return os.getenv("NETEASE_LOG_JSON", "false").lower() == "true"
    
    @staticmethod
    def get_debug_mode() -> bool:
        """从环境变量获取调试模式"""
        return os.getenv("NETEASE_DEBUG", "false").lower() == "true"


def get_logging_config() -> Dict[str, Any]:
    """获取最终的日志配置（合并文件配置和环境变量）"""
    # 加载文件配置
    config_manager = LoggingConfig()
    file_config = config_manager.load_config()
    
    # 应用环境变量覆盖
    env_config = {
        "root": {
            "level": EnvConfig.get_log_level()
        },
        "handlers": {
            "console": {
                "level": "DEBUG" if EnvConfig.get_console_output() else "DISABLED"
            }
        }
    }
    
    # 如果禁用文件输出，移除所有文件处理器
    if not EnvConfig.get_file_output():
        for handler_name in ["app_file", "error_file", "login_file", "webview_file", "performance_file"]:
            if "handlers" in file_config and handler_name in file_config["handlers"]:
                del file_config["handlers"][handler_name]
        
        if "root" in file_config and "handlers" in file_config["root"]:
            file_config["root"]["handlers"] = [
                h for h in file_config["root"]["handlers"] 
                if h not in ["app_file", "error_file", "login_file", "webview_file", "performance_file"]
            ]
    
    # 合并配置
    config_manager._merge_config(file_config, env_config)
    
    return file_config
