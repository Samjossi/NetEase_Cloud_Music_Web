#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐网页播放器桌面版 - 应用入口
使用PySide6创建原生窗口壳
"""

import sys
from PySide6.QtWidgets import QApplication

# 导入日志系统
from logger import init_logging, get_logger, log_startup_performance
from profile_manager import cleanup_profile_manager

# 导入GUI模块
from gui import NetEaseMusicWindow


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
