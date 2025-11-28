#!/bin/bash

# 网易云音乐桌面版打包脚本
# 使用全局Python解释器和虚拟环境依赖

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGING_DIR="$PROJECT_ROOT/packaging_02"
DISH_DIR="$PACKAGING_DIR/dish"
VENV_DIR="$PROJECT_ROOT/.venv"

echo -e "${BLUE}=== 网易云音乐桌面版打包脚本 ===${NC}"
echo -e "${BLUE}项目根目录: $PROJECT_ROOT${NC}"
echo -e "${BLUE}打包目录: $PACKAGING_DIR${NC}"
echo -e "${BLUE}输出目录: $DISH_DIR${NC}"
echo

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}错误: 虚拟环境不存在: $VENV_DIR${NC}"
    exit 1
fi

# 获取虚拟环境中的所有依赖（使用uv）
echo -e "${YELLOW}导出虚拟环境依赖...${NC}"
if command -v uv > /dev/null 2>&1; then
    uv pip freeze > "$PACKAGING_DIR/venv_requirements.txt"
else
    # 如果uv不可用，尝试激活虚拟环境后使用python -m pip
    source "$VENV_DIR/bin/activate"
    python -m pip freeze > "$PACKAGING_DIR/venv_requirements.txt"
fi

# 使用虚拟环境中的Python
GLOBAL_PYTHON="$VENV_DIR/bin/python3"
if [ ! -f "$GLOBAL_PYTHON" ]; then
    echo -e "${RED}错误: 虚拟环境Python不存在: $GLOBAL_PYTHON${NC}"
    exit 1
fi

echo -e "${GREEN}使用虚拟环境Python解释器: $GLOBAL_PYTHON${NC}"

# 在虚拟环境中安装PyInstaller（如果还没有）
echo -e "${YELLOW}检查并安装PyInstaller...${NC}"
if ! $GLOBAL_PYTHON -m pip show pyinstaller > /dev/null 2>&1; then
    echo -e "${YELLOW}安装PyInstaller到虚拟环境...${NC}"
    if command -v uv > /dev/null 2>&1; then
        uv add pyinstaller
    else
        echo -e "${RED}错误: uv不可用，无法安装PyInstaller${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}PyInstaller已安装在虚拟环境中${NC}"
fi

echo -e "${YELLOW}使用虚拟环境中现有的依赖...${NC}"
echo -e "${GREEN}虚拟环境依赖已包含在venv_requirements.txt中${NC}"

# 生成PyInstaller规格文件
echo -e "${YELLOW}生成PyInstaller规格文件...${NC}"
$GLOBAL_PYTHON "$PACKAGING_DIR/build_spec.py"

# 执行打包
echo -e "${YELLOW}开始打包应用...${NC}"
cd "$PROJECT_ROOT"

# 使用PyInstaller打包
$GLOBAL_PYTHON -m PyInstaller \
    --clean \
    --noconfirm \
    "$PACKAGING_DIR/netease_music.spec"

# 移动生成的文件到dish目录
echo -e "${YELLOW}整理打包结果...${NC}"
if [ -d "$PROJECT_ROOT/dist/NetEaseMusicDesktop" ]; then
    cp -r "$PROJECT_ROOT/dist/NetEaseMusicDesktop"/* "$DISH_DIR/"
    echo -e "${GREEN}打包完成! 文件已复制到: $DISH_DIR${NC}"
elif [ -f "$PROJECT_ROOT/dist/NetEaseMusicDesktop" ]; then
    cp "$PROJECT_ROOT/dist/NetEaseMusicDesktop" "$DISH_DIR/"
    echo -e "${GREEN}打包完成! 可执行文件已复制到: $DISH_DIR/NetEaseMusicDesktop${NC}"
else
    echo -e "${RED}错误: 未找到打包结果${NC}"
    exit 1
fi

# 创建启动脚本
echo -e "${YELLOW}创建启动脚本...${NC}"
cat > "$DISH_DIR/run.sh" << 'EOF'
#!/bin/bash
# 网易云音乐桌面版启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 如果是单文件模式，直接执行
if [ -f "NetEaseMusicDesktop" ]; then
    ./NetEaseMusicDesktop "$@"
else
    # 如果是目录模式，执行目录中的可执行文件
    if [ -f "NetEaseMusicDesktop/NetEaseMusicDesktop" ]; then
        ./NetEaseMusicDesktop/NetEaseMusicDesktop "$@"
    else
        echo "错误: 未找到可执行文件"
        exit 1
    fi
fi
EOF

chmod +x "$DISH_DIR/run.sh"

# 创建README
echo -e "${YELLOW}创建打包说明文档...${NC}"
cat > "$DISH_DIR/README_packaging.md" << 'EOF'
# 网易云音乐桌面版 - 打包版本

## 文件说明

- `NetEaseMusicDesktop` - 主可执行文件
- `run.sh` - 启动脚本（推荐使用）
- `README_packaging.md` - 本说明文件

## 运行方法

### 方法1: 使用启动脚本（推荐）
```bash
./run.sh
```

### 方法2: 直接运行可执行文件
```bash
./NetEaseMusicDesktop
```

## 注意事项

1. 本应用已经包含了所有必要的依赖，无需额外安装Python环境
2. 首次运行可能需要一些时间来初始化
3. 应用图标和资源文件已内置到可执行文件中
4. 日志文件将保存在应用目录下的 `logs/` 文件夹中

## 系统要求

- Linux x86_64 系统
- 支持GTK3的桌面环境（如GNOME、KDE、XFCE等）

## 故障排除

如果遇到无法启动的问题，请检查：
1. 文件是否有执行权限：`chmod +x NetEaseMusicDesktop`
2. 系统是否缺少必要的库：`ldd NetEaseMusicDesktop`
3. 查看错误日志：检查 `logs/` 目录下的日志文件

## 打包信息

- 打包时间: $(date)
- 打包工具: PyInstaller
- Python版本: $(python3 --version)
EOF

echo -e "${GREEN}=== 打包完成! ===${NC}"
echo -e "${GREEN}输出目录: $DISH_DIR${NC}"
echo -e "${GREEN}可执行文件: $DISH_DIR/NetEaseMusicDesktop${NC}"
echo -e "${GREEN}启动脚本: $DISH_DIR/run.sh${NC}"
echo -e "${GREEN}说明文档: $DISH_DIR/README_packaging.md${NC}"
echo
echo -e "${BLUE}运行应用: $DISH_DIR/run.sh${NC}"
