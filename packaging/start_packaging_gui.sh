#!/bin/bash
# 网易云音乐打包工具启动脚本

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUI_SCRIPT="$SCRIPT_DIR/scripts/packaging_gui.py"

echo "启动网易云音乐打包工具GUI..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 检查GUI脚本
if [ ! -f "$GUI_SCRIPT" ]; then
    echo "错误: 未找到GUI脚本: $GUI_SCRIPT"
    exit 1
fi

# 启动GUI
cd "$SCRIPT_DIR"
python3 "$GUI_SCRIPT"

# 如果退出码不为0，显示错误
if [ $? -ne 0 ]; then
    echo "GUI启动失败，退出码: $?"
    echo "请检查Python环境和依赖项"
    exit 1
fi
