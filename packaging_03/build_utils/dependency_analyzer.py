#!/usr/bin/env python3
"""
AppImage依赖分析器
负责分析Python应用的所有依赖，包括系统库和Python包
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Set, Dict, List, Tuple
import re


class DependencyAnalyzer:
    def __init__(self, venv_path: Path, app_script: Path):
        self.venv_path = venv_path
        self.app_script = app_script
        self.analyzed_libs = set()
        self.python_packages = set()
        
    def find_python_executable(self) -> Path:
        """找到虚拟环境中的Python可执行文件"""
        python_exe = self.venv_path / "bin" / "python3"
        if not python_exe.exists():
            python_exe = self.venv_path / "bin" / "python"
        return python_exe
    
    def get_package_dependencies(self) -> Set[str]:
        """获取Python包依赖"""
        python_exe = self.find_python_executable()
        
        try:
            # 使用pip list获取所有包
            result = subprocess.run([
                python_exe, "-m", "pip", "list", "--format=freeze"
            ], capture_output=True, text=True, check=True)
            
            packages = set()
            for line in result.stdout.strip().split('\n'):
                if line:
                    package_name = line.split('==')[0].lower()
                    packages.add(package_name)
            
            self.python_packages = packages
            return packages
            
        except subprocess.CalledProcessError as e:
            print(f"警告: 无法获取Python包列表: {e}")
            return set()
    
    def analyze_binary_dependencies(self, binary_path: Path) -> Set[str]:
        """分析二进制文件的动态库依赖"""
        if not binary_path.exists():
            return set()
        
        try:
            result = subprocess.run([
                "ldd", str(binary_path)
            ], capture_output=True, text=True, check=True)
            
            dependencies = set()
            for line in result.stdout.split('\n'):
                if '=>' in line:
                    # 解析库路径
                    lib_path = line.split('=>')[1].strip().split()[0]
                    if lib_path and lib_path != 'not' and 'not found' not in lib_path:
                        dependencies.add(lib_path)
            
            return dependencies
            
        except subprocess.CalledProcessError:
            # ldd失败，可能是静态链接或非ELF文件
            return set()
    
    def get_python_library_paths(self) -> List[Path]:
        """获取Python库路径"""
        python_exe = self.find_python_executable()
        
        try:
            result = subprocess.run([
                python_exe, "-c", 
                "import sys; print(':'.join(sys.path))"
            ], capture_output=True, text=True, check=True)
            
            paths = []
            for path_str in result.stdout.strip().split(':'):
                path = Path(path_str)
                if path.exists():
                    paths.append(path)
            
            return paths
            
        except subprocess.CalledProcessError:
            return []
    
    def find_so_files(self, search_paths: List[Path]) -> Set[Path]:
        """在指定路径中查找.so文件"""
        so_files = set()
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            for so_file in search_path.rglob("*.so"):
                so_files.add(so_file)
        
        return so_files
    
    def analyze_python_dependencies(self) -> Dict[str, Set[Path]]:
        """分析Python包的文件依赖"""
        python_exe = self.find_python_executable()
        packages_files = {}
        
        try:
            # 获取所有已安装包的路径
            result = subprocess.run([
                python_exe, "-c", 
                """
import pkg_resources
import sys
for package in pkg_resources.working_set:
    if package.location:
        print(f"{package.key}:{package.location}")
