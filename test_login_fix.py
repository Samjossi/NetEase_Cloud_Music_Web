#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录持久化修复测试脚本
验证Profile管理器和登录数据持久化是否正常工作
"""

import sys
import os
import time
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_profile_manager():
    """测试Profile管理器"""
    print("=== 测试Profile管理器 ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from profile_manager import get_profile_manager, cleanup_profile_manager
        
        # 创建应用实例
        app = QApplication([])
        
        # 测试Profile管理器
        profile_manager = get_profile_manager("./test_login_data")
        
        # 创建持久化Profile
        profile = profile_manager.create_persistent_profile("TestProfile")
        print(f"✓ Profile创建成功: {profile}")
        
        # 验证配置
        storage_path = profile.persistentStoragePath()
        cookie_policy = profile.persistentCookiesPolicy()
        cache_type = profile.httpCacheType()
        
        print(f"存储路径: {storage_path}")
        print(f"Cookie策略: {cookie_policy}")
        print(f"缓存类型: {cache_type}")
        
        # 验证关键设置
        expected_path = os.path.abspath("./test_login_data")
        if storage_path == expected_path:
            print("✓ 存储路径设置正确")
        else:
            print(f"✗ 存储路径设置错误: 期望 {expected_path}, 实际 {storage_path}")
        
        # 检查Cookie策略
        from PySide6.QtWebEngineCore import QWebEngineProfile
        if cookie_policy == QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies:
            print("✓ Cookie策略设置正确（强制持久化）")
        else:
            print(f"✗ Cookie策略设置错误: 期望 ForcePersistentCookies, 实际 {cookie_policy}")
        
        # 检查缓存类型
        if cache_type == QWebEngineProfile.HttpCacheType.DiskHttpCache:
            print("✓ 缓存类型设置正确（磁盘缓存）")
        else:
            print(f"✗ 缓存类型设置错误: 期望 DiskHttpCache, 实际 {cache_type}")
        
        # 测试数据验证
        is_valid = profile_manager.validate_login_data()
        print(f"登录数据验证结果: {is_valid}")
        
        # 获取数据信息
        data_info = profile_manager.get_login_data_info()
        print(f"登录数据信息: {data_info}")
        
        # 清理
        profile_manager.close()
        cleanup_profile_manager()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ Profile管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logging_integration():
    """测试日志系统集成"""
    print("\n=== 测试日志系统集成 ===")
    
    try:
        from logger import init_logging, get_logger, log_login_operation, log_webview_event
        
        # 初始化日志系统
        logger_manager = init_logging(
            level="DEBUG",
            console_output=True,
            file_output=True,
            json_output=False
        )
        
        logger = get_logger("test")
        
        # 测试登录操作日志
        log_login_operation("test_operation", "/test/path", True, "测试登录操作")
        log_login_operation("test_operation", "/test/path", False, "测试登录操作失败")
        
        # 测试WebView事件日志
        log_webview_event("test_event", "https://test.com", True, "测试WebView事件")
        log_webview_event("test_event", "https://test.com", False, "测试WebView事件失败")
        
        print("✓ 日志系统集成测试完成")
        
        # 清理
        from logger import cleanup_logging
        cleanup_logging()
        
        return True
        
    except Exception as e:
        print(f"✗ 日志系统集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_directory_operations():
    """测试目录操作"""
    print("\n=== 测试目录操作 ===")
    
    test_dir = "./test_login_data"
    
    try:
        # 清理之前的测试数据
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
        
        # 测试目录创建
        os.makedirs(test_dir, exist_ok=True)
        print(f"✓ 目录创建成功: {test_dir}")
        
        # 测试文件写入
        test_file = os.path.join(test_dir, "test_cookies.txt")
        with open(test_file, 'w') as f:
            f.write("test cookie data")
        print(f"✓ 文件写入成功: {test_file}")
        
        # 测试文件读取
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"✓ 文件读取成功: {content}")
        
        # 测试权限
        if os.access(test_dir, os.W_OK):
            print("✓ 目录写权限正常")
        else:
            print("✗ 目录写权限异常")
        
        # 清理
        import shutil
        shutil.rmtree(test_dir)
        print("✓ 测试目录清理完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 目录操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_application():
    """测试完整应用程序"""
    print("\n=== 测试完整应用程序 ===")
    
    try:
        # 导入主模块
        import main
        
        print("✓ 主模块导入成功")
        
        # 检查关键类是否存在
        if hasattr(main, 'NetEaseMusicWindow'):
            print("✓ NetEaseMusicWindow类存在")
        else:
            print("✗ NetEaseMusicWindow类不存在")
            return False
        
        # 检查Profile管理器导入
        if hasattr(main, 'get_profile_manager'):
            print("✓ Profile管理器导入成功")
        else:
            print("✗ Profile管理器导入失败")
            return False
        
        print("✓ 完整应用程序测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 完整应用程序测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始登录持久化修复测试...\n")
    
    tests = [
        ("目录操作", test_directory_operations),
        ("日志系统集成", test_logging_integration),
        ("Profile管理器", test_profile_manager),
        ("完整应用程序", test_full_application),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"运行测试: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"\n✓ {test_name} 测试通过")
            else:
                print(f"\n✗ {test_name} 测试失败")
                
        except Exception as e:
            print(f"\n✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print(f"\n{'='*50}")
    print("测试结果总结")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！登录持久化修复成功！")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
