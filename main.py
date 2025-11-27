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

# 导入日志系统
from logger import init_logging, get_logger, log_login_operation, log_webview_event, log_startup_performance


class NetEaseMusicWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = get_logger("window")
        self.logger.info("正在初始化主窗口...")
        
        self.init_ui()
        self.setup_webview_monitoring()
        
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
            
            # 创建网页视图
            self.web_view = QWebEngineView()
            self.logger.debug("创建WebView组件")
            
            # 精简的登录状态持久化配置
            profile = self.web_view.page().profile()
            
            # 使用绝对路径确保目录能创建
            login_data_path = os.path.abspath("./login_data")
            try:
                os.makedirs(login_data_path, exist_ok=True)
                log_login_operation("create_directory", login_data_path, True, "登录数据目录创建成功")
            except Exception as e:
                log_login_operation("create_directory", login_data_path, False, str(e))
                self.logger.error(f"创建登录数据目录失败: {e}")
            
            # 只保存登录相关的核心数据
            profile.setPersistentStoragePath(login_data_path)
            profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
            log_login_operation("set_persistent_storage", login_data_path, True, 
                               f"设置持久化存储路径: {login_data_path}")
            
            # 使用内存缓存，避免存储大量音频文件
            profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
            self.logger.debug("设置HTTP缓存类型为内存缓存")
            
            # 记录登录数据存储信息
            self.logger.info(f"登录数据存储路径: {login_data_path}")
            
            # 添加定期检查登录数据的定时器
            self.setup_login_data_monitor(login_data_path)
            
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
    
    def setup_login_data_monitor(self, login_data_path):
        """设置登录数据监控"""
        try:
            # 创建定时器，定期检查登录数据目录
            self.login_monitor_timer = QTimer()
            self.login_monitor_timer.timeout.connect(lambda: self.check_login_data(login_data_path))
            self.login_monitor_timer.start(5000)  # 每5秒检查一次
            
            self.logger.debug("登录数据监控定时器已启动")
        except Exception as e:
            self.logger.error(f"设置登录数据监控失败: {e}")
    
    def check_login_data(self, login_data_path):
        """检查登录数据目录的变化"""
        try:
            if os.path.exists(login_data_path):
                files = os.listdir(login_data_path)
                if files:
                    for file in files:
                        file_path = os.path.join(login_data_path, file)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            log_login_operation("file_detected", file_path, True, f"文件大小: {size} 字节")
                            
                            # 如果是新的数据库文件，记录详细信息
                            if file.endswith(('.db', '.sqlite', '.cookies')):
                                self.logger.info(f"检测到登录数据文件: {file} ({size} 字节)")
                                log_login_operation("database_file_created", file_path, True, 
                                                 f"数据库文件大小: {size} 字节")
        except Exception as e:
            self.logger.error(f"检查登录数据失败: {e}")
    
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
        else:
            self.logger.error(f"页面加载失败: {url}")
            log_webview_event("load_finished", url, False, "页面加载失败")
    
    def on_title_changed(self, title):
        """页面标题变化"""
        self.logger.debug(f"页面标题变化: {title}")
        if title:
            self.setWindowTitle(f"网易云音乐 - {title}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.logger.info("正在关闭应用窗口...")
        
        # 停止定时器
        if hasattr(self, 'login_monitor_timer'):
            self.login_monitor_timer.stop()
        
        log_webview_event("window_close", "", True, "用户关闭窗口")
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
        
        # 清理日志系统
        from logger import cleanup_logging
        cleanup_logging()
        
        sys.exit(result)
        
    except Exception as e:
        app_logger.critical(f"应用运行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
