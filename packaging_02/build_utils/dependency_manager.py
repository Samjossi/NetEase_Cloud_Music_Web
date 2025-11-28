#!/usr/bin/env python3
"""
依赖管理工具 v2.0
专门用于打包时的依赖分析和验证
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
import json


class DependencyManager:
    """依赖管理器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.venv_dir = project_root / ".venv"
        self.python_exe = self.venv_dir / "bin" / "python3"
        self._installed_packages_cache = None
        
    def get_installed_packages(self) -> Dict[str, str]:
        """获取已安装的包列表（带缓存）"""
        if self._installed_packages_cache is not None:
            return self._installed_packages_cache
            
        """获取已安装的包列表"""
        try:
            # 使用 uv pip list 获取包列表
            result = subprocess.run([
                "uv", "pip", "list", "--format=json"
            ], capture_output=True, text=True, check=True)
            
            print(f"UV PIP 输出长度: {len(result.stdout)} 字符")
            print(f"UV PIP 输出前200字符: {result.stdout[:200]}")
            
            packages = json.loads(result.stdout)
            package_dict = {pkg["name"]: pkg["version"] for pkg in packages}
            
            print(f"成功解析 {len(package_dict)} 个包")
            # 检查关键包（使用小写）
            if "pyside6" in package_dict:
                print(f"✓ 找到 pyside6: {package_dict['pyside6']}")
            if "pyinstaller" in package_dict:
                print(f"✓ 找到 pyinstaller: {package_dict['pyinstaller']}")
                
            # 缓存结果
            self._installed_packages_cache = package_dict
            return package_dict
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"获取已安装包失败: {e}")
            print(f"命令输出: {getattr(e, 'stdout', '无输出')}")
            # 备用方案：使用文本解析
            try:
                result = subprocess.run([
                    "uv", "pip", "list"
                ], capture_output=True, text=True, check=True)
                
                package_dict = {}
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]
                            package_dict[name] = version
                
                print(f"备用方案解析到 {len(package_dict)} 个包")
                # 缓存结果
                self._installed_packages_cache = package_dict
                return package_dict
                
            except Exception as backup_e:
                print(f"备用方案也失败: {backup_e}")
                self._installed_packages_cache = {}
                return {}
    
    def get_project_dependencies(self) -> Dict[str, str]:
        """从项目配置文件获取依赖"""
        dependencies = {}
        
        # 从requirements.txt读取
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '==' in line:
                            name, version = line.split('==', 1)
                            dependencies[name.strip()] = version.strip()
                        else:
                            dependencies[line.strip()] = "*"
        
        # 从pyproject.toml读取
        pyproject_file = self.project_root / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomllib
                with open(pyproject_file, 'rb') as f:
                    pyproject_data = tomllib.load(f)
                
                # 读取dependencies
                project_deps = pyproject_data.get('project', {}).get('dependencies', [])
                for dep in project_deps:
                    if '==' in dep:
                        name, version = dep.split('==', 1)
                        dependencies[name.strip()] = version.strip()
                    else:
                        dependencies[dep.strip()] = "*"
                
                # 读取dev-dependencies
                dev_groups = pyproject_data.get('dependency-groups', {})
                dev_deps = dev_groups.get('dev', [])
                for dep in dev_deps:
                    if '==' in dep:
                        name, version = dep.split('==', 1)
                        dependencies[name.strip()] = version.strip()
                    else:
                        dependencies[dep.strip()] = "*"
                        
            except ImportError:
                try:
                    import toml
                    with open(pyproject_file, 'r') as f:
                        pyproject_data = toml.load(f)
                    # 处理逻辑同上
                except ImportError:
                    print("警告: 无法读取pyproject.toml，需要安装toml或tomllib")
        
        return dependencies
    
    def scan_python_imports(self) -> Set[str]:
        """扫描Python文件中的import语句"""
        imports = set()
        
        # 扫描项目根目录下的Python文件
        for py_file in self.project_root.rglob("*.py"):
            # 跳过虚拟环境和缓存目录
            if any(part in str(py_file) for part in ['.venv', '__pycache__', '.git']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 简单的import语句解析
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    
                    # import module
                    if line.startswith('import '):
                        module = line[7:].split(' as ')[0].split(',')[0].strip()
                        if module and not module.startswith('.'):
                            imports.add(module)
                    
                    # from module import ...
                    elif line.startswith('from '):
                        parts = line[5:].split(' import ')
                        if len(parts) >= 2:
                            module = parts[0].strip()
                            if module and not module.startswith('.'):
                                imports.add(module)
                                
            except Exception as e:
                print(f"扫描文件失败 {py_file}: {e}")
        
        return imports
    
    def get_pyside6_components(self) -> List[str]:
        """获取PySide6的所有组件"""
        pyside6_components = []
        
        try:
            import PySide6
            pyside6_path = Path(PySide6.__file__).parent
            
            # 扫描PySide6目录
            for item in pyside6_path.iterdir():
                if item.is_dir() and item.name.startswith('Qt'):
                    pyside6_components.append(f"PySide6.{item.name}")
                elif item.is_file() and item.suffix == '.py' and not item.name.startswith('_'):
                    pyside6_components.append(f"PySide6.{item.stem}")
                    
        except ImportError:
            pass
        
        return pyside6_components
    
    def validate_critical_dependencies(self) -> Tuple[bool, List[str]]:
        """验证关键依赖"""
        installed = self.get_installed_packages()
        missing = []
        
        # 关键依赖列表（使用小写，因为uv pip list返回小写）
        critical_deps = [
            "pyside6",
            "pyinstaller",
        ]
        
        for dep in critical_deps:
            if dep not in installed:
                missing.append(dep)
        
        return len(missing) == 0, missing
    
    def get_dependency_tree(self, package_name: str) -> Dict:
        """获取依赖树"""
        try:
            result = subprocess.run([
                "uv", "pip", "show", package_name
            ], capture_output=True, text=True, check=True)
            
            info = {}
            for line in result.stdout.split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    info[key.lower()] = value
            
            return info
            
        except subprocess.CalledProcessError:
            return {}
    
    def check_pyinstaller_compatibility(self) -> Dict[str, bool]:
        """检查PyInstaller兼容性"""
        compatibility = {}
        
        installed = self.get_installed_packages()
        
        # 检查PySide6版本兼容性（使用小写）
        if 'pyside6' in installed:
            version = installed['pyside6']
            # PySide6 6.2+ 通常有更好的PyInstaller支持
            major, minor = map(int, version.split('.')[:2])
            compatibility['pyside6_modern'] = major >= 6 and minor >= 2
        else:
            compatibility['pyside6_modern'] = False
        
        return compatibility
    
    def generate_import_map(self) -> Dict[str, List[str]]:
        """生成导入映射"""
        import_map = {}
        
        # 获取所有import语句
        imports = self.scan_python_imports()
        
        # 获取已安装的包
        installed = self.get_installed_packages()
        
        # 映射import到包名
        for imp in imports:
            possible_packages = []
            
            for pkg_name in installed.keys():
                try:
                    # 尝试导入包的顶级模块
                    module = importlib.import_module(pkg_name.lower())
                    if hasattr(module, '__file__'):
                        pkg_path = Path(module.__file__).parent
                        # 检查import是否可能来自这个包
                        if any(imp == Path(f).stem for f in pkg_path.glob("*.py")):
                            possible_packages.append(pkg_name)
                except ImportError:
                    pass
            
            if possible_packages:
                import_map[imp] = possible_packages
        
        return import_map
    
    def export_requirements(self, output_file: Path):
        """导出完整的需求文件"""
        installed = self.get_installed_packages()
        
        with open(str(output_file), 'w') as f:
            f.write("# 网易云音乐桌面版完整依赖列表\n")
            f.write("# 由dependency_manager自动生成\n")
            f.write(f"# Python版本: {sys.version}\n")
            f.write(f"# 生成时间: {Path(__file__).stat().st_mtime}\n\n")
            
            # 按字母顺序排序
            for pkg_name in sorted(installed.keys()):
                version = installed[pkg_name]
                f.write(f"{pkg_name}=={version}\n")
    
    def validate_environment(self) -> Dict[str, bool]:
        """验证打包环境"""
        results = {}
        
        # 检查虚拟环境
        results['venv_exists'] = self.venv_dir.exists()
        results['python_exists'] = self.python_exe.exists()
        
        # 检查关键依赖
        critical_ok, missing = self.validate_critical_dependencies()
        results['critical_deps'] = critical_ok
        results['missing_deps'] = missing
        
        # 检查PyInstaller兼容性
        compatibility = self.check_pyinstaller_compatibility()
        results.update(compatibility)
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="依赖管理工具")
    parser.add_argument("--project-root", type=str, default=str(Path(__file__).parent.parent.parent),
                       help="项目根目录")
    parser.add_argument("--export", type=str, help="导出依赖列表到文件")
    parser.add_argument("--validate", action="store_true", help="验证环境")
    parser.add_argument("--scan-imports", action="store_true", help="扫描import语句")
    
    args = parser.parse_args()
    
    dep_manager = DependencyManager(Path(args.project_root))
    
    if args.validate:
        print("=== 验证打包环境 ===")
        results = dep_manager.validate_environment()
        
        for key, value in results.items():
            if isinstance(value, bool):
                status = "✓" if value else "❌"
                print(f"{status} {key}: {value}")
            elif isinstance(value, list):
                status = "✓" if not value else "❌"
                print(f"{status} {key}: {value}")
        
        return 0 if all(results[k] for k in ['venv_exists', 'python_exists', 'critical_deps']) else 1
    
    if args.scan_imports:
        print("=== 扫描Import语句 ===")
        imports = dep_manager.scan_python_imports()
        print(f"发现 {len(imports)} 个唯一导入:")
        for imp in sorted(imports):
            print(f"  {imp}")
        
        import_map = dep_manager.generate_import_map()
        print(f"\n导入映射:")
        for imp, packages in import_map.items():
            print(f"  {imp} -> {packages}")
        
        return 0
    
    if args.export:
        output_path = Path(args.export)
        print(f"=== 导出依赖列表到 {output_path} ===")
        dep_manager.export_requirements(output_path)
        print("导出完成")
        return 0
    
    # 默认操作：显示基本信息
    print("=== 依赖信息 ===")
    installed = dep_manager.get_installed_packages()
    print(f"已安装包数量: {len(installed)}")
    
    project_deps = dep_manager.get_project_dependencies()
    print(f"项目依赖数量: {len(project_deps)}")
    
    critical_ok, missing = dep_manager.validate_critical_dependencies()
    print(f"关键依赖: {'✓ 完整' if critical_ok else '❌ 缺失 ' + ', '.join(missing)}")
    
    pyside6_components = dep_manager.get_pyside6_components()
    print(f"PySide6组件: {len(pyside6_components)} 个")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
