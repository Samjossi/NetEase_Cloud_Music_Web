#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统测试脚本
验证各个日志功能是否正常工作
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_logging():
    """测试基本日志功能"""
    print("=== 测试基本日志功能 ===")
    
    from logger import init_logging, get_logger, cleanup_logging
    
    # 初始化日志系统
    logger_manager = init_logging(
        level="DEBUG",
        console_output=True,
        file_output=True,
        json_output=False
    )
    
    # 获取不同类型的日志器
    main_logger = get_logger("test_main")
    login_logger = get_logger("login")
    webview_logger = get_logger("webview")
    
    # 测试不同级别的日志
    main_logger.debug("这是一条DEBUG级别的日志")
    main_logger.info("这是一条INFO级别的日志")
    main_logger.warning("这是一条WARNING级别的日志")
    main_logger.error("这是一条ERROR级别的日志")
    
    # 测试登录相关日志
    from logger import log_login_operation
    log_login_operation("test_login", "/test/path", True, "测试登录操作")
    log_login_operation("test_login_fail", "/test/path", False, "测试登录失败")
    
    # 测试WebView相关日志
    from logger import log_webview_event
    log_webview_event("load_url", "https://music.163.com", True, "测试页面加载")
    log_webview_event("load_error", "https://error.com", False, "测试页面加载失败")
    
    # 测试异常日志
    try:
        raise ValueError("这是一个测试异常")
    except Exception as e:
        main_logger.exception("捕获到测试异常")
    
    # 等待异步处理器完成
    time.sleep(1)
    
    # 清理
    cleanup_logging()
    
    print("基本日志功能测试完成\n")

def test_log_files():
    """测试日志文件是否正确生成"""
    print("=== 测试日志文件生成 ===")
    
    from logger import init_logging, get_logger, cleanup_logging
    
    # 初始化日志系统
    logger_manager = init_logging(
        level="DEBUG",
        console_output=False,  # 关闭控制台输出，只写文件
        file_output=True,
        json_output=False
    )
    
    # 生成一些测试日志
    main_logger = get_logger("test_files")
    main_logger.info("测试日志文件生成")
    main_logger.warning("测试警告信息")
    main_logger.error("测试错误信息")
    
    # 测试登录日志
    from logger import log_login_operation
    log_login_operation("file_test", "/test/login", True, "测试登录文件日志")
    
    # 测试WebView日志
    from logger import log_webview_event
    log_webview_event("file_test", "https://test.com", True, "测试WebView文件日志")
    
    # 等待文件写入
    time.sleep(2)
    
    # 检查日志文件
    log_dir = Path("logs")
    expected_files = ["app.log", "login.log", "webview.log", "error.log"]
    
    for file_name in expected_files:
        file_path = log_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✓ {file_name}: {size} 字节")
            
            # 读取最后几行内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"  最后一行: {lines[-1].strip()}")
            except Exception as e:
                print(f"  读取文件失败: {e}")
        else:
            print(f"✗ {file_name}: 文件不存在")
    
    # 清理
    cleanup_logging()
    
    print("日志文件生成测试完成\n")

def test_json_logging():
    """测试JSON格式日志"""
    print("=== 测试JSON格式日志 ===")
    
    from logger import init_logging, get_logger, cleanup_logging
    
    # 初始化JSON日志系统
    logger_manager = init_logging(
        level="INFO",
        console_output=False,
        file_output=True,
        json_output=True
    )
    
    # 获取性能日志器
    from logger import get_logger
    perf_logger = get_logger("performance")
    
    # 记录性能数据
    perf_logger.info("测试性能日志", extra={'extra_data': {
        'operation': 'test_operation',
        'duration': 0.123,
        'memory_usage': '45MB',
        'event': 'performance_test'
    }})
    
    # 等待文件写入
    time.sleep(1)
    
    # 检查JSON日志文件
    perf_log_path = Path("logs/performance.log")
    if perf_log_path.exists():
        print("✓ performance.log 文件已生成")
        try:
            with open(perf_log_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print(f"JSON内容: {content}")
                else:
                    print("文件为空")
        except Exception as e:
            print(f"读取JSON文件失败: {e}")
    else:
        print("✗ performance.log 文件不存在")
    
    # 清理
    cleanup_logging()
    
    print("JSON格式日志测试完成\n")

def test_configuration():
    """测试配置系统"""
    print("=== 测试配置系统 ===")
    
    try:
        from config.logging_config import LoggingConfig, EnvConfig, get_logging_config
        
        # 测试默认配置
        config_manager = LoggingConfig()
        config = config_manager.load_config()
        print("✓ 默认配置加载成功")
        
        # 测试环境变量
        os.environ["NETEASE_LOG_LEVEL"] = "DEBUG"
        os.environ["NETEASE_LOG_CONSOLE"] = "false"
        
        env_level = EnvConfig.get_log_level()
        env_console = EnvConfig.get_console_output()
        
        print(f"✓ 环境变量日志级别: {env_level}")
        print(f"✓ 环境变量控制台输出: {env_console}")
        
        # 测试合并配置
        merged_config = get_logging_config()
        print("✓ 配置合并成功")
        
    except Exception as e:
        print(f"✗ 配置系统测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("配置系统测试完成\n")

def cleanup_test_logs():
    """清理测试生成的日志文件"""
    print("=== 清理测试日志文件 ===")
    
    log_dir = Path("logs")
    if log_dir.exists():
        for log_file in log_dir.glob("*.log"):
            try:
                log_file.unlink()
                print(f"删除: {log_file}")
            except Exception as e:
                print(f"删除失败 {log_file}: {e}")
    
    # 清理配置文件
    config_file = Path("config/logging.json")
    if config_file.exists():
        try:
            config_file.unlink()
            print(f"删除: {config_file}")
        except Exception as e:
            print(f"删除失败 {config_file}: {e}")
    
    print("清理完成\n")

def main():
    """主测试函数"""
    print("开始日志系统测试...\n")
    
    # 清理之前的测试文件
    cleanup_test_logs()
    
    try:
        # 运行各项测试
        test_basic_logging()
        test_log_files()
        test_json_logging()
        test_configuration()
        
        print("=== 所有测试完成 ===")
        print("请检查 logs/ 目录中的日志文件以验证功能")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 询问是否清理测试文件
    try:
        response = input("是否清理测试文件? (y/n): ").lower()
        if response == 'y':
            cleanup_test_logs()
    except KeyboardInterrupt:
        print("\n测试结束")

if __name__ == "__main__":
    main()
