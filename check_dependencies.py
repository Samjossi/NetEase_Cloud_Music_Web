#!/usr/bin/env python3
"""
网易云音乐桌面版 - 依赖检查脚本
检查构建AppImage所需的所有依赖
"""

import subprocess
import sys
import shutil
from pathlib import Path


def check_python_packages():
    """检查Python包依赖"""
    print("=== Python包依赖检查 ===")
    
    required_packages = [
        "pyside6",
        "pyinstaller", 
        "appimage-builder",
        "pyinstaller-hooks-contrib",
    ]
    
    missing_packages = []
    
    # 使用subprocess检查包是否安装
    try:
        result = subprocess.run([
            "uv", "pip", "list"
        ], capture_output=True, text=True, check=True)
        
        installed_packages = result.stdout.lower()
        
        for package in required_packages:
            if package.replace('-', '_') in installed_packages or package in installed_packages:
                print(f"✓ {package}")
            else:
                print(f"❌ {package} (未安装)")
                missing_packages.append(package)
                
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 回退到导入检查
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"✓ {package}")
            except ImportError:
                print(f"❌ {package} (未安装)")
                missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages


def check_system_tools():
    """检查系统工具"""
    print("\n=== 系统工具检查 ===")
    
    # 必需工具
    required_tools = ["python3", "ldd", "cp", "find"]
    
    # 可选但推荐的工具
    optional_tools = ["patchelf", "appimagetool", "strip"]
    
    missing_required = []
    missing_optional = []
    
    for tool in required_tools:
        if shutil.which(tool):
            print(f"✓ {tool} (必需)")
        else:
            print(f"❌ {tool} (必需，未安装)")
            missing_required.append(tool)
    
    for tool in optional_tools:
        if shutil.which(tool):
            print(f"✓ {tool} (可选)")
        else:
            print(f"⚠️  {tool} (可选，未安装)")
            missing_optional.append(tool)
    
    return len(missing_required) == 0, missing_required, missing_optional


def check_project_structure():
    """检查项目结构"""
    print("\n=== 项目结构检查 ===")
    
    project_root = Path.cwd()
    required_files = [
        "main.py",
        ".venv",
        "icon/",
        "config/",
        "pyproject.toml",
        "requirements.txt",
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} (不存在)")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files


def generate_install_instructions(missing_required, missing_optional):
    """生成安装说明"""
    if not missing_required and not missing_optional:
        return
    
    print("\n=== 安装说明 ===")
    
    if missing_required:
        print("\n🔧 安装必需的系统工具:")
        if "patchelf" in missing_required:
            print("  # Ubuntu/Debian:")
            print("  sudo apt-get install patchelf")
            print("  # CentOS/RHEL:")
            print("  sudo yum install patchelf")
    
    if missing_optional:
        print("\n📦 安装可选工具 (推荐):")
        if "appimagetool" in missing_optional:
            print("  # 下载appimagetool:")
            print("  wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage")
            print("  chmod +x appimagetool-x86_64.AppImage")
            print("  sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool")
        
        if "strip" in missing_optional:
            print("  # Ubuntu/Debian:")
            print("  sudo apt-get install binutils")
            print("  # CentOS/RHEL:")
            print("  sudo yum install binutils")


def main():
    """主函数"""
    print("网易云音乐桌面版 - 依赖检查工具")
    print("=" * 50)
    
    # 检查Python包
    packages_ok, missing_packages = check_python_packages()
    
    # 检查系统工具
    tools_ok, missing_required, missing_optional = check_system_tools()
    
    # 检查项目结构
    structure_ok, missing_files = check_project_structure()
    
    # 生成安装说明
    generate_install_instructions(missing_required, missing_optional)
    
    # 总结
    print("\n" + "=" * 50)
    print("检查结果总结:")
    
    if packages_ok and tools_ok and structure_ok:
        print("🎉 所有依赖检查通过！可以开始构建AppImage。")
        return 0
    else:
        print("⚠️  发现以下问题:")
        
        if missing_packages:
            print(f"  - 缺少Python包: {', '.join(missing_packages)}")
            print("    解决方案: uv pip install -r requirements.txt")
        
        if missing_required:
            print(f"  - 缺少必需工具: {', '.join(missing_required)}")
        
        if missing_files:
            print(f"  - 缺少项目文件: {', '.join(missing_files)}")
        
        if missing_optional:
            print(f"  - 缺少可选工具: {', '.join(missing_optional)}")
            print("    (这些工具不是必需的，但建议安装以获得更好的构建结果)")
        
        print("\n请解决上述问题后重新运行检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
