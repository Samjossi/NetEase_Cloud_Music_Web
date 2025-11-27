#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐网页播放器桌面版
使用PySide6创建原生窗口壳
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QUrl, QSize, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile

# 导入日志系统和Profile管理器
from logger import init_logging, get_logger, log_login_operation, log_webview_event, log_startup_performance
from profile_manager import get_profile_manager, cleanup_profile_manager


class NetEaseMusicWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = get_logger("window")
        self.logger.info("正在初始化主窗口...")
        
        # 初始化窗口状态管理
        self.window_save_timer = None  # 延迟保存定时器
        
        self.init_ui()
        self.setup_webview_monitoring()
        self.load_window_settings()
        
        self.logger.info("主窗口初始化完成")
        
    def init_ui(self):
        """初始化用户界面"""
        try:
            # 设置窗口标题
            self.setWindowTitle("网易云音乐")
            self.logger.debug("设置窗口标题: 网易云音乐")
            
            # 设置窗口大小 (适合播放器的尺寸)
            self.resize(1200, 800)
            self.setMinimumSize(800, 600)
            self.logger.debug("设置窗口大小: 1200x800，最小尺寸: 800x600")
            
            # 初始化Profile管理器（关键修复：在WebView创建前配置Profile）
            self.profile_manager = get_profile_manager()
            persistent_profile = self.profile_manager.create_persistent_profile()
            self.logger.info("持久化Profile创建完成")
            
            # 创建网页视图并应用自定义Profile
            self.web_view = QWebEngineView()
            # 使用正确的方式设置Profile：通过构造函数传入
            from PySide6.QtWebEngineCore import QWebEnginePage
            page = QWebEnginePage(persistent_profile, self.web_view)
            self.web_view.setPage(page)
            self.logger.debug("创建WebView并设置持久化Profile")
            
            # 验证登录数据状态
            self.validate_login_status()
            
            # 添加增强的登录数据监控
            self.setup_enhanced_login_monitor()
            
            # 加载网易云音乐播放器
            music_url = "https://music.163.com/st/webplayer"
            self.web_view.setUrl(QUrl(music_url))
            log_webview_event("load_url", music_url, True, "开始加载网易云音乐播放器")
            
            # 设置为中心控件
            self.setCentralWidget(self.web_view)
            self.logger.debug("设置WebView为中心控件")
            
            # 如果有图标文件，可以设置窗口图标
            try:
                icon_path = "NetEase_Music_icon.png"
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    self.logger.debug(f"设置窗口图标: {icon_path}")
                else:
                    self.logger.warning(f"图标文件不存在: {icon_path}")
            except Exception as e:
                self.logger.warning(f"设置窗口图标失败: {e}")
                
        except Exception as e:
            self.logger.error(f"初始化用户界面失败: {e}", exc_info=True)
            raise
    
    def validate_login_status(self):
        """验证登录数据状态"""
        try:
            self.logger.info("开始验证登录数据状态...")
            
            # 使用Profile管理器验证登录数据
            is_valid = self.profile_manager.validate_login_data()
            
            if is_valid:
                self.logger.info("✓ 登录数据验证通过，检测到有效的登录状态")
                log_login_operation("validate_login_status", "valid", True, "登录数据有效")
            else:
                self.logger.info("⚠ 未检测到有效的登录数据，可能需要重新登录")
                log_login_operation("validate_login_status", "invalid", False, "未检测到有效登录数据")
            
            # 获取详细的登录数据信息
            data_info = self.profile_manager.get_login_data_info()
            self.logger.info(f"登录数据详情: {data_info}")
            
        except Exception as e:
            self.logger.error(f"验证登录状态失败: {e}")
            log_login_operation("validate_login_status", "error", False, str(e))
    
    def setup_enhanced_login_monitor(self):
        """设置增强的登录数据监控"""
        try:
            # 创建定时器，定期检查登录数据状态
            self.enhanced_login_timer = QTimer()
            self.enhanced_login_timer.timeout.connect(self.enhanced_login_check)
            self.enhanced_login_timer.start(10000)  # 每10秒检查一次
            
            self.logger.debug("增强登录监控定时器已启动")
            log_login_operation("setup_monitor", "enhanced", True, "增强登录监控已启动")
            
        except Exception as e:
            self.logger.error(f"设置增强登录监控失败: {e}")
            log_login_operation("setup_monitor", "enhanced", False, str(e))
    
    def enhanced_login_check(self):
        """增强的登录状态检查"""
        try:
            # 检查登录数据变化
            data_info = self.profile_manager.get_login_data_info()
            
            if data_info["status"] == "has_data":
                # 检查文件变化
                if hasattr(self, '_last_file_count'):
                    if data_info["file_count"] != self._last_file_count:
                        self.logger.info(f"检测到登录文件数量变化: {self._last_file_count} -> {data_info['file_count']}")
                        log_login_operation("file_count_changed", str(data_info["file_count"]), True, 
                                         f"文件数量从 {self._last_file_count} 变为 {data_info['file_count']}")
                
                if hasattr(self, '_last_total_size'):
                    if data_info["total_size"] != self._last_total_size:
                        self.logger.info(f"检测到登录数据大小变化: {self._last_total_size} -> {data_info['total_size']}")
                        log_login_operation("data_size_changed", str(data_info["total_size"]), True,
                                         f"数据大小从 {self._last_total_size} 变为 {data_info['total_size']}")
                
                # 更新状态
                self._last_file_count = data_info["file_count"]
                self._last_total_size = data_info["total_size"]
                
                # 验证数据完整性
                if data_info["file_count"] > 0:
                    self.profile_manager.validate_login_data()
            
            # 检查Cookie状态（通过JavaScript）
            self.check_cookie_status()
            
        except Exception as e:
            self.logger.error(f"增强登录检查失败: {e}")
    
    def check_cookie_status(self):
        """通过JavaScript检查Cookie状态"""
        try:
            # 执行JavaScript检查登录状态
            js_code = """
            (function() {
                // 检查常见的登录Cookie
                var cookies = document.cookie;
                var hasLoginCookie = cookies.includes('MUSIC_U') || 
                                   cookies.includes('MUSIC_A') || 
                                   cookies.includes('__csrf');
                
                // 检查页面元素
                var hasLoginElement = document.querySelector('.user-info') !== null ||
                                    document.querySelector('.avatar') !== null ||
                                    document.querySelector('[data-name="用户"]') !== null;
                
                return {
                    hasLoginCookie: hasLoginCookie,
                    hasLoginElement: hasLoginElement,
                    cookieCount: cookies.split(';').length,
                    url: window.location.href
                };
            })();
            """
            
            self.web_view.page().runJavaScript(js_code, self.on_cookie_check_result)
            
        except Exception as e:
            self.logger.debug(f"Cookie状态检查失败（页面可能未加载）: {e}")
    
    def on_cookie_check_result(self, result):
        """处理Cookie检查结果"""
        try:
            if result and isinstance(result, dict):
                if result.get("hasLoginCookie") or result.get("hasLoginElement"):
                    self.logger.info("✓ 检测到登录状态（Cookie或页面元素）")
                    log_login_operation("cookie_check", "logged_in", True, 
                                     f"登录状态确认，URL: {result.get('url', 'unknown')}")
                else:
                    self.logger.debug("未检测到登录状态")
                    log_login_operation("cookie_check", "not_logged_in", False, "未检测到登录Cookie")
                
                # 记录详细信息
                if result.get("cookieCount", 0) > 0:
                    self.logger.debug(f"检测到 {result['cookieCount']} 个Cookie")
                    
        except Exception as e:
            self.logger.error(f"处理Cookie检查结果失败: {e}")
    
    
    def setup_webview_monitoring(self):
        """设置WebView监控"""
        try:
            # 监控页面加载状态
            self.web_view.loadStarted.connect(self.on_load_started)
            self.web_view.loadFinished.connect(self.on_load_finished)
            
            # 监控标题变化
            self.web_view.titleChanged.connect(self.on_title_changed)
            
            self.logger.debug("WebView监控设置完成")
        except Exception as e:
            self.logger.error(f"设置WebView监控失败: {e}")
    
    def on_load_started(self):
        """页面开始加载"""
        url = self.web_view.url().toString()
        self.logger.info(f"页面开始加载: {url}")
        log_webview_event("load_started", url, True, "页面加载开始")
        
        # 检查URL是否包含登录相关内容
        if 'login' in url.lower():
            self.logger.info(f"检测到登录页面: {url}")
            log_webview_event("login_page_detected", url, True, "用户访问登录页面")
    
    def on_load_finished(self, success):
        """页面加载完成"""
        url = self.web_view.url().toString()
        if success:
            self.logger.info(f"页面加载成功: {url}")
            log_webview_event("load_finished", url, True, "页面加载成功")
            
            # 检查是否从登录页面跳转回主页
            if 'login' not in url.lower() and 'music.163.com' in url:
                self.logger.info(f"可能登录成功，跳转到: {url}")
                log_webview_event("possible_login_success", url, True, "可能登录成功")
            
            # 验证 localStorage 配置和音量设置
            if 'music.163.com' in url:
                self.verify_localstorage_and_volume()
        else:
            self.logger.error(f"页面加载失败: {url}")
            log_webview_event("load_finished", url, False, "页面加载失败")
    
    def verify_localstorage_and_volume(self):
        """验证 localStorage 配置和音量设置"""
        try:
            # 延迟执行，确保页面完全加载
            QTimer.singleShot(2000, self._check_localstorage_and_volume)
        except Exception as e:
            self.logger.error(f"验证 localStorage 和音量设置失败: {e}")
    
    def _check_localstorage_and_volume(self):
        """检查 localStorage 和音量设置"""
        try:
            js_code = """
            (function() {
                try {
                    // 检查 localStorage 是否可用
                    var localStorageAvailable = typeof(Storage) !== "undefined" && window.localStorage !== null;
                    
                    var volumeInfo = {
                        localStorageAvailable: localStorageAvailable,
                        volumeSettings: {}
                    };
                    
                    if (localStorageAvailable) {
                        try {
                            // 检查网易云音乐可能存储的音量相关键值
                            var volumeKeys = ['volume', 'playerVolume', 'musicVolume', 'netease_volume'];
                            
                            for (var i = 0; i < volumeKeys.length; i++) {
                                var key = volumeKeys[i];
                                if (localStorage.getItem(key) !== null) {
                                    volumeInfo.volumeSettings[key] = localStorage.getItem(key);
                                }
                            }
                            
                            // 检查是否有其他可能的设置键
                            var allKeys = Object.keys(localStorage);
                            volumeInfo.allKeys = allKeys;
                            volumeInfo.totalKeys = allKeys.length;
                            
                        } catch (e) {
                            volumeInfo.error = "localStorage access error: " + e.message;
                        }
                    } else {
                        volumeInfo.error = "localStorage not available";
                    }
                    
                    return volumeInfo;
                    
                } catch (e) {
                    return {
                        error: "Check failed: " + e.message,
                        localStorageAvailable: false
                    };
                }
            })();
            """
            
            self.web_view.page().runJavaScript(js_code, self.on_localstorage_check_result)
            
        except Exception as e:
            self.logger.error(f"执行 localStorage 检查失败: {e}")
    
    def on_localstorage_check_result(self, result):
        """处理 localStorage 检查结果"""
        try:
            if not result:
                self.logger.warning("localStorage 检查返回空结果")
                return
            
            if isinstance(result, dict):
                if result.get("localStorageAvailable"):
                    self.logger.info("✓ localStorage 可用，配置正确")
                    
                    volume_settings = result.get("volumeSettings", {})
                    if volume_settings:
                        self.logger.info(f"检测到音量相关设置: {list(volume_settings.keys())}")
                        for key, value in volume_settings.items():
                            self.logger.debug(f"  {key}: {value}")
                    else:
                        self.logger.debug("未检测到音量相关设置")
                    
                    all_keys = result.get("allKeys", [])
                    total_keys = result.get("totalKeys", 0)
                    self.logger.info(f"localStorage 总键数: {total_keys}")
                    
                    # 记录所有键（调试用）
                    if total_keys > 0 and total_keys <= 20:  # 避免日志过多
                        self.logger.debug(f"所有 localStorage 键: {all_keys}")
                    
                else:
                    error_msg = result.get("error", "未知错误")
                    self.logger.warning(f"localStorage 不可用或配置错误: {error_msg}")
                    
        except Exception as e:
            self.logger.error(f"处理 localStorage 检查结果失败: {e}")
    
    def on_title_changed(self, title):
        """页面标题变化"""
        self.logger.debug(f"页面标题变化: {title}")
        if title:
            self.setWindowTitle(f"网易云音乐 - {title}")
    
    def load_window_settings(self):
        """加载窗口设置"""
        try:
            if not hasattr(self, 'profile_manager') or not self.profile_manager:
                self.logger.warning("Profile管理器未初始化，跳过窗口设置加载")
                return
            
            window_data = self.profile_manager.load_window_geometry()
            
            if window_data["valid"] and window_data["geometry"]:
                # 恢复窗口几何信息
                self.restoreGeometry(window_data["geometry"])
                
                # 恢复最大化状态
                if window_data["maximized"]:
                    self.showMaximized()
                
                self.logger.info(f"窗口设置加载成功，保存时间: {window_data['last_saved']}")
            else:
                self.logger.debug("未找到有效的窗口设置，使用默认设置")
                
        except Exception as e:
            self.logger.error(f"加载窗口设置失败: {e}")
    
    def save_window_settings(self):
        """保存窗口设置"""
        try:
            if not hasattr(self, 'profile_manager') or not self.profile_manager:
                self.logger.warning("Profile管理器未初始化，跳过窗口设置保存")
                return
            
            # 获取当前窗口几何信息
            geometry_qbytearray = self.saveGeometry()
            maximized = self.isMaximized()
            
            # 转换QByteArray为bytes
            geometry_bytes = geometry_qbytearray.data()
            
            # 保存到ProfileManager
            success = self.profile_manager.save_window_geometry(geometry_bytes, maximized)
            
            if success:
                self.logger.debug("窗口设置保存成功")
            else:
                self.logger.warning("窗口设置保存失败")
                
        except Exception as e:
            self.logger.error(f"保存窗口设置失败: {e}")
    
    def schedule_save_window_settings(self):
        """延迟保存窗口设置（避免频繁保存）"""
        try:
            # 如果定时器不存在，创建它
            if self.window_save_timer is None:
                self.window_save_timer = QTimer()
                self.window_save_timer.setSingleShot(True)
                self.window_save_timer.timeout.connect(self.save_window_settings)
            
            # 重新启动定时器（延迟1秒保存）
            self.window_save_timer.start(1000)
            
        except Exception as e:
            self.logger.error(f"调度窗口设置保存失败: {e}")
    
    def resizeEvent(self, event):
        """窗口大小变化事件"""
        super().resizeEvent(event)
        self.schedule_save_window_settings()
    
    def moveEvent(self, event):
        """窗口位置变化事件"""
        super().moveEvent(event)
        self.schedule_save_window_settings()
    
    def changeEvent(self, event):
        """窗口状态变化事件（包括最大化/最小化）"""
        super().changeEvent(event)
        
        # 检查是否是窗口状态变化
        if event.type() == event.Type.WindowStateChange:
            self.schedule_save_window_settings()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.logger.info("正在关闭应用窗口...")
        
        try:
            # 停止定时器（只保留新的增强监控定时器）
            if hasattr(self, 'enhanced_login_timer'):
                self.enhanced_login_timer.stop()
                self.logger.debug("增强登录监控定时器已停止")
            
            # 备份登录数据（在关闭前）
            if hasattr(self, 'profile_manager') and self.profile_manager:
                try:
                    backup_success = self.profile_manager.backup_login_data("shutdown")
                    if backup_success:
                        self.logger.info("登录数据备份成功（关闭前）")
                    else:
                        self.logger.warning("登录数据备份失败（关闭前）")
                except Exception as e:
                    self.logger.warning(f"备份数据时出错: {e}")
            
            # 清理Profile管理器
            if hasattr(self, 'profile_manager') and self.profile_manager:
                self.profile_manager.close()
                self.logger.debug("Profile管理器已清理")
            
            log_webview_event("window_close", "", True, "用户关闭窗口，资源清理完成")
            
        except Exception as e:
            self.logger.error(f"关闭窗口时清理资源失败: {e}")
            log_webview_event("window_close", "", False, f"资源清理失败: {e}")
        
        finally:
            super().closeEvent(event)


