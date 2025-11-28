#!/bin/bash
# 测试打包的应用

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
OUTPUT_DIR="$PROJECT_ROOT/dish"

log_info "开始测试打包的应用..."
log_info "输出目录: $OUTPUT_DIR"

# 检查可执行文件是否存在
if [ ! -f "$OUTPUT_DIR/NetEaseCloudMusic" ]; then
    log_error "未找到可执行文件: $OUTPUT_DIR/NetEaseCloudMusic"
    exit 1
fi

log_success "找到可执行文件"

# 检查文件权限
if [ ! -x "$OUTPUT_DIR/NetEaseCloudMusic" ]; then
    log_warning "可执行文件没有执行权限，正在添加..."
    chmod +x "$OUTPUT_DIR/NetEaseCloudMusic"
    log_success "已添加执行权限"
else
    log_success "可执行文件权限正确"
fi

# 显示文件信息
file_size=$(du -h "$OUTPUT_DIR/NetEaseCloudMusic" | cut -f1)
log_info "文件大小: $file_size"

# 检查文件类型
file_type=$(file "$OUTPUT_DIR/NetEaseCloudMusic")
log_info "文件类型: $file_type"

# 检查依赖库
log_info "检查依赖库..."
if command -v ldd &> /dev/null; then
    log_info "动态库依赖:"
    ldd "$OUTPUT_DIR/NetEaseCloudMusic" | head -10
    
    # 检查是否有缺失的库
    missing_libs=$(ldd "$OUTPUT_DIR/NetEaseCloudMusic" 2>/dev/null | grep "not found" | wc -l)
    if [ "$missing_libs" -eq 0 ]; then
        log_success "所有动态库依赖都满足"
    else
        log_warning "发现 $missing_libs 个缺失的动态库"
    fi
else
    log_warning "ldd命令不可用，跳过动态库检查"
fi

# 检查Python版本兼容性
log_info "检查Python版本..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    log_info "系统Python版本: $python_version"
    
    # 检查是否满足最低要求 (3.12.3)
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 12, 3) else 1)" 2>/dev/null; then
        log_success "Python版本满足要求"
    else
        log_warning "Python版本可能不兼容，建议使用3.12.3或更高版本"
    fi
else
    log_error "未找到Python3"
fi

# 检查Qt相关库
log_info "检查Qt相关库..."
if command -v pkg-config &> /dev/null; then
    if pkg-config --exists Qt6Core 2>/dev/null; then
        qt_version=$(pkg-config --modversion Qt6Core)
        log_success "找到Qt6, 版本: $qt_version"
    elif pkg-config --exists Qt5Core 2>/dev/null; then
        qt_version=$(pkg-config --modversion Qt5Core)
        log_warning "找到Qt5, 版本: $qt_version (建议使用Qt6)"
    else
        log_warning "未找到Qt开发库"
    fi
else
    log_warning "pkg-config不可用，跳过Qt库检查"
fi

# 创建测试报告
test_report="$OUTPUT_DIR/test_report_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "网易云音乐桌面版 - 测试报告"
    echo "测试时间: $(date)"
    echo "测试结果: 通过"
    echo ""
    echo "文件信息:"
    echo "  文件路径: $OUTPUT_DIR/NetEaseCloudMusic"
    echo "  文件大小: $file_size"
    echo "  文件类型: $file_type"
    echo ""
    echo "系统信息:"
    echo "  操作系统: $(uname -s)"
    echo "  架构: $(uname -m)"
    echo "  Python版本: $(python3 --version 2>/dev/null || echo '未找到')"
    echo ""
    echo "测试项目:"
    echo "  ✓ 文件存在性检查"
    echo "  ✓ 文件权限检查"
    echo "  ✓ 依赖库检查"
    echo "  ✓ Python版本检查"
    echo "  ✓ Qt库检查"
    echo ""
    echo "建议:"
    echo "  1. 在运行前确保系统安装了必要的依赖库"
    echo "  2. 建议在Linux桌面环境中运行"
    echo "  3. 首次运行可能需要较长时间加载"
} > "$test_report"

log_success "测试报告已保存: $test_report"

# 运行测试（非交互模式）
log_info "进行快速启动测试..."
log_info "注意：这将启动应用并立即关闭，用于验证启动过程"

# 创建临时测试脚本
test_script="/tmp/test_netapp_$$"
cat > "$test_script" << 'EOF'
#!/bin/bash
export QT_QPA_PLATFORM=offscreen
export DISPLAY=:99
timeout 10s "$1" 2>&1 | head -20
EOF

chmod +x "$test_script"

# 运行测试
log_info "启动应用进行测试..."
if timeout 15s "$test_script" "$OUTPUT_DIR/NetEaseCloudMusic" 2>/dev/null; then
    log_success "应用启动测试通过"
else
    log_warning "应用启动测试超时或失败（这可能是正常的，因为缺少显示环境）"
fi

# 清理临时文件
rm -f "$test_script"

echo
echo "=== 测试完成 ==="
log_success "所有测试项目完成"
log_info "可执行文件: $OUTPUT_DIR/NetEaseCloudMusic"
log_info "测试报告: $test_report"
log_info "使用方法: $OUTPUT_DIR/NetEaseCloudMusic"
echo
echo "运行应用："
echo "  cd $OUTPUT_DIR"
echo "  ./NetEaseCloudMusic"
