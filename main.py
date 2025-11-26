#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐网页播放器桌面版
使用PySide6创建原生窗口壳
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QUrl, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile


class NetEaseMusicWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口标题
        self.setWindowTitle("网易云音乐")
        
        # 设置窗口大小 (适合播放器的尺寸)
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        # 创建网页视图
        self.web_view = QWebEngineView()
        
        # 精简的登录状态持久化配置
        profile = self.web_view.page().profile()
        
        # 使用绝对路径确保目录能创建
        login_data_path = os.path.abspath("./login_data")
        os.makedirs(login_data_path, exist_ok=True)
        
        # 只保存登录相关的核心数据
        profile.setPersistentStoragePath(login_data_path)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        
        # 使用内存缓存，避免存储大量音频文件
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        
        # 调试信息
        print(f"登录数据存储路径: {login_data_path}")
        
        # 加载网易云音乐播放器
        self.web_view.setUrl(QUrl("https://music.163.com/st/webplayer"))
        
        # 设置为中心控件
        self.setCentralWidget(self.web_view)
        
        # 如果有图标文件，可以设置窗口图标
        try:
            self.setWindowIcon(QIcon("assets/icon.png"))
        except:
            pass  # 如果图标文件不存在，忽略错误


def main():
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("网易云音乐桌面版")
    app.setOrganizationName("NetEase Music Desktop")
    
    # 创建主窗口
    window = NetEaseMusicWindow()
    
    # 显示窗口
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