"""
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    package_name, location = line.split(':', 1)
                    package_path = Path(location)
                    
                    if package_path.exists():
                        files = set()
                        # 收集包的主要文件
                        for py_file in package_path.rglob("*.py"):
                            files.add(py_file)
                        for so_file in package_path.rglob("*.so"):
                            files.add(so_file)
                        
                        packages_files[package_name] = files
            
        except subprocess.CalledProcessError:
            pass
        
        return packages_files
    
    def get_qt_libraries(self) -> Set[Path]:
        """获取Qt相关库文件"""
        qt_libs = set()
        
        # 常见的Qt库路径
        qt_paths = [
            self.venv_path / "lib",
            self.venv_path / "lib64",
            self.venv_path / "lib" / "python3.12" / "site-packages" / "PySide6",
            self.venv_path / "lib" / "python3.12" / "site-packages" / "PySide6" / "Qt6",
        ]
        
        for qt_path in qt_paths:
            if qt_path.exists():
                for lib_file in qt_path.rglob("libQt6*.so*"):
                    qt_libs.add(lib_file)
        
        return qt_libs
    
    def get_qt_plugins(self) -> Dict[str, Set[Path]]:
        """获取Qt插件"""
        plugins = {}
        
        plugin_paths = [
            self.venv_path / "lib" / "python3.12" / "site-packages" / "PySide6" / "Qt6" / "plugins",
            self.venv_path / "lib" / "qt6" / "plugins",
            self.venv_path / "share" / "qt6" / "plugins",
        ]
        
        for plugin_path in plugin_paths:
            if not plugin_path.exists():
                continue
                
            for plugin_dir in plugin_path.iterdir():
                if plugin_dir.is_dir():
                    plugin_name = plugin_dir.name
                    if plugin_name not in plugins:
                        plugins[plugin_name] = set()
                    
                    for plugin_file in plugin_dir.iterdir():
                        plugins[plugin_name].add(plugin_file)
        
        return plugins
    
    def collect_system_libraries(self) -> Set[Path]:
        """收集必需的系统库"""
        system_libs = set()
        
        # 首先分析主Python解释器
        python_exe = self.find_python_executable()
        python_deps = self.analyze_binary_dependencies(python_exe)
        
        for lib_path in python_deps:
            if lib_path.startswith('/usr/'):
                system_libs.add(Path(lib_path))
        
        # 然后分析关键Python包的库
        critical_packages = ['PySide6', 'numpy', 'PIL']
        python_paths = self.get_python_library_paths()
        
        for package in critical_packages:
            package_found = False
            for py_path in python_paths:
                package_path = py_path / package
                if package_path.exists():
                    for so_file in package_path.rglob("*.so"):
                        so_deps = self.analyze_binary_dependencies(so_file)
                        for dep_path in so_deps:
                            if dep_path.startswith('/usr/') and Path(dep_path).exists():
                                system_libs.add(Path(dep_path))
                    package_found = True
                    break
            if package_found:
                break
        
        return system_libs
    
    def get_all_dependencies(self) -> Dict:
        """获取所有依赖信息"""
        return {
            'python_packages': self.get_package_dependencies(),
            'python_files': self.analyze_python_dependencies(),
            'qt_libraries': self.get_qt_libraries(),
            'qt_plugins': self.get_qt_plugins(),
            'system_libraries': self.collect_system_libraries(),
            'python_paths': self.get_python_library_paths(),
        }
    
    def print_dependency_summary(self):
        """打印依赖摘要"""
        deps = self.get_all_dependencies()
        
        print("=== 依赖分析结果 ===")
        print(f"Python包数量: {len(deps['python_packages'])}")
        print(f"Qt库数量: {len(deps['qt_libraries'])}")
        print(f"Qt插件类型: {len(deps['qt_plugins'])}")
        print(f"系统库数量: {len(deps['system_libraries'])}")
        
        total_files = sum(len(files) for files in deps['python_files'].values())
        print(f"Python文件总数: {total_files}")
        
        print("\n主要Python包:")
        for package in sorted(deps['python_packages'])[:10]:
            print(f"  - {package}")
        
        print("\nQt插件:")
        for plugin_name in sorted(deps['qt_plugins'].keys()):
            print(f"  - {plugin_name}: {len(deps['qt_plugins'][plugin_name])} 个文件")


def main():
    """测试函数"""
    venv_path = Path("../../.venv")
    app_script = Path("../../main.py")
    
    analyzer = DependencyAnalyzer(venv_path, app_script)
    analyzer.print_dependency_summary()


if __name__ == "__main__":
    main()
