#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录数据持久化诊断脚本
分析为什么登录数据没有被正确保存
"""

import os
import sys
import time
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnose_pywebengine_settings():
    """诊断PySide6 WebEngine设置"""
    print("=== PySide6 WebEngine 诊断 ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWebEngineCore import QWebEngineProfile
        
        # 创建临时应用实例
        app = QApplication([])
        
        # 创建WebView和Profile
        web_view = QWebEngineView()
        profile = web_view.page().profile()
        
        print(f"当前Profile类型: {type(profile)}")
        print(f"默认持久化存储路径: {profile.persistentStoragePath()}")
        print(f"默认Cookie策略: {profile.persistentCookiesPolicy()}")
        print(f"默认HTTP缓存类型: {profile.httpCacheType()}")
        
        # 检查支持的存储类型
        print("\n=== 支持的Cookie策略 ===")
        policies = [
            ("NoPersistentCookies", QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies),
            ("AllowPersistentCookies", QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies),
            ("ForcePersistentCookies", QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies),
        ]
        for name, policy in policies:
            print(f"{name}: {policy}")
        
        print("\n=== 支持的HTTP缓存类型 ===")
        cache_types = [
            ("MemoryHttpCache", QWebEngineProfile.HttpCacheType.MemoryHttpCache),
            ("DiskHttpCache", QWebEngineProfile.HttpCacheType.DiskHttpCache),
        ]
        for name, cache_type in cache_types:
            print(f"{name}: {cache_type}")
        
        # 清理
        web_view.deleteLater()
        app.quit()
        
    except Exception as e:
        print(f"诊断失败: {e}")
        import traceback
        traceback.print_exc()

def test_directory_permissions():
    """测试目录权限"""
    print("\n=== 目录权限测试 ===")
    
    login_data_path = os.path.abspath("./login_data")
    print(f"测试目录: {login_data_path}")
    
    try:
        # 创建目录
        os.makedirs(login_data_path, exist_ok=True)
        print("✓ 目录创建成功")
        
        # 测试写入权限
        test_file = os.path.join(login_data_path, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        print("✓ 写入权限正常")
        
        # 测试读取权限
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"✓ 读取权限正常: {content}")
        
        # 测试删除权限
        os.remove(test_file)
        print("✓ 删除权限正常")
        
        # 检查目录所有者
        stat_info = os.stat(login_data_path)
        print(f"目录所有者: UID {stat_info.st_uid}, GID {stat_info.st_gid}")
        print(f"目录权限: {oct(stat_info.st_mode)}")
        
    except Exception as e:
        print(f"✗ 权限测试失败: {e}")

def test_file_operations():
    """测试文件操作"""
    print("\n=== 文件操作测试 ===")
    
    login_data_path = os.path.abspath("./login_data")
    
    try:
        # 模拟WebEngine可能创建的文件类型
        test_files = [
            "Cookies",
            "Cookies-journal", 
            "Local Storage",
            "Web Data",
            "Web Data-journal",
            "Quota Manager",
            "Visited Links",
            "Current Session",
            "Last Session",
            "Preferences",
        ]
        
        for filename in test_files:
            file_path = os.path.join(login_data_path, filename)
            
            # 测试创建文件
            with open(file_path, 'w') as f:
                f.write(f"test content for {filename}")
            
            size = os.path.getsize(file_path)
            print(f"✓ 创建文件 {filename}: {size} 字节")
            
            # 模拟数据库文件（二进制）
            if filename.endswith(('Data', 'Storage')):
                db_path = os.path.join(login_data_path, f"{filename}.db")
                with open(db_path, 'wb') as f:
                    f.write(b'\x53\x51\x4C\x69\x74\x65\x20\x66\x6f\x72\x6d\x61\x74\x20\x33\x00')
                print(f"✓ 创建数据库 {filename}.db")
        
        # 列出所有文件
        print(f"\n目录中的文件:")
        for root, dirs, files in os.walk(login_data_path):
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                print(f"  {file}: {size} 字节")
        
        # 清理测试文件
        import shutil
        shutil.rmtree(login_data_path)
        print("✓ 清理测试文件完成")
        
    except Exception as e:
        print(f"✗ 文件操作测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_webengine_profile_creation():
    """测试WebEngine Profile创建"""
    print("\n=== WebEngine Profile 创建测试 ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWebEngineCore import QWebEngineProfile
        
        # 创建应用
        app = QApplication([])
        
        # 测试不同的Profile设置
        login_data_path = os.path.abspath("./login_data")
        os.makedirs(login_data_path, exist_ok=True)
        
        print(f"测试路径: {login_data_path}")
        
        # 创建多个Profile实例测试
        profiles = []
        for i in range(3):
            web_view = QWebEngineView()
            profile = web_view.page().profile()
            
            profile.setPersistentStoragePath(login_data_path)
            profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
            profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            
            profiles.append((web_view, profile))
            print(f"Profile {i+1}:")
            print(f"  存储路径: {profile.persistentStoragePath()}")
            print(f"  Cookie策略: {profile.persistentCookiesPolicy()}")
            print(f"  缓存类型: {profile.httpCacheType()}")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 等待一段时间，看看是否会创建文件
        print("等待5秒，检查文件创建...")
        time.sleep(5)
        
        # 检查文件
        if os.path.exists(login_data_path):
            files = os.listdir(login_data_path)
            if files:
                print(f"检测到文件: {files}")
            else:
                print("未检测到任何文件")
        
        # 清理
        for web_view, profile in profiles:
            web_view.deleteLater()
        app.quit()
        
    except Exception as e:
        print(f"Profile创建测试失败: {e}")
        import traceback
        traceback.print_exc()

def check_system_info():
    """检查系统信息"""
    print("\n=== 系统信息 ===")
    
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"用户主目录: {os.path.expanduser('~')}")
    
    # 检查临时目录
    import tempfile
    print(f"临时目录: {tempfile.gettempdir()}")
    
    # 检查环境变量
    env_vars = [
        'HOME', 'USER', 'USERNAME', 'XDG_DATA_HOME', 
        'XDG_CONFIG_HOME', 'XDG_CACHE_HOME'
    ]
    print("相关环境变量:")
    for var in env_vars:
        value = os.environ.get(var, '未设置')
        print(f"  {var}: {value}")

def main():
    """主诊断函数"""
    print("开始登录数据持久化诊断...\n")
    
    # 运行各项诊断
    check_system_info()
    test_directory_permissions()
    test_file_operations()
    diagnose_pywebengine_settings()
    test_webengine_profile_creation()
    
    print("\n=== 诊断完成 ===")
    print("请将以上信息提供给开发者进行问题分析")

if __name__ == "__main__":
    main()
