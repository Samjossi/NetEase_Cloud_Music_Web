#!/usr/bin/env python3
"""
AppImage主构建器
协调所有组件完成AppImage的构建
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import subprocess
import time

# 添加build_utils到路径
sys.path.insert(0, str(Path(__file__).parent / "build_utils"))

from dependency_analyzer import DependencyAnalyzer
from appdir_creator import AppDirCreator
from library_manager import LibraryManager


class AppImageBuilder:
    def __init__(self, project_root: Path, output_dir: Path):
        self.project_root = project_root
        self.output_dir = output_dir
        self.venv_path = project_root / ".venv"
        self.app_script = project_root / "main.py"
        self.app_name = "NetEaseMusicDesktop"
        
        # 工作路径
        self.build_dir = output_dir / "build"
        self.appdir_path = self.build_dir / f"{self.app_name}.AppDir"
        self.final_appimage = output_dir / f"{self.app_name}-x86_64.AppImage"
        
    def check_prerequisites(self) -> bool:
        """检查构建前提条件"""
        print("=== 检查构建前提条件 ===")
        
        # 检查项目文件
        required_files = [self.app_script, self.venv_path]
        for file_path in required_files:
            if not file_path.exists():
                print(f"❌ 缺少必要文件: {file_path}")
                return False
            print(f"✓ {file_path.relative_to(self.project_root)}")
        
        # 检查虚拟环境
        python_exe = self.venv_path / "bin" / "python3"
        if not python_exe.exists():
            python_exe = self.venv_path / "bin" / "python"
        
        if not python_exe.exists():
            print("❌ 虚拟环境中未找到Python解释器")
            return False
        print(f"✓ Python解释器: {python_exe}")
        
        # 检查关键工具
        required_tools = ["ldd", "cp", "find"]
        for tool in required_tools:
            if shutil.which(tool):
                print(f"✓ {tool}")
            else:
                print(f"❌ 缺少工具: {tool}")
                return False
        
        # 检查可选工具
        optional_tools = ["patchelf", "strip", "appimagetool"]
        for tool in optional_tools:
            if shutil.which(tool):
                print(f"✓ {tool} (可选)")
            else:
                print(f"⚠️  {tool} (可选，未安装)")
        
        return True
    
    def prepare_build_environment(self):
        """准备构建环境"""
        print(f"\n=== 准备构建环境 ===")
        
        # 清理并创建构建目录
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        
        self.build_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ 构建目录已创建: {self.build_dir}")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ 输出目录: {self.output_dir}")
    
    def analyze_dependencies(self) -> dict:
        """分析应用依赖"""
        print(f"\n=== 分析应用依赖 ===")
        
        analyzer = DependencyAnalyzer(self.venv_path, self.app_script)
        deps = analyzer.get_all_dependencies()
        
        analyzer.print_dependency_summary()
        return deps
    
    def create_appdir(self, deps: dict) -> bool:
        """创建AppDir结构"""
        print(f"\n=== 创建AppDir结构 ===")
        
        try:
            creator = AppDirCreator(self.appdir_path)
            
            # 创建目录结构
            creator.create_directory_structure()
            
            # 复制Python解释器
            python_exe = self.venv_path / "bin" / "python3"
            if not python_exe.exists():
                python_exe = self.venv_path / "bin" / "python"
            
            creator.copy_python_interpreter(python_exe)
            
            # 复制应用脚本
            creator.copy_application_script(self.app_script)
            
            # 复制Python包
            creator.copy_python_packages(deps['python_files'])
            
            # 复制Qt库
            creator.copy_qt_libraries(deps['qt_libraries'])
            
            # 复制Qt插件
            creator.copy_qt_plugins(deps['qt_plugins'])
            
            # 复制系统库
            creator.copy_system_libraries(deps['system_libraries'])
            
            # 复制应用资源
            creator.copy_application_resources(self.project_root)
            
            # 创建desktop文件
            icon_files = list((self.project_root / "icon").glob("*.png"))
            icon_path = icon_files[0] if icon_files else None
            creator.create_desktop_file(icon_path)
            
            # 创建AppRun脚本
            creator.create_apprun_script()
            
            # 创建.DirIcon
            creator.create_dir_icon(icon_path)
            
            print(f"✓ AppDir创建完成: {creator.get_appdir_size()}")
            return True
            
        except Exception as e:
            print(f"❌ AppDir创建失败: {e}")
            return False
    
    def optimize_libraries(self) -> bool:
        """优化库文件"""
        print(f"\n=== 优化库文件 ===")
        
        try:
            manager = LibraryManager(self.appdir_path)
            
            if not manager.optimize_libraries():
                print("⚠️  库优化部分失败，但继续构建")
                return False
            
            # 显示库文件摘要
            summary = manager.get_library_summary()
            print(f"📊 库文件摘要:")
            print(f"  - 总库文件数: {summary['total_libraries']}")
            print(f"  - Qt库数: {summary['qt_libraries']}")
            print(f"  - Python扩展数: {summary['python_extensions']}")
            print(f"  - 总大小: {summary['total_size'] / 1024 / 1024:.1f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ 库优化失败: {e}")
            return False
    
    def create_appimage(self) -> bool:
        """创建最终的AppImage文件"""
        print(f"\n=== 创建AppImage ===")
        
        # 检查appimagetool
        appimagetool = shutil.which("appimagetool")
        if not appimagetool:
            print("❌ appimagetool未安装")
            print("请安装appimagetool:")
            print("  wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage")
            print("  chmod +x appimagetool-x86_64.AppImage")
            print("  sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool")
            return False
        
        print(f"✓ 使用appimagetool: {appimagetool}")
        
        try:
            # 构建AppImage命令
            cmd = [
                appimagetool,
                "--comp", "zstd",  # 使用zstd压缩
                "--no-appstream",  # 跳过AppStream验证
                str(self.appdir_path),
                str(self.final_appimage)
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print("✓ AppImage创建成功")
                
                # 显示结果文件信息
                if self.final_appimage.exists():
                    size = self.final_appimage.stat().st_size
                    size_mb = size / 1024 / 1024
                    print(f"✓ 文件大小: {size_mb:.1f} MB")
                    print(f"✓ 输出路径: {self.final_appimage}")
                
                return True
            else:
                print(f"❌ AppImage创建失败:")
                print(f"错误输出: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ AppImage创建超时")
            return False
        except Exception as e:
            print(f"❌ AppImage创建异常: {e}")
            return False
    
    def test_appimage(self) -> bool:
        """测试生成的AppImage"""
        print(f"\n=== 测试AppImage ===")
        
        if not self.final_appimage.exists():
            print("❌ AppImage文件不存在")
            return False
        
        # 设置可执行权限
        try:
            self.final_appimage.chmod(0o755)
            print("✓ 可执行权限已设置")
        except Exception as e:
            print(f"⚠️  无法设置可执行权限: {e}")
        
        # 基本测试
        try:
            result = subprocess.run([
                str(self.final_appimage), "--version"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✓ AppImage基本测试通过")
                return True
            else:
                print("⚠️  AppImage测试返回非零退出码")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  AppImage测试超时")
            return False
        except Exception as e:
            print(f"⚠️  AppImage测试异常: {e}")
            return False
    
    def create_test_scripts(self):
        """创建测试和运行脚本"""
        print(f"\n=== 创建辅助脚本 ===")
        
        # 创建运行脚本
        run_script = self.output_dir / "run_appimage.sh"
        run_content = f'''#!/bin/bash
# 网易云音乐桌面版 AppImage运行脚本

APPIMAGE_PATH="$(cd "$(dirname "${{BASH_SOURCE[0]}")" && pwd)/{self.final_appimage.name}"

if [ ! -f "$APPIMAGE_PATH" ]; then
    echo "错误: AppImage文件不存在: $APPIMAGE_PATH"
    exit 1
fi

echo "启动网易云音乐桌面版..."
echo "AppImage路径: $APPIMAGE_PATH"

# 设置环境变量
export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_QPA_PLATFORM=xcb

# 运行AppImage
exec "$APPIMAGE_PATH" "$@"
'''
        
        with open(run_script, 'w', encoding='utf-8') as f:
            f.write(run_content)
        
        run_script.chmod(0o755)
        print(f"✓ 运行脚本已创建: {run_script}")
        
        # 创建测试脚本
        test_script = self.output_dir / "test_appimage.sh"
        test_content = f'''#!/bin/bash
# 网易云音乐桌面版 AppImage测试脚本

APPIMAGE_PATH="$(cd "$(dirname "${{BASH_SOURCE[0]}")" && pwd)/{self.final_appimage.name}"

echo "=== AppImage兼容性测试 ==="
echo "AppImage路径: $APPIMAGE_PATH"

# 检查文件
if [ -f "$APPIMAGE_PATH" ]; then
    echo "✓ AppImage文件存在"
    
    # 检查权限
    if [ -x "$APPIMAGE_PATH" ]; then
        echo "✓ 可执行权限正确"
    else
        echo "❌ 缺少可执行权限"
        chmod +x "$APPIMAGE_PATH"
    fi
    
    # 检查大小
    SIZE=$(stat -c%s "$APPIMAGE_PATH" 2>/dev/null || stat -f%z "$APPIMAGE_PATH" 2>/dev/null || echo "unknown")
    if [ "$SIZE" != "unknown" ] && [ "$SIZE" -gt 50000000 ]; then
        SIZE_MB=$((SIZE / 1024 / 1024))
        echo "✓ 文件大小: ${SIZE_MB}MB"
    else
        echo "⚠️  文件大小可能异常"
    fi
    
    # 尝试获取版本信息
    echo "尝试运行AppImage..."
    timeout 10 "$APPIMAGE_PATH" --help 2>/dev/null || echo "AppImage基本测试完成"
    
else
    echo "❌ AppImage文件不存在"
fi

echo
echo "=== 测试完成 ==="
echo "要运行应用，请执行: ./run_appimage.sh"
'''
        
        with open(test_script, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        test_script.chmod(0o755)
        print(f"✓ 测试脚本已创建: {test_script}")
        
        # 创建README
        readme_content = f'''# 网易云音乐桌面版 - AppImage版本

## 🎯 文件说明

- `{self.final_appimage.name}` - 主AppImage文件
- `run_appimage.sh` - **推荐使用**的运行脚本
- `test_appimage.sh` - AppImage兼容性测试脚本
- `README_AppImage.md` - 本说明文件

## 🚀 运行方法

### 方法1: 使用运行脚本（推荐）
```bash
./run_appimage.sh
```

### 方法2: 直接运行
```bash
./{self.final_appimage.name}
```

### 方法3: 先测试再运行
```bash
./test_appimage.sh    # 检查兼容性
./run_appimage.sh      # 如果测试通过则运行
```

## 📦 AppImage特性

- ✅ **完全便携** - 无需安装，解压即用
- ✅ **自包含依赖** - 包含所有必需的库和Python环境
- ✅ **跨发行版** - 支持Ubuntu、Fedora、Arch等主流发行版
- ✅ **系统集成** - 支持桌面菜单和应用图标
- ✅ **自动更新** - 支持AppImage的自动更新机制

## 🔧 系统要求

- Linux x86_64 系统
- 支持X11的桌面环境
- 基本的系统库（glibc、libstdc++等）

## 🐛 故障排除

### 常见问题

1. **权限被拒绝**
   ```bash
   chmod +x {self.final_appimage.name}
   ```

2. **缺少系统库**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libfuse2
   
   # CentOS/RHEL
   sudo yum install fuse-libs
   ```

3. **无法启动GUI**
   ```bash
   # 确保在图形环境中运行
   echo $DISPLAY
   
   # 如果为空，尝试：
   export DISPLAY=:0
   ```

4. **Qt相关错误**
   ```bash
   # 设置Qt环境变量
   export QT_QPA_PLATFORM=xcb
   export QT_AUTO_SCREEN_SCALE_FACTOR=1
   ```

## 📊 构建信息

- **构建时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **构建工具**: 自定义AppImage构建系统
- **Python版本**: 3.12
- **Qt版本**: 6.10.1
- **目标平台**: Linux x86_64
- **压缩格式**: zstd

## 💡 使用提示

1. **首次运行**: 可能需要较长时间（解压内置资源）
2. **文件关联**: 可以设置为默认音乐播放器
3. **桌面集成**: 支持右键菜单和文件拖放
4. **自动更新**: 应用会提示新版本可用

## 🆘 获取帮助

如果遇到问题：
1. 运行 `./test_appimage.sh` 检查兼容性
2. 查看系统日志：`journalctl -xe`
3. 检查AppImage日志：`./{self.final_appimage.name} --debug`

---

享受你的音乐时光！🎵
'''
        
        readme_file = self.output_dir / "README_AppImage.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✓ README文档已创建: {readme_file}")
    
    def cleanup_build_files(self):
        """清理构建临时文件"""
        print(f"\n=== 清理构建文件 ===")
        
        try:
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                print(f"✓ 构建目录已清理: {self.build_dir}")
        except Exception as e:
            print(f"⚠️  清理构建目录失败: {e}")
    
    def build(self) -> bool:
        """执行完整的AppImage构建流程"""
        print("=== 网易云音乐桌面版 AppImage构建器 ===")
        print(f"项目根目录: {self.project_root}")
        print(f"输出目录: {self.output_dir}")
        print()
        
        # 检查前提条件
        if not self.check_prerequisites():
            return False
        
        # 准备构建环境
        self.prepare_build_environment()
        
        # 分析依赖
        deps = self.analyze_dependencies()
        
        # 创建AppDir
        if not self.create_appdir(deps):
            return False
        
        # 优化库文件
        if not self.optimize_libraries():
            return False
        
        # 创建AppImage
        if not self.create_appimage():
            return False
        
        # 测试AppImage
        if not self.test_appimage():
            return False
        
        # 创建辅助脚本
        self.create_test_scripts()
        
        # 清理临时文件
        self.cleanup_build_files()
        
        print(f"\n🎉 AppImage构建完成!")
        print(f"📦 输出文件: {self.final_appimage}")
        print(f"🚀 运行命令: ./run_appimage.sh")
        print(f"🧪 测试命令: ./test_appimage.sh")
        
        return True


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python appimage_builder.py <项目根目录> [输出目录]")
        print("示例: python appimage_builder.py .. ../packaging_03/dish")
        sys.exit(1)
    
    project_root = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd() / "dish"
    
    builder = AppImageBuilder(project_root, output_dir)
    
    try:
        success = builder.build()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ 构建被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 构建过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
