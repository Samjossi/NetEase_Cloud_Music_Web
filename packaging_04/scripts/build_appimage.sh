#!/bin/bash
# 网易云音乐桌面版 - AppImage打包脚本
# 使用系统Python，打包UV虚拟环境中的依赖包

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$BUILD_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$BUILD_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$BUILD_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$BUILD_LOG"
}

# 项目路径设置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGING_DIR="$PROJECT_ROOT"
SOURCE_DIR="$(dirname "$PACKAGING_DIR")"
BUILD_LOG="$PACKAGING_DIR/build_logs/build_$(date +%Y%m%d_%H%M%S).log"
TEMP_DIR="$PACKAGING_DIR/temp"
OUTPUT_DIR="$PACKAGING_DIR/dish"

log_info "开始网易云音乐桌面版AppImage打包"
log_info "项目根目录: $SOURCE_DIR"
log_info "打包目录: $PACKAGING_DIR"
log_info "日志文件: $BUILD_LOG"

# 创建必要的目录
mkdir -p "$TEMP_DIR" "$OUTPUT_DIR" "$(dirname "$BUILD_LOG")"

# 检查系统Python版本
check_system_python() {
    log_info "检查系统Python版本..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "系统未安装Python3"
        exit 1
    fi
    
    SYSTEM_PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    log_info "系统Python版本: $SYSTEM_PYTHON_VERSION"
    
    # 检查是否为3.12.3或更高版本
    python3 -c "import sys; exit(0 if sys.version_info >= (3, 12, 3) else 1)" || {
        log_error "系统Python版本过低，需要3.12.3或更高版本"
        exit 1
    }
    
    log_success "系统Python版本检查通过"
}

# 检查UV虚拟环境
check_uv_venv() {
    log_info "检查UV虚拟环境..."
    
    if [ ! -d "$SOURCE_DIR/.venv" ]; then
        log_error "未找到UV虚拟环境: $SOURCE_DIR/.venv"
        exit 1
    fi
    
    VENV_PYTHON_VERSION=$("$SOURCE_DIR/.venv/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    log_info "虚拟环境Python版本: $VENV_PYTHON_VERSION"
    
    if [ "$SYSTEM_PYTHON_VERSION" != "$VENV_PYTHON_VERSION" ]; then
        log_warning "系统Python与虚拟环境Python版本不一致"
        log_warning "系统: $SYSTEM_PYTHON_VERSION, 虚拟环境: $VENV_PYTHON_VERSION"
    fi
    
    log_success "UV虚拟环境检查通过"
}

# 安装构建依赖
install_build_deps() {
    log_info "安装构建依赖..."
    
    # 激活UV虚拟环境
    source "$SOURCE_DIR/.venv/bin/activate"
    
    # 使用UV的包管理器安装依赖
    log_info "使用UV安装构建依赖..."
    uv pip install --upgrade pyinstaller appimage-builder pyinstaller-hooks-contrib
    
    log_success "构建依赖安装完成"
}

# 生成PyInstaller规格文件
generate_pyinstaller_spec() {
    log_info "生成PyInstaller规格文件..."
    
    cat > "$TEMP_DIR/NetEaseMusic.spec" << 'EOF'
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PySide6.QtCore import QCoreApplication

# 获取项目根目录
project_root = "/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web"
icon_dir = os.path.join(project_root, 'icon')
config_dir = os.path.join(project_root, 'config')
logger_dir = os.path.join(project_root, 'logger')
gui_dir = os.path.join(project_root, 'gui')

# 数据文件配置
datas = [
    (icon_dir, 'icon'),
    (config_dir, 'config'),
    (logger_dir, 'logger'),
    (os.path.join(project_root, 'gui'), 'gui'),
]

# 隐藏导入（PySide6相关）
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
    name='NetEaseMusicDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(icon_dir, 'icon_256x256.png'),
)
EOF

    log_success "PyInstaller规格文件生成完成: $TEMP_DIR/NetEaseMusic.spec"
}

