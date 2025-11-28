#!/usr/bin/env python3
"""
AppImage库管理器
负责处理库文件的路径重写和依赖修复
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Set, Optional


class LibraryManager:
    def __init__(self, appdir_path: Path):
        self.appdir_path = appdir_path
        self.usr_lib = appdir_path / "usr" / "lib"
        self.usr_lib64 = appdir_path / "usr" / "lib64"
    
    def check_patchelf_availability(self) -> bool:
        """检查patchelf是否可用"""
        try:
            subprocess.run(['patchelf', '--version'], 
                        capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_current_rpath(self, binary_path: Path) -> str:
        """获取二进制文件的当前RPATH"""
        try:
            result = subprocess.run([
                'patchelf', '--print-rpath', str(binary_path)
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
    
    def set_rpath(self, binary_path: Path, rpath: str) -> bool:
        """设置二进制文件的RPATH"""
        try:
            subprocess.run([
                'patchelf', '--set-rpath', rpath, str(binary_path)
            ], check=True, capture_output=True, timeout=30)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"警告: 无法设置 {binary_path} 的RPATH: {e}")
            return False
    
    def set_interpreter(self, binary_path: Path, interpreter: str) -> bool:
        """设置二进制文件的解释器"""
        try:
            subprocess.run([
                'patchelf', '--set-interpreter', interpreter, str(binary_path)
            ], check=True, capture_output=True, timeout=30)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"警告: 无法设置 {binary_path} 的解释器: {e}")
            return False
    
    def fix_python_interpreter(self):
        """修复Python解释器的库路径"""
        python_exe = self.appdir_path / "usr" / "bin" / "python3"
        
        if not python_exe.exists():
            return False
        
        # 设置Python解释器的RPATH
        rpath = f"$ORIGIN/../lib:$ORIGIN/../lib64"
        return self.set_rpath(python_exe, rpath)
    
    def fix_qt_libraries(self):
        """修复Qt库的RPATH"""
        qt_libs = []
        
        # 查找所有Qt库
        for lib_dir in [self.usr_lib, self.usr_lib64]:
            if lib_dir.exists():
                qt_libs.extend(lib_dir.glob("libQt6*.so*"))
        
        fixed_count = 0
        for lib_file in qt_libs:
            # 设置Qt库的RPATH
            rpath = "$ORIGIN"
            if self.set_rpath(lib_file, rpath):
                fixed_count += 1
        
        print(f"✓ Qt库RPATH已修复: {fixed_count} 个文件")
        return fixed_count > 0
    
    def fix_python_extensions(self):
        """修复Python扩展模块的RPATH"""
        python_extensions = []
        
        # 查找Python扩展
        site_packages = self.appdir_path / "usr" / "lib" / "python3.12" / "site-packages"
        if site_packages.exists():
            for ext_file in site_packages.rglob("*.so"):
                python_extensions.append(ext_file)
        
        fixed_count = 0
        for ext_file in python_extensions:
            # 设置扩展模块的RPATH
            rpath = "$ORIGIN/../../../..:$ORIGIN/../../../lib64"
            if self.set_rpath(ext_file, rpath):
                fixed_count += 1
        
        print(f"✓ Python扩展RPATH已修复: {fixed_count} 个文件")
        return fixed_count > 0
    
    def fix_library_dependencies(self):
        """修复库文件的依赖关系"""
        all_libs = []
        
        # 收集所有库文件
        for lib_dir in [self.usr_lib, self.usr_lib64]:
            if lib_dir.exists():
                all_libs.extend(lib_dir.glob("*.so*"))
        
        fixed_count = 0
        for lib_file in all_libs:
            # 分析库的依赖
            try:
                result = subprocess.run([
                    'ldd', str(lib_file)
                ], capture_output=True, text=True, check=True)
                
                # 检查是否有未找到的依赖
                if 'not found' in result.stdout:
                    # 设置相对RPATH来帮助找到依赖
                    rpath = "$ORIGIN"
                    if self.set_rpath(lib_file, rpath):
                        fixed_count += 1
                        
            except subprocess.CalledProcessError:
                continue
        
        print(f"✓ 库依赖已修复: {fixed_count} 个文件")
        return fixed_count > 0
    
    def create_symlinks(self):
        """创建必要的符号链接"""
        symlinks = []
        
        # lib64到lib的符号链接
        if self.usr_lib64.exists() and not (self.usr_lib64 / "lib").exists():
            target = self.usr_lib64 / "lib"
            source = Path("../lib")
            try:
                target.symlink_to(source)
                symlinks.append(str(target))
            except OSError:
                pass
        
        # 创建常见的库符号链接
        common_libs = [
            ("libQt6Core.so.6", "libQt6Core.so"),
            ("libQt6Gui.so.6", "libQt6Gui.so"),
            ("libQt6Widgets.so.6", "libQt6Widgets.so"),
            ("libQt6WebEngineWidgets.so.6", "libQt6WebEngineWidgets.so"),
        ]
        
        for lib_dir in [self.usr_lib, self.usr_lib64]:
            if not lib_dir.exists():
                continue
                
            for source_name, target_name in common_libs:
                source = lib_dir / source_name
                target = lib_dir / target_name
                
                if source.exists() and not target.exists():
                    try:
                        target.symlink_to(source_name)
                        symlinks.append(str(target))
                    except OSError:
                        pass
        
        if symlinks:
            print(f"✓ 符号链接已创建: {len(symlinks)} 个")
        
        return len(symlinks) > 0
    
    def strip_binaries(self, dry_run: bool = True) -> bool:
        """剥离二进制文件的调试信息（可选）"""
        if not dry_run and not shutil.which("strip"):
            print("警告: strip命令不可用，跳过二进制剥离")
            return False
        
        binaries = []
        
        # 收集所有二进制文件
        for lib_dir in [self.usr_lib, self.usr_lib64]:
            if lib_dir.exists():
                binaries.extend(lib_dir.glob("*.so*"))
        
        # 添加可执行文件
        bin_dir = self.appdir_path / "usr" / "bin"
        if bin_dir.exists():
            binaries.extend(bin_dir.glob("*"))
        
        total_size_saved = 0
        stripped_count = 0
        
        for binary in binaries:
            if not binary.is_file():
                continue
                
            try:
                original_size = binary.stat().st_size
                
                if dry_run:
                    # 只是估算可以节省的空间
                    estimated_size = original_size * 0.8  # 假设可以节省20%
                    total_size_saved += original_size - estimated_size
                    stripped_count += 1
                else:
                    # 实际执行剥离
                    subprocess.run([
                        'strip', '--strip-unneeded', str(binary)
                    ], check=True, capture_output=True, timeout=10)
                    
                    new_size = binary.stat().st_size
                    total_size_saved += original_size - new_size
                    stripped_count += 1
                    
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue
        
        if dry_run:
            print(f"📊 预计剥离后可节省: {total_size_saved / 1024 / 1024:.1f} MB ({stripped_count} 个文件)")
        else:
            print(f"✓ 二进制已剥离: 节省 {total_size_saved / 1024 / 1024:.1f} MB ({stripped_count} 个文件)")
        
        return stripped_count > 0
    
    def verify_library_integrity(self) -> bool:
        """验证库文件的完整性"""
        critical_libs = [
            "libpython3.12.so",
            "libQt6Core.so",
            "libQt6Gui.so",
            "libQt6Widgets.so",
        ]
        
        missing_libs = []
        
        for lib_name in critical_libs:
            found = False
            
            # 在lib和lib64中查找
            for lib_dir in [self.usr_lib, self.usr_lib64]:
                lib_path = lib_dir / lib_name
                if lib_path.exists():
                    found = True
                    break
            
            if not found:
                missing_libs.append(lib_name)
        
        if missing_libs:
            print(f"❌ 缺少关键库: {', '.join(missing_libs)}")
            return False
        else:
            print("✓ 所有关键库都存在")
            return True
    
    def optimize_libraries(self) -> bool:
        """优化库文件"""
        if not self.check_patchelf_availability():
            print("警告: patchelf不可用，跳过库优化")
            return False
        
        success = True
        
        # 修复Python解释器
        success &= self.fix_python_interpreter()
        
        # 修复Qt库
        success &= self.fix_qt_libraries()
        
        # 修复Python扩展
        success &= self.fix_python_extensions()
        
        # 修复库依赖
        success &= self.fix_library_dependencies()
        
        # 创建符号链接
        success &= self.create_symlinks()
        
        # 可选：剥离二进制文件（这里只做预览）
        self.strip_binaries(dry_run=True)
        
        # 验证完整性
        success &= self.verify_library_integrity()
        
        return success
    
    def get_library_summary(self) -> dict:
        """获取库文件摘要"""
        summary = {
            'total_libraries': 0,
            'total_size': 0,
            'qt_libraries': 0,
            'python_extensions': 0,
        }
        
        for lib_dir in [self.usr_lib, self.usr_lib64]:
            if not lib_dir.exists():
                continue
                
            for lib_file in lib_dir.glob("*.so*"):
                if lib_file.is_file():
                    summary['total_libraries'] += 1
                    summary['total_size'] += lib_file.stat().st_size
                    
                    if 'Qt6' in lib_file.name:
                        summary['qt_libraries'] += 1
        
        # 统计Python扩展
        site_packages = self.appdir_path / "usr" / "lib" / "python3.12" / "site-packages"
        if site_packages.exists():
            for ext_file in site_packages.rglob("*.so"):
                if ext_file.is_file():
                    summary['python_extensions'] += 1
        
        return summary


def main():
    """测试函数"""
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as temp_dir:
        appdir_path = Path(temp_dir) / "Test.AppDir"
        appdir_path.mkdir()
        
        # 创建测试目录结构
        (appdir_path / "usr" / "lib").mkdir(parents=True)
        (appdir_path / "usr" / "bin").mkdir(parents=True)
        
        manager = LibraryManager(appdir_path)
        
        print("=== 库管理器测试 ===")
        print(f"patchelf可用: {manager.check_patchelf_availability()}")
        
        summary = manager.get_library_summary()
        print(f"库文件摘要: {summary}")


if __name__ == "__main__":
    main()
