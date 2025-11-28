#!/usr/bin/env python3
"""
PyInstaller规格文件生成器 v2.0
专注于兼容性和可靠性
"""

import os
import sys
from pathlib import Path
import subprocess

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
PACKAGING_DIR = Path(__file__).parent

def collect_hidden_imports():
    """收集所有必要的隐藏导入"""
    
    # 基础PySide6组件
    pyside6_imports = [
        "PySide6.QtCore",
        "PySide6.QtGui", 
        "PySide6.QtWidgets",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtNetwork",
        "PySide6.QtWebEngine",
        "PySide6.QtPrintSupport",
        "PySide6.QtSvg",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
    ]
    
    # PySide6内部模块（确保完整打包）
    pyside6_internal = [
        "PySide6.QtCore.qbytearray",
        "PySide6.QtCore.qobject",
        "PySide6.QtGui.qicon",
        "PySide6.QtWidgets.qapplication",
        "PySide6.QtWebEngineCore.qwebenginepage",
        "PySide6.QtWebEngineWidgets.qwebengineview",
    ]
    
    # 应用模块
    app_modules = [
        "gui",
        "gui.main_window",
        "gui.settings_dialog", 
        "gui.close_confirm_dialog",
        "logger",
        "logger.formatters",
        "logger.handlers",
        "profile_manager",
        "tray_manager",
    ]
    
    # 标准库模块
    std_lib_modules = [
        "json",
        "os",
        "sys",
        "pathlib",
        "logging",
        "datetime",
        "threading",
        "subprocess",
        "time",
        "base64",
        "shutil",
        "tempfile",
        "traceback",
        "inspect",
        "types",
        "collections",
        "itertools",
        "functools",
        "re",
        "urllib",
        "urllib.parse",
        "urllib.request",
        "http.client",
        "socket",
        "ssl",
        "hashlib",
        "hmac",
        "secrets",
    ]
    
    # 网络相关
    network_modules = [
        "socketserver",
        "http.server",
        "email",
        "email.mime",
        "email.mime.text",
        "email.mime.multipart",
    ]
    
    # 可能需要的其他模块
    extra_modules = [
        "numpy",  # 如果存在
        "PIL",    # 如果存在
        "PIL.Image",
        "cryptography",
        "certifi",
        "idna",
    ]
    
    all_imports = (pyside6_imports + pyside6_internal + app_modules + 
                   std_lib_modules + network_modules + extra_modules)
    
    # 检查哪些模块实际可用
    available_imports = []
    for module in all_imports:
        try:
            __import__(module)
            available_imports.append(module)
        except ImportError:
            pass
    
    return available_imports


def collect_data_files():
    """收集所有需要打包的数据文件"""
    
    data_files = []
    
    # 图标文件
    icon_dir = PROJECT_ROOT / "icon"
    if icon_dir.exists():
        # 收集所有图标文件
        for icon_file in icon_dir.glob("*.png"):
            data_files.append((str(icon_file), "icon"))
        
        for icon_file in icon_dir.glob("*.ico"):
            data_files.append((str(icon_file), "icon"))
            
        for icon_file in icon_dir.glob("*.svg"):
            data_files.append((str(icon_file), "icon"))
    
    # 配置文件
    config_dir = PROJECT_ROOT / "config"
    if config_dir.exists():
        data_files.append((str(config_dir / "*"), "config"))
    
    # 其他可能的资源文件
    resource_patterns = [
        ("resources", "resources"),
        ("assets", "assets"), 
        ("data", "data"),
        ("static", "static"),
    ]
    
    for pattern_name, target_dir in resource_patterns:
        resource_dir = PROJECT_ROOT / pattern_name
        if resource_dir.exists():
            data_files.append((str(resource_dir / "*"), target_dir))
    
    return data_files


def get_pyside6_plugins():
    """获取PySide6需要的插件路径"""
    
    try:
        import PySide6
        pyside6_path = Path(PySide6.__file__).parent
        
        # 常见的插件目录
        plugin_dirs = [
            pyside6_path / "plugins",
            pyside6_path / "Qt6" / "plugins",
            pyside6_path.parent / "PySide6" / "plugins",
            pyside6_path.parent / "PySide6" / "Qt6" / "plugins",
        ]
        
        valid_plugins = []
        for plugin_dir in plugin_dirs:
            if plugin_dir.exists():
                # 添加所有插件目录
                for plugin_subdir in plugin_dir.iterdir():
                    if plugin_subdir.is_dir():
                        valid_plugins.append((str(plugin_subdir), f"plugins/{plugin_subdir.name}"))
        
        return valid_plugins
        
    except ImportError:
        return []


def create_spec_file():
    """创建优化的PyInstaller规格文件"""
    
    # 收集所有导入和数据文件
    hidden_imports = collect_hidden_imports()
    data_files = collect_data_files()
    pyside6_plugins = get_pyside6_plugins()
    
    # 合并所有数据文件
    all_data_files = data_files + pyside6_plugins
    
    # 构建规格文件内容
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