# 使用PyInstaller打包
run_pyinstaller() {
    log_info "使用PyInstaller打包应用..."
    
    source "$SOURCE_DIR/.venv/bin/activate"
    
    # 在项目根目录运行PyInstaller，但使用临时目录的spec文件
    cd "$SOURCE_DIR"
    pyinstaller "$TEMP_DIR/NetEaseMusic.spec" --clean --noconfirm
    
    log_success "PyInstaller打包完成"
}

# 生成AppImage配置文件
generate_appimage_recipe() {
    log_info "生成AppImage配置文件..."
    
    cat > "$TEMP_DIR/appimage.yml" << EOF
version: 1

AppDir:
  path: ./NetEaseCloudMusic.AppDir
  app_info:
    id: netease-music-desktop
    name: 网易云音乐桌面版
    icon: netease-music-desktop
    version: 0.1.0
    exec: usr/bin/NetEaseCloudMusic
    exec_args: \$@
  runtime:
    env:
      PYTHONPATH: \$APPDIR/usr/lib/python3.12/site-packages:\$APPDIR/usr/lib/python3.12
      QT_QPA_PLATFORM_PLUGIN_PATH: \$APPDIR/usr/plugins/platforms
      QT_PLUGIN_PATH: \$APPDIR/usr/plugins
  files:
    include:
    - ./NetEaseCloudMusic/
    exclude:
    - __pycache__
    - '*.pyc'
    - '*.pyo'

AppImage:
  arch: x86_64
  update-information: None
EOF

    log_success "AppImage配置文件生成完成: $TEMP_DIR/appimage.yml"
}

# 构建AppImage
build_appimage() {
    log_info "构建AppImage..."
    
    source "$SOURCE_DIR/.venv/bin/activate"
    cd "$TEMP_DIR"
    
    # 清理之前的AppDir
    rm -rf NetEaseMusicDesktop.AppDir
    
    # 创建AppDir目录结构
    mkdir -p NetEaseMusicDesktop.AppDir
    
    # 复制PyInstaller输出的可执行文件到AppDir
    cp "$SOURCE_DIR/dist/NetEaseMusicDesktop" NetEaseMusicDesktop.AppDir/
    
    # 创建桌面文件
    cat > NetEaseMusicDesktop.AppDir/netease-music-desktop.desktop << EOF
[Desktop Entry]
Type=Application
Name=网易云音乐桌面版
Name[en]=NetEase Cloud Music Desktop
Comment=基于PySide6的网易云音乐桌面播放器
Comment[en]=NetEase Cloud Music Desktop Player
Exec=NetEaseMusicDesktop
Icon=netease-music-desktop
Categories=AudioVideo;Audio;Player;
StartupNotify=true
StartupWMClass=netease-music-desktop
EOF

    # 复制图标
    cp "$SOURCE_DIR/icon/icon_256x256.png" NetEaseMusicDesktop.AppDir/netease-music-desktop.png
    
    # 创建AppRun脚本
    cat > NetEaseMusicDesktop.AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"

# 设置基本环境变量
export LD_LIBRARY_PATH="${HERE}:${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="${HERE}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}"

# 添加调试信息
echo "AppImage启动调试信息:"
echo "HERE: $HERE"
echo "可执行文件: ${HERE}/NetEaseMusicDesktop"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "QT_PLUGIN_PATH: $QT_PLUGIN_PATH"

# 检查可执行文件是否存在
if [ ! -f "${HERE}/NetEaseMusicDesktop" ]; then
    echo "错误：找不到可执行文件 ${HERE}/NetEaseMusicDesktop"
    ls -la "${HERE}/"
    exit 1
fi

