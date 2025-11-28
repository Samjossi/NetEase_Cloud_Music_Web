#!/usr/bin/env python3
"""
AppImage AppDir构建器
负责创建标准的AppImage目录结构
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Set, Optional
import subprocess


class AppDirCreator:
    def __init__(self, appdir_path: Path):
        self.appdir_path = appdir_path
        self.app_name = "NetEaseMusicDesktop"
        
    def create_directory_structure(self):
        """创建标准的AppDir目录结构"""
        directories = [
            self.appdir_path,
            self.appdir_path / "usr" / "bin",
            self.appdir_path / "usr" / "lib",
            self.appdir_path / "usr" / "lib64",
            self.appdir_path / "usr" / "share" / "applications",
            self.appdir_path / "usr" / "share" / "icons",
            self.appdir_path / "usr" / "share" / "metainfo",
            self.appdir_path / "plugins",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ AppDir目录结构已创建: {self.appdir_path}")
    
    def copy_python_interpreter(self, python_exe: Path) -> Path:
        """复制Python解释器到AppDir"""
        target_bin = self.appdir_path / "usr" / "bin" / "python3"
        
        if python_exe.exists():
            shutil.copy2(python_exe, target_bin)
            target_bin.chmod(0o755)
            print(f"✓ Python解释器已复制: {target_bin}")
            return target_bin
        else:
            raise FileNotFoundError(f"Python解释器不存在: {python_exe}")
    
    def copy_application_script(self, app_script: Path) -> Path:
        """复制应用主脚本"""
        target_script = self.appdir_path / "usr" / "bin" / self.app_name
        
        # 创建主脚本的包装器
        script_content = f'''#!/usr/bin/env python3
"""
网易云音乐桌面版 - AppImage启动包装器
"""

import sys
import os
from pathlib import Path

# 设置应用根目录
APPDIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(APPDIR / "usr" / "lib" / "python3.12" / "site-packages"))

# 设置环境变量
os.environ['PYTHONPATH'] = str(APPDIR / "usr" / "lib" / "python3.12" / "site-packages")
os.environ['QT_PLUGIN_PATH'] = str(APPDIR / "plugins")
os.environ['LD_LIBRARY_PATH'] = str(APPDIR / "usr" / "lib") + ':' + str(APPDIR / "usr" / "lib64")

# 导入并运行主应用
sys.path.insert(0, str(APPDIR.parent.parent))
exec(open(str(APPDIR.parent.parent / "{app_script.name}")).read())
'''
        
        with open(target_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        target_script.chmod(0o755)
        print(f"✓ 应用脚本已创建: {target_script}")
        return target_script
    
    def copy_python_packages(self, package_files: Dict[str, Set[Path]]):
        """复制Python包文件"""
        target_lib = self.appdir_path / "usr" / "lib" / "python3.12" / "site-packages"
        
        total_files = 0
        for package_name, files in package_files.items():
            if not files:
                continue
                
            for file_path in files:
                if file_path.exists():
                    # 计算相对路径
                    relative_path = file_path.relative_to(file_path.parts[0])  # 去掉第一个路径部分
                    target_path = target_lib / relative_path
                    
                    # 确保目标目录存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(file_path, target_path)
                    total_files += 1
        
        print(f"✓ Python包已复制: {total_files} 个文件")
    
    def copy_qt_libraries(self, qt_libs: Set[Path]):
        """复制Qt库文件"""
        target_lib = self.appdir_path / "usr" / "lib"
        target_lib64 = self.appdir_path / "usr" / "lib64"
        
        copied_count = 0
        for lib_file in qt_libs:
            if lib_file.exists():
                # 根据库文件名决定目标位置
                if lib_file.name.endswith('.so') or 'lib64' in str(lib_file):
                    target_path = target_lib64 / lib_file.name
                else:
                    target_path = target_lib / lib_file.name
                
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(lib_file, target_path)
                copied_count += 1
        
        print(f"✓ Qt库已复制: {copied_count} 个文件")
    
    def copy_qt_plugins(self, qt_plugins: Dict[str, Set[Path]]):
        """复制Qt插件"""
        target_plugins = self.appdir_path / "plugins"
        
        total_plugins = 0
        for plugin_name, plugin_files in qt_plugins.items():
            if not plugin_files:
                continue
                
            plugin_target = target_plugins / plugin_name
            plugin_target.mkdir(parents=True, exist_ok=True)
            
            for plugin_file in plugin_files:
                if plugin_file.exists():
                    shutil.copy2(plugin_file, plugin_target / plugin_file.name)
                    total_plugins += 1
        
        print(f"✓ Qt插件已复制: {total_plugins} 个文件")
    
    def copy_system_libraries(self, system_libs: Set[Path]):
        """复制系统库文件"""
        target_lib = self.appdir_path / "usr" / "lib"
        target_lib64 = self.appdir_path / "usr" / "lib64"
        
        copied_count = 0
        for lib_file in system_libs:
            if lib_file.exists():
                # 智能判断目标目录
                if 'lib64' in str(lib_file) or lib_file.stat().st_size > 10*1024*1024:  # 大文件放在lib64
                    target_path = target_lib64 / lib_file.name
                else:
                    target_path = target_lib / lib_file.name
                
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(lib_file, target_path)
                copied_count += 1
        
        print(f"✓ 系统库已复制: {copied_count} 个文件")
    
    def copy_application_resources(self, project_root: Path):
        """复制应用资源文件"""
        # 复制图标文件
        icon_dir = project_root / "icon"
        target_icon_dir = self.appdir_path / "usr" / "share" / "icons"
        
        if icon_dir.exists():
            for icon_file in icon_dir.glob("*.png"):
                shutil.copy2(icon_file, target_icon_dir / icon_file.name)
        
        # 复制配置文件
        config_dir = project_root / "config"
        target_config_dir = self.appdir_path / "usr" / "share" / "config"
        
        if config_dir.exists():
            shutil.copytree(config_dir, target_config_dir, dirs_exist_ok=True)
        
        print(f"✓ 应用资源已复制")
    
    def create_desktop_file(self, icon_path: Optional[Path] = None):
        """创建.desktop文件"""
        desktop_content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=网易云音乐桌面版
Name[en]=NetEase Music Desktop
Comment=网易云音乐的桌面客户端
Comment[en]=Desktop client for NetEase Cloud Music
Exec={self.app_name}
Icon={icon_path.name if icon_path else self.app_name}
Terminal=false
Categories=AudioVideo;Audio;Player;
StartupWMClass=NetEaseMusicDesktop
'''
        
        desktop_file = self.appdir_path / f"{self.app_name}.desktop"
        with open(desktop_file, 'w', encoding='utf-8') as f:
            f.write(desktop_content)
        
        # 复制到标准位置
        desktop_target = self.appdir_path / "usr" / "share" / "applications" / f"{self.app_name}.desktop"
        shutil.copy2(desktop_file, desktop_target)
        
        print(f"✓ Desktop文件已创建: {desktop_file}")
        return desktop_file
    
    def create_apprun_script(self):
        """创建AppRun启动脚本"""
        app_run_content = '''#!/bin/bash
# AppImage启动脚本
# 确保在AppImage环境中正确运行

# 获取AppImage信息
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export APPDIR="${HERE}"

# 设置库路径
export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${APPDIR}/usr/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# 设置Python路径
export PYTHONPATH="${APPDIR}/usr/lib/python3.12/site-packages${PYTHONPATH:+:$PYTHONPATH}"

# 设置Qt环境
export QT_PLUGIN_PATH="${APPDIR}/plugins"
export QT_QPA_PLATFORM=xcb
export QT_AUTO_SCREEN_SCALE_FACTOR=1

# 确保可以找到Python
export PATH="${APPDIR}/usr/bin:${PATH}"

# 切换到AppDir
cd "${APPDIR}"

# 启动应用
exec "${APPDIR}/usr/bin/NetEaseMusicDesktop" "$@"
'''
        
        app_run_file = self.appdir_path / "AppRun"
        with open(app_run_file, 'w', encoding='utf-8') as f:
            f.write(app_run_content)
        
        app_run_file.chmod(0o755)
        print(f"✓ AppRun脚本已创建: {app_run_file}")
        return app_run_file
    
    def create_dir_icon(self, icon_path: Optional[Path] = None):
        """创建.DirIcon文件"""
        if icon_path and icon_path.exists():
            dir_icon = self.appdir_path / ".DirIcon"
            shutil.copy2(icon_path, dir_icon)
            print(f"✓ .DirIcon已创建: {dir_icon}")
    
    def fix_library_paths(self):
        """修复库文件的RPATH"""
        # 这个方法会在后面用library_manager实现
        pass
    
    def get_appdir_size(self) -> str:
        """获取AppDir大小"""
        if not self.appdir_path.exists():
            return "0B"
        
        total_size = 0
        for file_path in self.appdir_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        # 转换为人类可读格式
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024:
                return f"{total_size:.1f}{unit}"
            total_size /= 1024
        
        return f"{total_size:.1f}TB"


def main():
    """测试函数"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        appdir_path = Path(temp_dir) / "NetEaseMusicDesktop.AppDir"
        creator = AppDirCreator(appdir_path)
        
        creator.create_directory_structure()
        print(f"AppDir大小: {creator.get_appdir_size()}")


if __name__ == "__main__":
    main()
