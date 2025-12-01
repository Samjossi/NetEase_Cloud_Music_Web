#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebEngine Profile管理器
解决登录数据持久化问题
"""

import os
import sys
import time
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWidgets import QApplication

from logger import get_logger


class ProfileManager:
    """WebEngine Profile管理器，确保登录数据正确持久化"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.logger = get_logger("profile_manager")
        
        # 优先使用环境变量，否则使用用户目录
        if storage_path is None:
            storage_path = os.environ.get('NETEASE_LOGIN_DATA_PATH')
            if storage_path is None:
                storage_path = os.path.expanduser("~/.local/share/netease-music/login_data")
        
        self.storage_path = os.path.abspath(storage_path)
        self.profile: Optional[QWebEngineProfile] = None
        self._ensure_storage_directory()
        
    def _ensure_storage_directory(self):
        """确保存储目录存在且可写"""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            
            # 测试目录权限
            test_file = os.path.join(self.storage_path, ".permission_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            self.logger.info(f"存储目录准备就绪: {self.storage_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"存储目录创建失败: {e}")
            raise
    
    def create_persistent_profile(self, profile_name: str = "NetEaseMusic") -> QWebEngineProfile:
        """创建持久化Profile"""
        try:
            self.logger.info("开始创建持久化Profile...")
            
            # 确保QApplication存在
            if not QApplication.instance():
                raise RuntimeError("QApplication实例不存在")
            
            # 创建新的Profile实例（不使用默认Profile）
            self.profile = QWebEngineProfile(profile_name)
            
            # 强制设置持久化存储路径
            self.profile.setPersistentStoragePath(self.storage_path)
            self.logger.info(f"设置持久化存储路径: {self.storage_path}")
            
            # 使用强制持久化Cookie策略（关键修复）
            self.profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            self.logger.info("设置Cookie策略为强制持久化")
            
            # 设置HTTP缓存为磁盘缓存（避免内存缓存导致数据丢失）
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            self.logger.info("设置HTTP缓存为磁盘缓存")
            
            # 设置其他相关配置
            self._configure_profile_settings()
            
            # 验证配置
            self._verify_profile_configuration()
            
            self.logger.info("持久化Profile创建成功")
            return self.profile
            
        except Exception as e:
            self.logger.error(f"创建持久化Profile失败: {e}", exc_info=True)
            raise
    
    def _configure_profile_settings(self):
        """配置Profile的其他设置"""
        try:
            if self.profile is None:
                self.logger.warning("Profile为空，跳过配置")
                return
            
            # 设置用户代理
            user_agent = self.profile.httpUserAgent()
            if user_agent and "NetEaseMusicDesktop" not in user_agent:
                new_user_agent = f"{user_agent} NetEaseMusicDesktop/1.0"
                self.profile.setHttpUserAgent(new_user_agent)
                self.logger.debug(f"设置用户代理: {new_user_agent}")
            
            # 启用 localStorage
            settings = self.profile.settings()
            if settings:
                settings.setAttribute(settings.WebAttribute.LocalStorageEnabled, True)
                self.logger.debug("启用本地存储")
            
        except Exception as e:
            self.logger.warning(f"配置Profile设置失败: {e}")
    
    def _verify_profile_configuration(self):
        """验证Profile配置是否正确"""
        try:
            if self.profile is None:
                self.logger.warning("Profile为空，无法验证配置")
                return
            
            storage_path = self.profile.persistentStoragePath()
            cookie_policy = self.profile.persistentCookiesPolicy()
            cache_type = self.profile.httpCacheType()
            
            self.logger.info("=== Profile配置验证 ===")
            self.logger.info(f"存储路径: {storage_path}")
            self.logger.info(f"Cookie策略: {cookie_policy}")
            self.logger.info(f"缓存类型: {cache_type}")
            
            # 验证关键设置
            if storage_path != self.storage_path:
                self.logger.warning(f"存储路径设置失败: 期望 {self.storage_path}, 实际 {storage_path}")
            
            if cookie_policy != QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies:
                self.logger.warning(f"Cookie策略设置失败: 期望 ForcePersistentCookies, 实际 {cookie_policy}")
            
            if cache_type != QWebEngineProfile.HttpCacheType.DiskHttpCache:
                self.logger.warning(f"缓存类型设置失败: 期望 DiskHttpCache, 实际 {cache_type}")
                
        except Exception as e:
            self.logger.error(f"验证Profile配置失败: {e}")
    
    def get_login_data_info(self) -> Dict[str, Any]:
        """获取登录数据信息"""
        try:
            if not os.path.exists(self.storage_path):
                return {"status": "no_data", "files": []}
            
            files = []
            total_size = 0
            
            for item in os.listdir(self.storage_path):
                item_path = os.path.join(self.storage_path, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    mtime = os.path.getmtime(item_path)
                    files.append({
                        "name": item,
                        "path": item_path,
                        "size": size,
                        "modified": mtime
                    })
                    total_size += size
            
            return {
                "status": "has_data" if files else "empty",
                "storage_path": self.storage_path,
                "files": files,
                "total_size": total_size,
                "file_count": len(files)
            }
            
        except Exception as e:
            self.logger.error(f"获取登录数据信息失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def validate_login_data(self) -> bool:
        """验证登录数据是否有效"""
        try:
            data_info = self.get_login_data_info()
            
            if data_info["status"] == "no_data":
                self.logger.warning("登录数据目录不存在")
                return False
            
            if data_info["status"] == "empty":
                self.logger.warning("登录数据目录为空")
                return False
            
            # 检查关键文件
            critical_files = ["Cookies", "Web Data", "Local Storage"]
            existing_files = [f["name"] for f in data_info["files"]]
            
            missing_files = [f for f in critical_files if f not in existing_files]
            if missing_files:
                self.logger.warning(f"缺少关键登录文件: {missing_files}")
            
            # 检查文件大小（避免空文件）
            tiny_files = [f["name"] for f in data_info["files"] if f["size"] < 100]
            if tiny_files:
                self.logger.warning(f"检测到过小的文件（可能损坏）: {tiny_files}")
            
            # 至少有一个数据文件且有内容
            valid_files = [f for f in data_info["files"] if f["size"] > 0]
            is_valid = len(valid_files) > 0
            
            self.logger.info(f"登录数据验证结果: {'有效' if is_valid else '无效'}")
            self.logger.info(f"有效文件数量: {len(valid_files)}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"验证登录数据失败: {e}")
            return False
    
    def cleanup_invalid_data(self):
        """清理无效的登录数据"""
        try:
            self.logger.info("开始清理无效登录数据...")
            
            data_info = self.get_login_data_info()
            if data_info["status"] in ["no_data", "empty"]:
                self.logger.info("没有数据需要清理")
                return
            
            cleaned_count = 0
            for file_info in data_info["files"]:
                if file_info["size"] == 0:
                    try:
                        os.remove(file_info["path"])
                        self.logger.info(f"删除空文件: {file_info['name']}")
                        cleaned_count += 1
                    except Exception as e:
                        self.logger.warning(f"删除文件失败 {file_info['name']}: {e}")
            
            self.logger.info(f"清理完成，删除了 {cleaned_count} 个无效文件")
            
        except Exception as e:
            self.logger.error(f"清理登录数据失败: {e}")
    
    def backup_login_data(self, backup_suffix: str = None) -> bool:
        """备份登录数据"""
        try:
            if not backup_suffix:
                backup_suffix = time.strftime("%Y%m%d_%H%M%S")
            
            backup_path = f"{self.storage_path}_backup_{backup_suffix}"
            
            if not os.path.exists(self.storage_path):
                self.logger.warning("没有数据需要备份")
                return False
            
            # 如果备份已存在，先删除
            if os.path.exists(backup_path):
                import shutil
                shutil.rmtree(backup_path)
                self.logger.debug(f"删除已存在的备份目录: {backup_path}")
            
            import shutil
            shutil.copytree(self.storage_path, backup_path)
            
            self.logger.info(f"登录数据备份成功: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"备份登录数据失败: {e}")
            return False
    
    def restore_login_data(self, backup_path: str) -> bool:
        """恢复登录数据"""
        try:
            if not backup_path or not os.path.exists(backup_path):
                self.logger.error(f"备份路径不存在: {backup_path}")
                return False
            
            # 备份当前数据
            self.backup_login_data("before_restore")
            
            # 删除当前数据
            if os.path.exists(self.storage_path):
                import shutil
                shutil.rmtree(self.storage_path)
            
            # 恢复数据
            import shutil
            shutil.copytree(backup_path, self.storage_path)
            
            self.logger.info(f"登录数据恢复成功: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复登录数据失败: {e}")
            return False
    
    def get_window_settings_path(self) -> str:
        """获取窗口设置文件路径"""
        return os.path.join(self.storage_path, "window_settings.json")
    
    def save_window_geometry(self, geometry_bytes: bytes, maximized: bool = False) -> bool:
        """保存窗口几何信息"""
        try:
            settings_path = self.get_window_settings_path()
            
            # 将几何数据编码为base64字符串
            geometry_b64 = base64.b64encode(geometry_bytes).decode('utf-8')
            
            window_settings = {
                "geometry": geometry_b64,
                "maximized": maximized,
                "last_saved": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0"
            }
            
            # 原子写入，避免文件损坏
            temp_path = settings_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(window_settings, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_path, settings_path)
            
            self.logger.debug(f"窗口几何信息已保存: {settings_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存窗口几何信息失败: {e}")
            return False
    
    def load_window_geometry(self) -> Dict[str, Any]:
        """加载窗口几何信息"""
        try:
            settings_path = self.get_window_settings_path()
            
            if not os.path.exists(settings_path):
                self.logger.debug("窗口设置文件不存在，返回默认设置")
                return {
                    "geometry": None,
                    "maximized": False,
                    "valid": False
                }
            
            with open(settings_path, 'r', encoding='utf-8') as f:
                window_settings = json.load(f)
            
            # 验证数据完整性
            if not all(key in window_settings for key in ["geometry", "maximized"]):
                self.logger.warning("窗口设置文件格式不完整")
                return {
                    "geometry": None,
                    "maximized": False,
                    "valid": False
                }
            
            # 解码几何数据
            geometry_bytes = base64.b64decode(window_settings["geometry"].encode('utf-8'))
            
            result = {
                "geometry": geometry_bytes,
                "maximized": window_settings.get("maximized", False),
                "valid": True,
                "last_saved": window_settings.get("last_saved", "unknown")
            }
            
            self.logger.debug(f"窗口几何信息加载成功，保存时间: {result['last_saved']}")
            return result
            
        except Exception as e:
            self.logger.error(f"加载窗口几何信息失败: {e}")
            return {
                "geometry": None,
                "maximized": False,
                "valid": False
            }
    
    def reset_window_settings(self) -> bool:
        """重置窗口设置"""
        try:
            settings_path = self.get_window_settings_path()
            
            if os.path.exists(settings_path):
                os.remove(settings_path)
                self.logger.info("窗口设置已重置")
            else:
                self.logger.debug("窗口设置文件不存在，无需重置")
            
            return True
            
        except Exception as e:
            self.logger.error(f"重置窗口设置失败: {e}")
            return False

    def get_user_preferences_path(self) -> str:
        """获取用户偏好设置文件路径"""
        return os.path.join(self.storage_path, "user_preferences.json")
    
    def save_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """保存用户偏好设置"""
        try:
            preferences_path = self.get_user_preferences_path()
            
            # 添加版本信息和时间戳
            preferences["version"] = "1.0"
            preferences["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 原子写入，避免文件损坏
            temp_path = preferences_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_path, preferences_path)
            
            self.logger.debug(f"用户偏好设置已保存: {preferences_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存用户偏好设置失败: {e}")
            return False
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """加载用户偏好设置"""
        try:
            preferences_path = self.get_user_preferences_path()
            
            if not os.path.exists(preferences_path):
                self.logger.debug("用户偏好设置文件不存在，返回默认设置")
                return self._get_default_user_preferences()
            
            with open(preferences_path, 'r', encoding='utf-8') as f:
                preferences = json.load(f)
            
            # 验证数据完整性
            if "close_behavior" not in preferences:
                self.logger.warning("用户偏好设置文件格式不完整，使用默认设置")
                return self._get_default_user_preferences()
            
            self.logger.debug(f"用户偏好设置加载成功，最后更新: {preferences.get('last_updated', 'unknown')}")
            return preferences
            
        except Exception as e:
            self.logger.error(f"加载用户偏好设置失败: {e}")
            return self._get_default_user_preferences()
    
    def _get_default_user_preferences(self) -> Dict[str, Any]:
        """获取默认用户偏好设置"""
        return {
            "close_behavior": {
                "action": "ask",  # ask, minimize_to_tray, exit_program
                "remember_choice": False,
                "first_time": True
            },
            "version": "1.0"
        }
    
    def update_close_behavior(self, action: str, remember_choice: bool = False) -> bool:
        """更新关闭行为偏好"""
        try:
            preferences = self.load_user_preferences()
            
            # 更新关闭行为设置
            preferences["close_behavior"]["action"] = action
            preferences["close_behavior"]["remember_choice"] = remember_choice
            preferences["close_behavior"]["first_time"] = False
            
            return self.save_user_preferences(preferences)
            
        except Exception as e:
            self.logger.error(f"更新关闭行为偏好失败: {e}")
            return False
    
    def get_close_behavior(self) -> Dict[str, Any]:
        """获取关闭行为偏好"""
        try:
            preferences = self.load_user_preferences()
            return preferences.get("close_behavior", self._get_default_user_preferences()["close_behavior"])
            
        except Exception as e:
            self.logger.error(f"获取关闭行为偏好失败: {e}")
            return self._get_default_user_preferences()["close_behavior"]
    
    def get_pipewire_config_path(self) -> str:
        """获取PipeWire配置文件路径"""
        return os.path.join(self.storage_path, "pipewire_config.json")
    
    def save_pipewire_config(self, config: Dict[str, Any]) -> bool:
        """保存PipeWire配置"""
        try:
            config_path = self.get_pipewire_config_path()
            
            # 添加版本信息和时间戳
            config["version"] = "1.0"
            config["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 验证配置
            validated_config = self._validate_pipewire_config(config)
            
            # 原子写入，避免文件损坏
            temp_path = config_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(validated_config, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_path, config_path)
            
            self.logger.debug(f"PipeWire配置已保存: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存PipeWire配置失败: {e}")
            return False
    
    def load_pipewire_config(self) -> Dict[str, Any]:
        """加载PipeWire配置"""
        try:
            config_path = self.get_pipewire_config_path()
            
            if not os.path.exists(config_path):
                self.logger.debug("PipeWire配置文件不存在，返回默认配置")
                return self._get_default_pipewire_config()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证配置完整性
            validated_config = self._validate_pipewire_config(config)
            
            self.logger.debug(f"PipeWire配置加载成功，最后更新: {config.get('last_updated', 'unknown')}")
            return validated_config
            
        except Exception as e:
            self.logger.error(f"加载PipeWire配置失败: {e}")
            return self._get_default_pipewire_config()
    
    def _validate_pipewire_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证PipeWire配置"""
        try:
            default_config = self._get_default_pipewire_config()
            validated_config = default_config.copy()
            
            # 验证并更新配置项
            if "auto_restart_enabled" in config:
                validated_config["auto_restart_enabled"] = bool(config["auto_restart_enabled"])
            
            if "restart_interval_minutes" in config:
                interval = int(config["restart_interval_minutes"])
                # 限制重启间隔在30分钟到180分钟之间
                validated_config["restart_interval_minutes"] = max(30, min(180, interval))
            
            if "show_notifications" in config:
                validated_config["show_notifications"] = bool(config["show_notifications"])
            
            if "last_restart_timestamp" in config:
                timestamp = float(config["last_restart_timestamp"])
                validated_config["last_restart_timestamp"] = timestamp
            
            if "restart_command" in config and isinstance(config["restart_command"], str):
                validated_config["restart_command"] = config["restart_command"]
            
            return validated_config
            
        except Exception as e:
            self.logger.error(f"验证PipeWire配置失败: {e}")
            return self._get_default_pipewire_config()
    
    def _get_default_pipewire_config(self) -> Dict[str, Any]:
        """获取默认PipeWire配置 - 用户可配置版本"""
        return {
            "auto_restart_enabled": False,  # 默认关闭，用户自行选择
            "restart_interval_minutes": 90,  # 默认90分钟重启一次
            "show_notifications": True,  # 默认显示通知
            "last_restart_timestamp": 0.0,
            "restart_command": "systemctl --user restart pipewire",
            "version": "1.0"
        }
    
    def update_pipewire_restart_time(self, restart_timestamp: float) -> bool:
        """更新PipeWire重启时间 - 简化版本：不计算下次重启时间"""
        try:
            config = self.load_pipewire_config()
            
            # 更新重启时间
            config["last_restart_timestamp"] = restart_timestamp
            
            # 简化版本：不自动计算下次重启时间，因为使用歌曲计数机制
            # 只重置跳过标志
            config["skip_next_restart"] = False
            
            # 保存配置
            success = self.save_pipewire_config(config)
            
            if success:
                self.logger.info(f"PipeWire重启时间已更新: 上次={restart_timestamp}")
            else:
                self.logger.error("更新PipeWire重启时间失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新PipeWire重启时间失败: {e}")
            return False
    
    def get_pipewire_next_restart_time(self) -> float:
        """获取下次PipeWire重启时间"""
        try:
            config = self.load_pipewire_config()
            return config.get("next_restart_timestamp", 0.0)
        except Exception as e:
            self.logger.error(f"获取下次PipeWire重启时间失败: {e}")
            return 0.0
    
    def is_pipewire_restart_due(self) -> bool:
        """检查是否到了PipeWire重启时间"""
        try:
            current_time = time.time()
            next_restart_time = self.get_pipewire_next_restart_time()
            
            # 检查是否到了重启时间
            is_due = current_time >= next_restart_time and next_restart_time > 0
            
            if is_due:
                self.logger.info(f"PipeWire重启时间已到: 当前={current_time}, 计划={next_restart_time}")
            
            return is_due
            
        except Exception as e:
            self.logger.error(f"检查PipeWire重启时间失败: {e}")
            return False
    
    def should_skip_pipewire_restart(self) -> bool:
        """检查是否应该跳过下次PipeWire重启"""
        try:
            config = self.load_pipewire_config()
            return config.get("skip_next_restart", False)
        except Exception as e:
            self.logger.error(f"检查PipeWire跳过重启标志失败: {e}")
            return False
    
    def set_skip_pipewire_restart(self, skip: bool) -> bool:
        """设置是否跳过下次PipeWire重启"""
        try:
            config = self.load_pipewire_config()
            config["skip_next_restart"] = skip
            
            success = self.save_pipewire_config(config)
            
            if success:
                self.logger.info(f"PipeWire跳过重启标志已设置: {skip}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"设置PipeWire跳过重启标志失败: {e}")
            return False
    
    def is_pipewire_auto_restart_enabled(self) -> bool:
        """检查PipeWire自动重启是否启用"""
        try:
            config = self.load_pipewire_config()
            return config.get("auto_restart_enabled", True)
        except Exception as e:
            self.logger.error(f"检查PipeWire自动重启状态失败: {e}")
            return False
    
    def enable_pipewire_auto_restart(self, enabled: bool) -> bool:
        """启用或禁用PipeWire自动重启"""
        try:
            config = self.load_pipewire_config()
            config["auto_restart_enabled"] = enabled
            
            # 如果启用，重新计算下次重启时间
            if enabled:
                current_time = time.time()
                interval_hours = config["restart_interval_hours"]
                next_restart_time = current_time + (interval_hours * 3600)
                config["next_restart_timestamp"] = next_restart_time
                self.logger.info(f"PipeWire自动重启已启用，下次重启时间: {next_restart_time}")
            else:
                config["next_restart_timestamp"] = 0.0
                self.logger.info("PipeWire自动重启已禁用")
            
            success = self.save_pipewire_config(config)
            return success
            
        except Exception as e:
            self.logger.error(f"设置PipeWire自动重启状态失败: {e}")
            return False
    
    def get_pipewire_restart_interval(self) -> float:
        """获取PipeWire重启间隔（小时）"""
        try:
            config = self.load_pipewire_config()
            return config.get("restart_interval_hours", 1.0)
        except Exception as e:
            self.logger.error(f"获取PipeWire重启间隔失败: {e}")
            return 1.0
    
    def set_pipewire_restart_interval(self, interval_hours: float) -> bool:
        """设置PipeWire重启间隔（小时）"""
        try:
            # 限制间隔范围
            interval_hours = max(0.5, min(24.0, interval_hours))
            
            config = self.load_pipewire_config()
            config["restart_interval_hours"] = interval_hours
            
            # 重新计算下次重启时间
            if config.get("auto_restart_enabled", False):
                current_time = time.time()
                next_restart_time = current_time + (interval_hours * 3600)
                config["next_restart_timestamp"] = next_restart_time
                self.logger.info(f"PipeWire重启间隔已更新: {interval_hours}小时, 下次重启: {next_restart_time}")
            
            success = self.save_pipewire_config(config)
            return success
            
        except Exception as e:
            self.logger.error(f"设置PipeWire重启间隔失败: {e}")
            return False
    
    def get_pipewire_full_config(self) -> Dict[str, Any]:
        """获取完整的PipeWire配置信息"""
        try:
            config = self.load_pipewire_config()
            
            # 添加格式化的时间信息
            current_time = time.time()
            
            # 格式化上次重启时间
            last_restart = config.get("last_restart_timestamp", 0.0)
            if last_restart > 0:
                config["last_restart_formatted"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_restart))
                config["last_restart_relative"] = self._format_relative_time(current_time - last_restart)
            else:
                config["last_restart_formatted"] = "从未重启"
                config["last_restart_relative"] = "从未"
            
            # 格式化下次重启时间
            next_restart = config.get("next_restart_timestamp", 0.0)
            if next_restart > 0:
                config["next_restart_formatted"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(next_restart))
                if current_time < next_restart:
                    config["next_restart_countdown"] = self._format_relative_time(next_restart - current_time)
                    config["restart_overdue"] = False
                else:
                    config["next_restart_countdown"] = "已过期"
                    config["restart_overdue"] = True
            else:
                config["next_restart_formatted"] = "未设置"
                config["next_restart_countdown"] = "未设置"
                config["restart_overdue"] = False
            
            return config
            
        except Exception as e:
            self.logger.error(f"获取PipeWire完整配置失败: {e}")
            return self._get_default_pipewire_config()
    
    def _format_relative_time(self, seconds: float) -> str:
        """格式化相对时间"""
        try:
            if seconds is None:
                return "未知"
            elif seconds < 0:
                return "刚刚"
            elif seconds < 60:
                return f"{int(seconds)}秒"
            elif seconds < 3600:
                minutes = int(seconds // 60)
                return f"{minutes}分钟"
            elif seconds < 86400:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                if minutes > 0:
                    return f"{hours}小时{minutes}分钟"
                else:
                    return f"{hours}小时"
            else:
                days = int(seconds // 86400)
                hours = int((seconds % 86400) // 3600)
                if hours > 0:
                    return f"{days}天{hours}小时"
                else:
                    return f"{days}天"
        except Exception:
            return "时间格式化失败"

    def get_profile(self) -> Optional[QWebEngineProfile]:
        """获取Profile实例"""
        return self.profile
    
    def close(self):
        """关闭Profile管理器"""
        try:
            if self.profile:
                self.profile.deleteLater()
                self.profile = None
            self.logger.info("Profile管理器已关闭")
        except Exception as e:
            self.logger.error(f"关闭Profile管理器失败: {e}")


# 全局Profile管理器实例
_profile_manager = None


def get_profile_manager(storage_path: Optional[str] = None) -> ProfileManager:
    """获取全局Profile管理器实例"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager(storage_path)
    return _profile_manager


def cleanup_profile_manager():
    """清理全局Profile管理器"""
    global _profile_manager
    if _profile_manager:
        _profile_manager.close()
        _profile_manager = None
