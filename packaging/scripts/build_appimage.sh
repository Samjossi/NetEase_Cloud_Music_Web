#!/bin/bash
# 网易云音乐桌面版 - AppImage 一键打包脚本
# 用法: bash packaging/scripts/build_appimage.sh
# 流程: PyInstaller(spec 固定于 packaging/NetEaseMusic.spec) -> 组装 AppDir -> appimagetool -> packaging/dish/

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$BUILD_LOG"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1" | tee -a "$BUILD_LOG"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$BUILD_LOG"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$BUILD_LOG"; }

# ---- 路径 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGING_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$PACKAGING_DIR")"
TEMP_DIR="$PACKAGING_DIR/temp"
OUTPUT_DIR="$PACKAGING_DIR/dish"
APPDIR="$TEMP_DIR/NetEaseMusicDesktop.AppDir"
SPEC_FILE="$PACKAGING_DIR/NetEaseMusic.spec"
APPIMAGETOOL="$TEMP_DIR/appimagetool-x86_64.AppImage"
BUILD_LOG="$PACKAGING_DIR/build_logs/build_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$TEMP_DIR" "$OUTPUT_DIR" "$(dirname "$BUILD_LOG")"
log_info "项目根目录: $PROJECT_ROOT"
log_info "日志文件: $BUILD_LOG"

# ---- 1. 环境检查 ----
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
[ -x "$VENV_PYTHON" ] || { log_error "未找到虚拟环境 Python: $VENV_PYTHON"; exit 1; }
"$VENV_PYTHON" -c "import PyInstaller" 2>/dev/null || {
    log_error "虚拟环境缺少 pyinstaller，请先执行: uv pip install pyinstaller"; exit 1; }
[ -f "$SPEC_FILE" ] || { log_error "未找到 spec 文件: $SPEC_FILE"; exit 1; }
log_success "环境检查通过（$("$VENV_PYTHON" --version 2>&1)）"

# ---- 2. PyInstaller 构建 ----
log_info "PyInstaller 构建中..."
cd "$PROJECT_ROOT"
"$VENV_PYTHON" -m PyInstaller "$SPEC_FILE" --clean --noconfirm \
    --distpath "$TEMP_DIR/dist" \
    --workpath "$TEMP_DIR/build" \
    >> "$BUILD_LOG" 2>&1
[ -f "$TEMP_DIR/dist/NetEaseMusicDesktop" ] || { log_error "PyInstaller 未产出可执行文件，详见日志"; exit 1; }
log_success "PyInstaller 构建完成: $(du -h "$TEMP_DIR/dist/NetEaseMusicDesktop" | cut -f1)"

# ---- 3. 组装 AppDir ----
log_info "组装 AppDir..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR"
cp "$TEMP_DIR/dist/NetEaseMusicDesktop" "$APPDIR/"
cp "$PROJECT_ROOT/icon/icon_256x256.png" "$APPDIR/netease-music-desktop.png"

cat > "$APPDIR/netease-music-desktop.desktop" << 'EOF'
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

cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="${HERE}:${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="${HERE}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}"
exec "${HERE}/NetEaseMusicDesktop" "$@"
EOF
chmod +x "$APPDIR/AppRun"
log_success "AppDir 组装完成"

# ---- 4. 构建 AppImage ----
if [ ! -x "$APPIMAGETOOL" ]; then
    log_info "下载 appimagetool..."
    wget -q -O "$APPIMAGETOOL" \
        https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$APPIMAGETOOL"
fi

log_info "appimagetool 打包中..."
cd "$TEMP_DIR"
rm -f ./*.AppImage.bak
find . -maxdepth 1 -name "*-x86_64.AppImage" ! -name "appimagetool*" -delete
./"$(basename "$APPIMAGETOOL")" NetEaseMusicDesktop.AppDir >> "$BUILD_LOG" 2>&1
APPIMAGE_FILE=$(find . -maxdepth 1 -name "*-x86_64.AppImage" | head -1)
[ -n "$APPIMAGE_FILE" ] || { log_error "AppImage 生成失败，详见日志"; exit 1; }

cp "$APPIMAGE_FILE" "$OUTPUT_DIR/网易云音乐桌面版-x86_64.AppImage"
log_success "AppImage: $OUTPUT_DIR/网易云音乐桌面版-x86_64.AppImage ($(du -h "$OUTPUT_DIR/网易云音乐桌面版-x86_64.AppImage" | cut -f1))"

# ---- 5. 清理中间产物 ----
rm -rf "$TEMP_DIR/dist" "$TEMP_DIR/build" "$APPDIR" "$APPIMAGE_FILE"
rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist"
log_success "中间产物已清理"
log_success "=== 打包完成 ==="
