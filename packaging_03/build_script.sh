#!/bin/bash

# 网易云音乐桌面版 AppImage打包脚本 v1.0
# 专门用于生成AppImage格式的便携应用

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGING_DIR="$PROJECT_ROOT/packaging_03"
DISH_DIR="$PACKAGING_DIR/dish"
VENV_DIR="$PROJECT_ROOT/.venv"

echo -e "${BLUE}=== 网易云音乐桌面版 AppImage打包脚本 v1.0 ===${NC}"
echo -e "${BLUE}项目根目录: $PROJECT_ROOT${NC}"
echo -e "${BLUE}打包目录: $PACKAGING_DIR${NC}"
echo -e "${BLUE}输出目录: $DISH_DIR${NC}"
echo -e "${BLUE}打包格式: AppImage${NC}"
echo

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}错误: 虚拟环境不存在: $VENV_DIR${NC}"
    echo -e "${YELLOW}请先运行: uv venv${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate"

# 检查Python版本
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}Python版本: $PYTHON_VERSION${NC}"

# 检查关键依赖
echo -e "${YELLOW}检查关键依赖...${NC}"
CRITICAL_DEPS=("PySide6" "appimage-builder")

for dep in "${CRITICAL_DEPS[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        VERSION=$(python3 -c "import $dep; print($dep.__version__ if hasattr($dep, '__version__') else 'unknown')" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓ $dep: $VERSION${NC}"
    else
        echo -e "${RED}✗ 缺少关键依赖: $dep${NC}"
        echo -e "${YELLOW}正在安装缺失的依赖...${NC}"
        
        case $dep in
            "PySide6")
                echo -e "${YELLOW}安装 PySide6...${NC}"
                uv add PySide6
                ;;
            "appimage-builder")
                echo -e "${YELLOW}安装 appimage-builder...${NC}"
                uv add appimage-builder
                ;;
        esac
    fi
done

# 检查系统工具
echo -e "${YELLOW}检查系统工具...${NC}"
REQUIRED_TOOLS=("python3" "ldd" "find" "cp")
OPTIONAL_TOOLS=("patchelf" "strip" "appimagetool")

for tool in "${REQUIRED_TOOLS[@]}"; do
    if command -v "$tool" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $tool${NC}"
    else
        echo -e "${RED}✗ 缺少必要工具: $tool${NC}"
        exit 1
    fi
done

for tool in "${OPTIONAL_TOOLS[@]}"; do
    if command -v "$tool" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $tool (可选)${NC}"
    else
        echo -e "${YELLOW}⚠️  $tool (可选，未安装)${NC}"
        case $tool in
            "appimagetool")
                echo -e "${YELLOW}  安装提示: wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage${NC}"
                echo -e "${YELLOW}           chmod +x appimagetool-x86_64.AppImage${NC}"
                echo -e "${YELLOW}           sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool${NC}"
                ;;
            "patchelf")
                echo -e "${YELLOW}  安装提示: sudo apt-get install patchelf  # Ubuntu/Debian${NC}"
                echo -e "${YELLOW}           sudo yum install patchelf     # CentOS/RHEL${NC}"
                ;;
        esac
    fi
done

# 准备输出目录
echo -e "${YELLOW}准备输出目录...${NC}"
if [ -d "$DISH_DIR" ]; then
    echo -e "${YELLOW}清理现有输出目录...${NC}"
    rm -rf "$DISH_DIR"
fi
mkdir -p "$DISH_DIR"
echo -e "${GREEN}✓ 输出目录已准备: $DISH_DIR${NC}"

# 安装构建依赖
echo -e "${YELLOW}安装构建依赖...${NC}"
cd "$PROJECT_ROOT"

# 确保uv sync
if command -v uv > /dev/null 2>&1; then
    echo -e "${GREEN}使用uv同步依赖...${NC}"
    uv sync --dev
else
    echo -e "${RED}错误: uv未安装${NC}"
    exit 1
fi

