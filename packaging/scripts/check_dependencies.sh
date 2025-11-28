#!/bin/bash
# 依赖检查脚本 - 验证打包前的环境和依赖

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

log_info "开始依赖检查..."
log_info "项目根目录: $SOURCE_DIR"

# 检查计数器
check_count=0
pass_count=0
fail_count=0

# 检查函数
check() {
    local description="$1"
    local command="$2"
    local expected="$3"
    
    ((check_count++))
    echo -n "检查 $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        if [ -n "$expected" ]; then
            local result=$(eval "$command")
            if [[ "$result" == *"$expected"* ]]; then
                echo -e "${GREEN}通过${NC}"
                ((pass_count++))
                return 0
            else
                echo -e "${RED}失败${NC} (期望: $expected, 实际: $result)"
                ((fail_count++))
                return 1
            fi
        else
            echo -e "${GREEN}通过${NC}"
            ((pass_count++))
            return 0
        fi
    else
        echo -e "${RED}失败${NC}"
        ((fail_count++))
        return 1
    fi
}

# 开始检查
log_info "=== 系统环境检查 ==="

check "系统Python3" "command -v python3"
check "Python版本" "python3 -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\")'" "3.12.3"

log_info "=== UV虚拟环境检查 ==="

check "UV虚拟环境存在" "test -d '$SOURCE_DIR/.venv'"
check "虚拟环境Python" "test -f '$SOURCE_DIR/.venv/bin/python'"

if [ -f "$SOURCE_DIR/.venv/bin/python" ]; then
    VENV_PYTHON_VERSION=$("$SOURCE_DIR/.venv/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    check "虚拟环境Python版本" "echo '$VENV_PYTHON_VERSION'" "3.12.3"
fi

log_info "=== 项目文件检查 ==="

check "主程序文件" "test -f '$SOURCE_DIR/main.py'"
check "项目配置文件" "test -f '$SOURCE_DIR/pyproject.toml'"
check "图标目录" "test -d '$SOURCE_DIR/icon'"
check "配置目录" "test -d '$SOURCE_DIR/config'"
check "日志模块目录" "test -d '$SOURCE_DIR/logger'"
check "GUI模块目录" "test -d '$SOURCE_DIR/gui'"

# 检查图标文件
icon_sizes=("16x16" "24x24" "32x32" "48x48" "64x64" "128x128" "256x256")
for size in "${icon_sizes[@]}"; do
    check "图标文件 $size" "test -f '$SOURCE_DIR/icon/icon_$size.png'"
done

log_info "=== Python依赖检查 ==="

# 激活虚拟环境进行检查
if [ -d "$SOURCE_DIR/.venv" ]; then
    source "$SOURCE_DIR/.venv/bin/activate"
    
    # 核心依赖
    check "PySide6" "python -c 'import PySide6; print(PySide6.__version__)'"
    check "PySide6-QtWidgets" "python -c 'import PySide6.QtWidgets'"
    check "PySide6-QtWebEngineWidgets" "python -c 'import PySide6.QtWebEngineWidgets'"
    
    # 打包依赖
    check "PyInstaller" "python -c 'import PyInstaller; print(PyInstaller.__version__)'"
    
    # 项目模块
    check "logger模块" "python -c 'import logger'"
    check "profile_manager" "python -c 'import profile_manager'"
    check "tray_manager" "python -c 'import tray_manager'"
    check "gui模块" "python -c 'import gui'"
    check "main_window" "python -c 'import gui.main_window'"
    
    # 获取依赖版本信息
    log_info "=== 依赖版本信息 ==="
    
    if command -v pip &> /dev/null; then
        echo "核心依赖版本:"
        pip list | grep -E "(PySide6|PyInstaller|appimage-builder)" | while read line; do
            echo "  $line"
        done
    fi
fi

log_info "=== 系统库检查 ==="

check "GLib库" "pkg-config --exists glib-2.0"
check "GTK+3库" "pkg-config --exists gtk+-3.0"
check "X11库" "pkg-config --exists x11"

log_info "=== 构建工具检查 ==="

check "GCC编译器" "command -v gcc"
check "Make工具" "command -v make"
check "pkg-config" "command -v pkg-config"

# 如果有appimage-builder，检查它
if command -v appimage-builder &> /dev/null; then
    check "appimage-builder" "command -v appimage-builder"
else
    log_warning "appimage-builder未安装，将使用虚拟环境版本"
fi

# 输出检查结果
echo
echo "=== 检查结果汇总 ==="
echo "总检查项目: $check_count"
echo -e "通过项目: ${GREEN}$pass_count${NC}"
echo -e "失败项目: ${RED}$fail_count${NC}"

if [ $fail_count -eq 0 ]; then
    log_success "所有检查通过！环境准备就绪，可以开始打包。"
    
    # 生成环境报告
    report_file="$PROJECT_ROOT/build_logs/environment_report_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p "$(dirname "$report_file")"
    
    {
        echo "网易云音乐桌面版 - 环境检查报告"
        echo "检查时间: $(date)"
        echo "检查结果: 全部通过 ($pass_count/$check_count)"
        echo ""
        echo "系统信息:"
        echo "  操作系统: $(uname -s)"
        echo "  架构: $(uname -m)"
        echo "  Python版本: $(python3 --version)"
        echo "  项目路径: $SOURCE_DIR"
        echo ""
        echo "关键依赖版本:"
        if [ -d "$SOURCE_DIR/.venv" ]; then
            source "$SOURCE_DIR/.venv/bin/activate"
            pip list | grep -E "(PySide6|PyInstaller)" | while read line; do
                echo "  $line"
            done
        fi
    } > "$report_file"
    
    log_success "环境报告已保存: $report_file"
    exit 0
else
    log_error "有 $fail_count 项检查失败，请修复后再进行打包。"
    echo
    echo "建议的修复步骤:"
    echo "1. 确保系统安装了Python 3.12.3+"
    echo "2. 确保UV虚拟环境正确设置: uv venv"
    echo "3. 安装项目依赖: uv pip install -r requirements.txt"
    echo "4. 安装系统依赖: sudo apt install libgtk-3-dev libglib2.0-dev"
    exit 1
fi
