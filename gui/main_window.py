#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐主窗口GUI模块
"""

import os
import time
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage

# 导入日志系统和相关管理器
from logger import get_logger, log_login_operation, log_webview_event
from profile_manager import get_profile_manager
from tray_manager import TrayManager, is_tray_supported, get_tray_backend
from gui.close_confirm_dialog import show_close_confirm_dialog
from gui.settings_dialog import show_settings_dialog


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
            
            # 设置窗口图标
            try:
                # 处理PyInstaller打包后的路径
                import sys
                if hasattr(sys, '_MEIPASS'):
                    base_path = sys._MEIPASS
                else:
                    base_path = os.getcwd()
                
                # Linux桌面环境推荐的图标尺寸顺序（针对GNOME优化）
                icon_paths = [
                    "icon/icon_48x48.png",    # GNOME任务栏标准尺寸
                    "icon/icon_64x64.png",    # 标准桌面图标尺寸
                    "icon/icon_32x32.png",    # 小尺寸图标
                    "icon/icon_128x128.png",  # 高DPI显示器
                    "icon/icon_24x24.png",    # 小型托盘/面板
                    "icon/icon_16x16.png",    # 极小尺寸
                    "icon/icon_256x256.png"   # 超高分辨率
                ]
                
                icon_set = False
                for icon_path in icon_paths:
                    full_path = os.path.join(base_path, icon_path)
                    if os.path.exists(full_path):
                        window_icon = QIcon(full_path)
                        if not window_icon.isNull():
                            self.setWindowIcon(window_icon)
                            self.logger.debug(f"设置窗口图标: {full_path}")
                            icon_set = True
                            break
                
                if not icon_set:
                    self.logger.warning("未找到合适的窗口图标文件")
                else:
                    # 额外设置应用级图标以确保最小化时也显示
                    from PySide6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app and icon_set:
                        # 如果main.py中已经设置了应用图标，这里不需要重复设置
                        self.logger.debug("窗口图标设置成功，应用级图标已在main.py中设置")
                    
            except Exception as e:
                self.logger.warning(f"设置窗口图标失败: {e}")
            
            # 初始化系统托盘
            self.setup_system_tray()
                
        except Exception as e:
            self.logger.error(f"初始化用户界面失败: {e}", exc_info=True)
            raise
    
    def setup_system_tray(self):
        """设置系统托盘功能"""
        try:
            # 检查系统是否支持托盘
            if not is_tray_supported():
                self.logger.warning("系统不支持托盘功能")
                return
            
            self.logger.info(f"正在初始化系统托盘，使用后端: {get_tray_backend()}")
            
            # 创建托盘管理器
            self.tray_manager = TrayManager(self)
            
            # 设置WebView实例给托盘管理器（用于获取歌曲信息）
            if hasattr(self, 'web_view') and self.web_view:
                self.tray_manager.set_webview(self.web_view)
            
            # 连接托盘信号
            self.tray_manager.show_window_requested.connect(self.show_window)
            self.tray_manager.exit_requested.connect(self.exit_application)
            
            self.logger.info("系统托盘初始化成功")
            
        except Exception as e:
            self.logger.error(f"设置系统托盘失败: {e}", exc_info=True)
            # 托盘功能失败不应该阻止应用启动
            self.tray_manager = None
    
    def show_window(self):
        """显示窗口"""
        try:
            # 如果窗口被最小化或隐藏，则显示并激活
            if self.isHidden():
                self.show()
            
            if self.isMinimized():
                self.showNormal()
            
            # 将窗口置于前台
            self.raise_()
            self.activateWindow()
            
            self.logger.info("窗口已显示并激活")
            
        except Exception as e:
            self.logger.error(f"显示窗口失败: {e}", exc_info=True)
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        try:
            self.logger.info("显示设置对话框")
            settings_changed = show_settings_dialog(self)
            
            if settings_changed:
                self.logger.info("用户已更改设置")
                # 可以在这里添加设置更改后的处理逻辑
            else:
                self.logger.debug("用户取消设置更改或未更改设置")
                
        except Exception as e:
            self.logger.error(f"显示设置对话框失败: {e}", exc_info=True)

    def exit_application(self):
        """退出应用程序"""
        try:
            self.logger.info("正在退出应用程序...")
            
            # 清理托盘资源
            if hasattr(self, 'tray_manager') and self.tray_manager:
                self.tray_manager.cleanup()
                self.tray_manager = None
            
            # 正常关闭窗口
            self.close()
            
        except Exception as e:
            self.logger.error(f"退出应用程序失败: {e}", exc_info=True)
            # 强制退出
            from PySide6.QtWidgets import QApplication
            QApplication.quit()
    
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
                    total_keys = result.get("total_keys", 0)
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
            self.setWindowTitle(f"{title} - 网页封装版")
    
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
        """窗口关闭事件 - 支持用户偏好设置"""
        try:
            self.logger.info("处理窗口关闭事件...")
            
            # 获取关闭行为偏好
            close_behavior = self.profile_manager.get_close_behavior()
            action = close_behavior.get("action", "ask")
            first_time = close_behavior.get("first_time", True)
            remember_choice = close_behavior.get("remember_choice", False)
            
            self.logger.info(f"关闭行为偏好: action={action}, first_time={first_time}, remember_choice={remember_choice}")
            
            # 检查是否有系统托盘且托盘可见
            has_tray = (hasattr(self, 'tray_manager') and 
                       self.tray_manager and 
                       self.tray_manager.is_visible)
            
            # 如果没有托盘，直接关闭程序
            if not has_tray:
                self.logger.info("系统不支持托盘或托盘不可见，直接关闭程序")
                self._perform_actual_close(event)
                return
            
            # 根据用户偏好处理关闭行为
            if action == "exit_program":
                # 用户偏好是直接退出程序
                self.logger.info("用户偏好设置：直接退出程序")
                self._perform_actual_close(event)
                return
            
            elif action == "minimize_to_tray":
                # 用户偏好是最小化到托盘
                self.logger.info("用户偏好设置：最小化到托盘")
                self._minimize_to_tray(event)
                return
            
            else:  # action == "ask" 或其他情况
                # 需要询问用户
                self.logger.info("需要询问用户关闭行为")
                user_action, remember = show_close_confirm_dialog(self)
                
                if user_action is None:
                    # 用户取消了对话框，不关闭窗口
                    self.logger.info("用户取消了关闭操作")
                    event.ignore()
                    return
                
                # 保存用户选择
                if remember:
                    self.logger.info(f"用户选择记住偏好: {user_action}")
                    success = self.profile_manager.update_close_behavior(user_action, True)
                    if success:
                        self.logger.info("用户偏好保存成功")
                    else:
                        self.logger.warning("用户偏好保存失败")
                else:
                    self.logger.info(f"用户选择不记住偏好: {user_action}")
                
                # 执行用户选择的行为
                if user_action == "exit_program":
                    self.logger.info("用户选择：退出程序")
                    self._perform_actual_close(event)
                elif user_action == "minimize_to_tray":
                    self.logger.info("用户选择：最小化到托盘")
                    self._minimize_to_tray(event)
                else:
                    # 默认情况下最小化到托盘
                    self.logger.info("默认行为：最小化到托盘")
                    self._minimize_to_tray(event)
            
        except Exception as e:
            self.logger.error(f"处理窗口关闭事件失败: {e}", exc_info=True)
            # 发生错误时，默认执行关闭程序
            self._perform_actual_close(event)
    
    def _minimize_to_tray(self, event):
        """最小化窗口到系统托盘"""
        try:
            self.logger.info("最小化窗口到系统托盘")
            
            # 隐藏窗口而不是关闭应用
            self.hide()
            
            # 阻止窗口关闭事件的默认行为
            event.ignore()
            
            # 显示系统托盘通知
            if hasattr(self, 'tray_manager') and self.tray_manager and hasattr(self.tray_manager, 'qt_tray') and self.tray_manager.qt_tray:
                try:
                    from PySide6.QtWidgets import QApplication
                    app_style = QApplication.style()
                    info_icon = app_style.standardIcon(
                        app_style.StandardPixmap.SP_MessageBoxInformation
                    )
                    self.tray_manager.qt_tray.showMessage(
                        "网易云音乐",
                        "应用程序已最小化到系统托盘\n点击托盘图标可恢复窗口",
                        info_icon,
                        3000  # 显示3秒
                    )
                except Exception as notify_error:
                    self.logger.warning(f"显示托盘通知失败: {notify_error}")
            
            self.logger.info("窗口已最小化到系统托盘")
            
        except Exception as e:
            self.logger.error(f"最小化到托盘失败: {e}", exc_info=True)
            # 如果最小化失败，执行实际关闭
            self._perform_actual_close(event)
    
    def _perform_actual_close(self, event):
        """执行实际的程序关闭操作"""
        try:
            self.logger.info("执行程序关闭操作...")
            
            # 停止定时器
            if hasattr(self, 'enhanced_login_timer'):
                self.enhanced_login_timer.stop()
                self.logger.debug("增强登录监控定时器已停止")
            
            if hasattr(self, 'window_save_timer') and self.window_save_timer:
                self.window_save_timer.stop()
                self.logger.debug("窗口设置保存定时器已停止")
            
            # 保存窗口设置
            try:
                self.save_window_settings()
            except Exception as e:
                self.logger.warning(f"保存窗口设置失败: {e}")
            
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
            
            # 清理托盘资源
            if hasattr(self, 'tray_manager') and self.tray_manager:
                self.tray_manager.cleanup()
                self.logger.debug("系统托盘资源已清理")
            
            # 清理Profile管理器
            if hasattr(self, 'profile_manager') and self.profile_manager:
                self.profile_manager.close()
                self.logger.debug("Profile管理器已清理")
            
            log_webview_event("window_close", "", True, "程序关闭完成，资源清理完成")
            
            # 调用父类的closeEvent以完成关闭
            super().closeEvent(event)
            
        except Exception as e:
            self.logger.error(f"执行程序关闭操作失败: {e}", exc_info=True)
            # 强制退出
            try:
                from PySide6.QtWidgets import QApplication
                QApplication.quit()
            except Exception as quit_error:
                self.logger.error(f"强制退出失败: {quit_error}")
                import sys
                sys.exit(1)