# 确保构建脚本可执行
echo -e "${YELLOW}设置构建脚本权限...${NC}"
chmod +x "$PACKAGING_DIR/appimage_builder.py"
chmod +x "$PACKAGING_DIR/build_utils"/*.py

# 执行AppImage构建
echo -e "${YELLOW}开始AppImage构建...${NC}"
cd "$PACKAGING_DIR"

python3 appimage_builder.py "$PROJECT_ROOT" "$DISH_DIR"

# 检查构建结果
echo -e "${YELLOW}检查构建结果...${NC}"

APPIMAGE_NAME="NetEaseMusicDesktop-x86_64.AppImage"
APPIMAGE_PATH="$DISH_DIR/$APPIMAGE_NAME"

if [ -f "$APPIMAGE_PATH" ]; then
    # 检查文件大小
    FILE_SIZE=$(stat -c%s "$APPIMAGE_PATH" 2>/dev/null || stat -f%z "$APPIMAGE_PATH" 2>/dev/null || echo "unknown")
    if [ "$FILE_SIZE" != "unknown" ]; then
        SIZE_MB=$((FILE_SIZE / 1024 / 1024))
        echo -e "${GREEN}✓ AppImage构建成功!${NC}"
        echo -e "${GREEN}  文件大小: ${SIZE_MB}MB${NC}"
        echo -e "${GREEN}  文件路径: $APPIMAGE_PATH${NC}"
    else
        echo -e "${YELLOW}⚠️  AppImage文件生成但大小检测失败${NC}"
    fi
    
    # 检查可执行权限
    if [ -x "$APPIMAGE_PATH" ]; then
        echo -e "${GREEN}✓ 可执行权限正确${NC}"
    else
        echo -e "${YELLOW}⚠️  设置可执行权限...${NC}"
        chmod +x "$APPIMAGE_PATH"
    fi
    
    # 检查其他文件
    EXPECTED_FILES=("run_appimage.sh" "test_appimage.sh" "README_AppImage.md")
    for file in "${EXPECTED_FILES[@]}"; do
        if [ -f "$DISH_DIR/$file" ]; then
            echo -e "${GREEN}✓ $file${NC}"
        else
            echo -e "${YELLOW}⚠️  $file 未生成${NC}"
        fi
    done
    
else
    echo -e "${RED}❌ AppImage构建失败${NC}"
    echo -e "${YELLOW}检查构建日志以获取详细错误信息${NC}"
    exit 1
fi

# 创建快速启动脚本
echo -e "${YELLOW}创建快速启动脚本...${NC}"
QUICK_RUN_SCRIPT="$DISH_DIR/quick_run.sh"
cat > "$QUICK_RUN_SCRIPT" << 'EOF'
#!/bin/bash
# 网易云音乐桌面版 - 快速启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE="$SCRIPT_DIR/NetEaseMusicDesktop-x86_64.AppImage"

if [ ! -f "$APPIMAGE" ]; then
    echo "错误: AppImage文件不存在"
    exit 1
fi

echo "启动网易云音乐桌面版..."
exec "$APPIMAGE" "$@"
EOF

chmod +x "$QUICK_RUN_SCRIPT"
echo -e "${GREEN}✓ 快速启动脚本: $QUICK_RUN_SCRIPT${NC}"

# 创建桌面集成脚本（可选）
echo -e "${YELLOW}创建桌面集成脚本...${NC}"
DESKTOP_INTEGRATION_SCRIPT="$DISH_DIR/install_desktop.sh"
cat > "$DESKTOP_INTEGRATION_SCRIPT" << 'EOF'
#!/bin/bash
# 网易云音乐桌面版 - 桌面集成脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE="$SCRIPT_DIR/NetEaseMusicDesktop-x86_64.AppImage"
DESKTOP_FILE="$SCRIPT_DIR/NetEaseMusicDesktop.desktop"

if [ ! -f "$APPIMAGE" ]; then
    echo "错误: AppImage文件不存在"
    exit 1
fi

# 复制到用户桌面
if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/"
    echo "✓ 桌面文件已复制到: $HOME/Desktop/"
fi

# 复制到应用目录
if [ -d "$HOME/.local/share/applications" ]; then
    cp "$DESKTOP_FILE" "$HOME/.local/share/applications/"
    echo "✓ 应用菜单项已添加"
fi

# 创建符号链接
if [ -d "$HOME/.local/bin" ]; then
    ln -sf "$APPIMAGE" "$HOME/.local/bin/NetEaseMusicDesktop"
    echo "✓ 命令行链接已创建: $HOME/.local/bin/NetEaseMusicDesktop"
fi

echo "桌面集成完成！"
echo "你可以从应用菜单或桌面启动网易云音乐桌面版。"
EOF

chmod +x "$DESKTOP_INTEGRATION_SCRIPT"
echo -e "${GREEN}✓ 桌面集成脚本: $DESKTOP_INTEGRATION_SCRIPT${NC}"

# 最终清理
echo -e "${YELLOW}清理临时文件...${NC}"
if [ -d "$PACKAGING_DIR/build" ]; then
    rm -rf "$PACKAGING_DIR/build"
    echo -e "${GREEN}✓ 构建临时文件已清理${NC}"
fi

# 显示结果摘要
echo
echo -e "${BLUE}=== AppImage构建完成! ===${NC}"
echo -e "${GREEN}📦 主文件: $APPIMAGE_PATH${NC}"
echo -e "${GREEN}🚀 运行脚本: $DISH_DIR/run_appimage.sh${NC}"
echo -e "${GREEN}🧪 测试脚本: $DISH_DIR/test_appimage.sh${NC}"
echo -e "${GREEN}⚡ 快速启动: $DISH_DIR/quick_run.sh${NC}"
echo -e "${GREEN}🖥️  桌面集成: $DISH_DIR/install_desktop.sh${NC}"
echo -e "${GREEN}📖 说明文档: $DISH_DIR/README_AppImage.md${NC}"
echo
echo -e "${BLUE}🎯 推荐使用方法:${NC}"
echo -e "${BLUE}1. 运行测试: $DISH_DIR/test_appimage.sh${NC}"
echo -e "${BLUE}2. 启动应用: $DISH_DIR/run_appimage.sh${NC}"
echo -e "${BLUE}3. 快速启动: $DISH_DIR/quick_run.sh${NC}"
echo -e "${BLUE}4. 桌面集成: $DISH_DIR/install_desktop.sh${NC}"
echo
echo -e "${YELLOW}💡 提示: 首次运行可能需要较长时间解压内置资源${NC}"
echo -e "${YELLOW}💡 提示: 如果遇到问题，请检查系统是否安装了libfuse2${NC}"