# 直接执行PyInstaller打包的单个可执行文件
exec "${HERE}/NetEaseMusicDesktop" "$@"
EOF
    chmod +x NetEaseMusicDesktop.AppDir/AppRun
    
        # 使用传统方法构建AppImage
    log_info "使用传统方法构建AppImage..."
    
    # 下载appimagetool如果不存在
    if [ ! -f "appimagetool-x86_64.AppImage" ]; then
        log_info "下载appimagetool..."
        wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
        chmod +x appimagetool-x86_64.AppImage
    fi
    
    # 创建AppImage
    ./appimagetool-x86_64.AppImage NetEaseMusicDesktop.AppDir
    
    log_success "AppImage构建完成"
}

# 复制结果到输出目录
copy_results() {
    log_info "复制打包结果到输出目录..."
    
    cd "$TEMP_DIR"
    
    # 找到生成的AppImage文件，排除appimagetool本身
    APPIMAGE_FILE=$(find . -name "*.AppImage" -type f ! -name "appimagetool*" | head -1)
    
    if [ -n "$APPIMAGE_FILE" ]; then
        cp "$APPIMAGE_FILE" "$OUTPUT_DIR/"
        APPIMAGE_NAME=$(basename "$APPIMAGE_FILE")
        log_success "AppImage已复制到: $OUTPUT_DIR/$APPIMAGE_NAME"
        
        # 生成构建报告
        generate_build_report "$APPIMAGE_NAME" "$APPIMAGE_FILE"
    else
        log_error "未找到生成的AppImage文件"
        exit 1
    fi
}

# 生成构建报告
generate_build_report() {
    local appimage_name="$1"
    local appimage_path="$2"
    
    log_info "生成构建报告..."
    
    cat > "$OUTPUT_DIR/build_report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>网易云音乐桌面版 - 构建报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>网易云音乐桌面版 - AppImage构建报告</h1>
        <p>构建时间: $(date)</p>
        <p>构建状态: <span class="success">成功</span></p>
    </div>
    
    <div class="section">
        <h2>系统信息</h2>
        <table>
            <tr><th>项目</th><th>值</th></tr>
            <tr><td>系统Python版本</td><td>$SYSTEM_PYTHON_VERSION</td></tr>
            <tr><td>虚拟环境Python版本</td><td>$VENV_PYTHON_VERSION</td></tr>
            <tr><td>项目根目录</td><td>$SOURCE_DIR</td></tr>
            <tr><td>输出文件</td><td>$appimage_name</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>文件信息</h2>
        <table>
            <tr><th>属性</th><th>值</th></tr>
            <tr><td>文件大小</td><td>$(du -h "$appimage_path" | cut -f1)</td></tr>
            <tr><td>文件路径</td><td>$OUTPUT_DIR/$appimage_name</td></tr>
            <tr><td>文件权限</td><td>$(ls -la "$appimage_path" | awk '{print $1}')</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>运行要求</h2>
        <ul>
            <li>Python 3.12.3 或更高版本</li>
            <li>Linux x86_64 架构</li>
            <li>GTK+ 3.0 或更高版本（用于系统集成）</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>使用说明</h2>
        <ol>
            <li>给AppImage添加执行权限: <code>chmod +x $appimage_name</code></li>
            <li>直接运行: <code>./$appimage_name</code></li>
            <li>或双击文件运行</li>
        </ol>
    </div>
</body>
</html>
EOF

    log_success "构建报告已生成: $OUTPUT_DIR/build_report.html"
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    rm -rf "$TEMP_DIR"/*
    log_success "临时文件清理完成"
}

# 主函数
main() {
    local start_time=$(date +%s)
    
    log_info "=== 开始打包过程 ==="
    
    check_system_python
    check_uv_venv
    install_build_deps
    generate_pyinstaller_spec
    run_pyinstaller
    generate_appimage_recipe
    build_appimage
    copy_results
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "=== 打包完成 ==="
    log_success "总耗时: ${duration}秒"
    log_success "输出目录: $OUTPUT_DIR"
    
    # 询问是否清理临时文件
    read -p "是否清理临时文件? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup
    fi
}

# 错误处理
trap 'log_error "脚本执行失败，退出码: $?"' ERR

# 执行主函数
main "$@"
