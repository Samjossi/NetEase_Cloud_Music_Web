#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 运行网易云音乐桌面版
"""

import subprocess
import sys
import os
import logging

# 简单的日志配置用于启动阶段
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
startup_logger = logging.getLogger("startup")

def check_dependencies():
    """检查依赖是否已安装"""
    startup_logger.info("开始检查依赖...")
    try:
        import PySide6
        import PySide6.QtWebEngineWidgets
        startup_logger.info(f"PySide6版本: {PySide6.__version__}")
        startup_logger.info("✓ 依赖检查通过")
        return True
    except ImportError as e:
        startup_logger.error(f"✗ 缺少依赖: {e}")
        print("请先运行: pip install -r requirements.txt")
        return False

def check_environment():
    """检查运行环境"""
    startup_logger.info("检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        startup_logger.error(f"Python版本过低: {sys.version}")
        startup_logger.error("需要Python 3.8或更高版本")
        return False
    
    startup_logger.info(f"Python版本: {sys.version}")
    
    # 检查工作目录
    startup_logger.info(f"当前工作目录: {os.getcwd()}")
    
    # 检查必要文件
    required_files = ["main.py", "logger/__init__.py"]
    for file in required_files:
        if not os.path.exists(file):
            startup_logger.error(f"缺少必要文件: {file}")
            return False
        else:
            startup_logger.debug(f"文件检查通过: {file}")
    
    startup_logger.info("环境检查完成")
    return True

def cleanup_on_exit():
    """退出时清理资源"""
    startup_logger.info("正在清理启动脚本资源...")

def main():
    startup_logger.info("=== 网易云音乐桌面版启动脚本 ===")
    startup_logger.info("正在启动网易云音乐桌面版...")
    
    try:
        # 检查环境
        if not check_environment():
            startup_logger.error("环境检查失败")
            input("按回车键退出...")
            return
        
        # 检查依赖
        if not check_dependencies():
            startup_logger.error("依赖检查失败")
            input("按回车键退出...")
            return
        
        startup_logger.info("所有检查通过，准备启动主程序...")
        
        # 运行主程序
        try:
            from main import main as app_main
            startup_logger.info("导入主程序模块成功")
            app_main()
        except ImportError as e:
            startup_logger.error(f"导入主程序失败: {e}")
            print(f"导入失败: {e}")
            input("按回车键退出...")
        except Exception as e:
            startup_logger.critical(f"启动失败: {e}", exc_info=True)
            print(f"启动失败: {e}")
            input("按回车键退出...")
            
    except KeyboardInterrupt:
        startup_logger.info("用户中断启动")
    except Exception as e:
        startup_logger.critical(f"启动脚本异常: {e}", exc_info=True)
        print(f"启动脚本异常: {e}")
        input("按回车键退出...")
    finally:
        cleanup_on_exit()

if __name__ == "__main__":
    main()
