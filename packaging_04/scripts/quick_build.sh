#!/bin/bash
# 快速打包脚本 - 仅使用PyInstaller生成可执行文件

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目路径设置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$(dirname "$PROJECT_ROOT")"
TEMP_DIR="$PROJECT_ROOT/temp"
OUTPUT_DIR="$PROJECT_ROOT/dish"

log_info "开始快速打包..."
log_info "项目根目录: $SOURCE_DIR"

# 创建必要的目录
mkdir -p "$TEMP_DIR" "$OUTPUT_DIR"

# 检查虚拟环境
if [ ! -d "$SOURCE_DIR/.venv" ]; then
    log_error "未找到UV虚拟环境"
    exit 1
fi

# 激活虚拟环境
source "$SOURCE_DIR/.venv/bin/activate"

# 检查PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    log_info "安装PyInstaller..."
    pip install pyinstaller pyinstaller-hooks-contrib
fi

# 生成简单的PyInstaller规格文件
log_info "生成PyInstaller配置..."

cat > "$TEMP_DIR/quick_build.spec" << EOF
# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# 获取项目根目录
project_root = '$SOURCE_DIR'
icon_dir = os.path.join(project_root, 'icon')
config_dir = os.path.join(project_root, 'config')
logger_dir = os.path.join(project_root, 'logger')
gui_dir = os.path.join(project_root, 'gui')

# 数据文件配置
datas = [
    (icon_dir, 'icon'),
    (config_dir, 'config'),
    (logger_dir, 'logger'),
    (gui_dir, 'gui'),
]

# 隐藏导入
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore',
    'PySide6.QtNetwork',
    'logger',
    'logger.formatters',
    'logger.handlers',
    'gui.main_window',
    'gui.settings_dialog',
    'gui.close_confirm_dialog',
    'profile_manager',
    'tray_manager',
]

# 排除不必要的模块
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'PIL',
    'cv2',
]

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NetEaseCloudMusic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(icon_dir, 'icon_256x256.png'),
)
EOF

# 运行PyInstaller
log_info "运行PyInstaller..."
cd "$SOURCE_DIR"

pyinstaller "$TEMP_DIR/quick_build.spec" --clean --noconfirm

# 检查结果
if [ -f "dist/NetEaseCloudMusic" ]; then
    log_success "可执行文件生成成功"
    
    # 复制到输出目录
    cp dist/NetEaseCloudMusic "$OUTPUT_DIR/"
    log_success "文件已复制到: $OUTPUT_DIR/NetEaseCloudMusic"
    
    # 显示文件信息
    file_size=$(du -h "dist/NetEaseCloudMusic" | cut -f1)
    log_info "文件大小: $file_size"
    
    # 生成运行说明
    cat > "$OUTPUT_DIR/README_quick_build.txt" << EOF
网易云音乐桌面版 - 快速构建版本

运行方法:
1. 直接运行: ./NetEaseCloudMusic
2. 确保系统已安装Python 3.12.3+
3. 确保已安装PySide6相关依赖

注意: 这是快速构建版本，可能需要在目标系统上安装相应的依赖包。
EOF
    
    log_success "快速构建完成！"
    log_info "输出目录: $OUTPUT_DIR"
    
else
    log_error "构建失败，未找到可执行文件"
    exit 1
fi