def main():
    # 初始化日志系统
    try:
        logger_manager = init_logging(
            level="INFO",  # 可以通过环境变量 NETEASE_LOG_LEVEL 覆盖
            console_output=True,  # 可以通过环境变量 NETEASE_LOG_CONSOLE 覆盖
            file_output=True,     # 可以通过环境变量 NETEASE_LOG_FILE 覆盖
            json_output=False      # 可以通过环境变量 NETEASE_LOG_JSON 覆盖
        )
        app_logger = get_logger("main")
        app_logger.info("日志系统初始化成功")
    except Exception as e:
        print(f"初始化日志系统失败: {e}")
        # 使用基本日志作为后备
        import logging
        logging.basicConfig(level=logging.INFO)
        app_logger = logging.getLogger("main")
        app_logger.warning("使用基本日志系统作为后备")
    
    try:
        # 创建应用实例
        app = QApplication(sys.argv)
        app_logger.info("创建QApplication实例")
        
        # 设置应用信息
        app.setApplicationName("网易云音乐桌面版")
        app.setOrganizationName("NetEase Music Desktop")
        app_logger.debug("设置应用信息完成")
        
        # 创建主窗口
        app_logger.info("正在创建主窗口...")
        window = NetEaseMusicWindow()
        
        # 显示窗口
        window.show()
        app_logger.info("主窗口显示完成")
        
        # 记录启动性能
        log_startup_performance()
        
        # 运行应用
        app_logger.info("开始运行应用主循环")
        result = app.exec()
        
        # 清理Profile管理器
        cleanup_profile_manager()
        
        # 清理日志系统
        from logger import cleanup_logging
        cleanup_logging()
        
        sys.exit(result)
        
    except Exception as e:
        app_logger.critical(f"应用运行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
