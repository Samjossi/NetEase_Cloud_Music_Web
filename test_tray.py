#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘功能测试脚本
验证托盘管理器的基本功能
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tray_manager import TrayManager, is_tray_supported, get_tray_backend
from logger import init_logging, get_logger

def test_tray_functionality():
    """测试托盘功能"""
    # 初始化日志
    init_logging(level="INFO", console_output=True, file_output=False)
    logger = get_logger("test_tray")
    
    logger.info("=== 系统托盘功能测试开始 ===")
    
    # 检查系统支持
    logger.info(f"系统托盘支持状态: {is_tray_supported()}")
    logger.info(f"使用的托盘后端: {get_tray_backend()}")
    
    if not is_tray_supported():
        logger.error("系统不支持托盘功能，测试终止")
        return False
    
    # 创建应用实例
    app = QApplication(sys.argv)
    
    try:
        # 创建托盘管理器
        logger.info("正在创建托盘管理器...")
        tray = TrayManager()
        
        # 连接信号用于测试
        def on_show_window():
            logger.info("✅ 收到显示窗口信号")
        
        def on_exit():
            logger.info("✅ 收到退出信号")
            app.quit()
        
        tray.show_window_requested.connect(on_show_window)
        tray.exit_requested.connect(on_exit)
        
        logger.info("✅ 托盘管理器创建成功")
        
        # 设置定时器自动退出测试（避免无限等待）
        QTimer.singleShot(10000, lambda: (
            logger.info("测试完成，正在退出..."),
            app.quit()
        ))
        
        logger.info("测试托盘功能...")
        logger.info("- 请检查系统托盘区域是否有网易云音乐图标")
        logger.info("- 右键点击图标查看菜单")
        logger.info("- 左键点击图标测试显示窗口功能")
        logger.info("- 测试将在10秒后自动退出")
        
        # 运行应用
        app.exec()
        
        # 清理资源
        tray.cleanup()
        logger.info("✅ 资源清理完成")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_tray_functionality()
    if success:
        print("\n🎉 系统托盘功能测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 系统托盘功能测试失败！")
        sys.exit(1)