"""
网易云音乐桌面版 - PyInstaller规格文件 v2.0
专注于兼容性和可靠性
自动生成于: {Path(__file__).name}
生成时间: {Path(__file__).stat().st_mtime}
"""

import os
import sys
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path("{PROJECT_ROOT}")
PACKAGING_DIR = Path("{PACKAGING_DIR}")

# 分析主脚本
a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[
        str(PROJECT_ROOT),
        str(PROJECT_ROOT / "gui"),
        str(PROJECT_ROOT / "logger"),
    ],
    binaries=[],
    datas=[
        # 数据文件
{chr(10).join(f'        {str(data_file)},' for data_file in all_data_files) if all_data_files else '        # 无数据文件'}
    ],
    hiddenimports=[
        # 隐藏导入
{chr(10).join(f'        "{import_name}",' for import_name in hidden_imports)}
    ],
    hookspath=[],
    hooksconfig={{
        # PySide6特定钩子配置
        "PySide6": {{
            "use-dependency-manifest": True,
            "collect-submodules": True,
            "collect-data": True,
        }}
    }},
    runtime_hooks=[
        # 运行时钩子，确保正确初始化
    ],
    excludes=[
        # 排除不需要的模块以减小大小
        "tkinter",
        "matplotlib",
        "scipy",
        "pandas",
        "notebook",
        "jupyter",
        "IPython",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 处理PYZ文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建可执行文件（单文件模式，确保最大兼容性）
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,     # 包含所有二进制文件
    a.zipfiles,      # 包含所有压缩文件
    a.datas,         # 包含所有数据文件
    [],
    name="NetEaseMusicDesktop",
    debug=False,     # 不包含调试信息
    bootloader_ignore_signals=False,
    strip=False,     # 不剥离符号（有助于调试）
    upx=True,        # 使用UPX压缩
    console=False,   # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Linux特定配置
    icon=None,       # 图标通过代码内部设置
    # 确保包含所有必要的库
    exclude_binaries=False,
)

# 单文件模式 - 不使用COLLECT，直接使用EXE
# 所有的datas和binaries都包含在EXE中，确保最大的兼容性
'''

    # 写入规格文件
    spec_file = PACKAGING_DIR / "netease_music.spec"
    
    # 备份现有文件
    if spec_file.exists():
        backup_file = spec_file.with_suffix('.spec.bak')
        spec_file.rename(backup_file)
        print(f"✓ 已备份现有规格文件: {backup_file}")
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ PyInstaller规格文件已生成: {spec_file}")
    print(f"✓ 隐藏导入数量: {len(hidden_imports)}")
    print(f"✓ 数据文件数量: {len(all_data_files)}")
    
    return spec_file


def validate_environment():
    """验证打包环境"""
    
    print("=== 验证打包环境 ===")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}")
        return False
    else:
        print(f"✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查关键模块
    critical_modules = ["PySide6", "PyInstaller"]
    for module in critical_modules:
        try:
            __import__(module)
            print(f"✓ {module} 已安装")
        except ImportError:
            print(f"❌ {module} 未安装")
            return False
    
    # 检查项目结构
    critical_paths = [
        PROJECT_ROOT / "main.py",
        PROJECT_ROOT / "gui",
        PROJECT_ROOT / "logger",
        PROJECT_ROOT / "profile_manager.py",
        PROJECT_ROOT / "tray_manager.py",
    ]
    
    for path in critical_paths:
        if path.exists():
            print(f"✓ {path.relative_to(PROJECT_ROOT)}")
        else:
            print(f"❌ 缺少关键文件: {path.relative_to(PROJECT_ROOT)}")
            return False
    
    # 检查资源文件
    icon_dir = PROJECT_ROOT / "icon"
    if icon_dir.exists():
        icon_count = len(list(icon_dir.glob("*.png")))
        print(f"✓ 图标文件: {icon_count} 个")
    else:
        print("⚠️  图标目录不存在")
    
    config_dir = PROJECT_ROOT / "config"
    if config_dir.exists():
        config_count = len(list(config_dir.glob("*.py")))
        print(f"✓ 配置文件: {config_count} 个")
    else:
        print("⚠️  配置目录不存在")
    
    return True


def main():
    """主函数"""
    print("=== PyInstaller规格文件生成器 v2.0 ===")
    print("重点关注: 兼容性和可靠性")
    print()
    
    # 验证环境
    if not validate_environment():
        print("❌ 环境验证失败，无法继续")
        sys.exit(1)
    
    print()
    
    # 创建规格文件
    try:
        spec_file = create_spec_file()
        
        print()
        print("✓ 规格文件生成完成!")
        print(f"✓ 规格文件路径: {spec_file}")
        print("✓ 可以运行PyInstaller进行打包了")
        print()
        print("📋 下一步操作:")
        print("1. 运行主打包脚本: ./build_script.sh")
        print("2. 或者直接运行: pyinstaller netease_music.spec")
        
    except Exception as e:
        print(f"❌ 规格文件生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
