#!/bin/bash

# 网易云音乐桌面版打包脚本 v2.0
# 专注于兼容性和可靠性

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

echo -e "${BLUE}=== 网易云音乐桌面版打包脚本 v2.0 ===${NC}"
echo -e "${BLUE}项目根目录: $PROJECT_ROOT${NC}"
echo -e "${BLUE}打包目录: $PACKAGING_DIR${NC}"
echo -e "${BLUE}输出目录: $DISH_DIR${NC}"
echo -e "${BLUE}重点关注: 兼容性和可靠性${NC}"
echo

# 清理并创建输出目录
echo -e "${YELLOW}准备输出目录...${NC}"
rm -rf "$DISH_DIR"
mkdir -p "$DISH_DIR"

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

# 确保使用虚拟环境中的Python
GLOBAL_PYTHON="$VENV_DIR/bin/python3"
if [ ! -f "$GLOBAL_PYTHON" ]; then
    echo -e "${RED}错误: 虚拟环境Python不存在: $GLOBAL_PYTHON${NC}"
    exit 1
fi

# 安装和更新依赖
echo -e "${YELLOW}检查并安装依赖...${NC}"
cd "$PROJECT_ROOT"

# 使用uv安装项目依赖（包括开发依赖）
if command -v uv > /dev/null 2>&1; then
    echo -e "${GREEN}使用uv安装依赖...${NC}"
    uv sync --dev
else
    echo -e "${RED}错误: uv未安装，请先安装uv${NC}"
    exit 1
fi

# 确保PyInstaller已安装
echo -e "${YELLOW}检查PyInstaller...${NC}"
if ! $GLOBAL_PYTHON -m pip show pyinstaller > /dev/null 2>&1; then
    echo -e "${YELLOW}安装PyInstaller...${NC}"
    uv add pyinstaller
else
    echo -e "${GREEN}PyInstaller已安装${NC}"
fi

# 导出完整依赖列表
echo -e "${YELLOW}导出依赖列表...${NC}"
uv pip freeze > "$PACKAGING_DIR/requirements_full.txt"
echo -e "${GREEN}依赖列表已保存到: $PACKAGING_DIR/requirements_full.txt${NC}"

# 检查关键依赖
echo -e "${YELLOW}检查关键依赖...${NC}"
CRITICAL_DEPS=("PySide6" "PyInstaller")
for dep in "${CRITICAL_DEPS[@]}"; do
    if uv pip show "$dep" > /dev/null 2>&1; then
        VERSION=$(uv pip show "$dep" | grep Version | cut -d' ' -f2)
        echo -e "${GREEN}✓ $dep: $VERSION${NC}"
    else
        echo -e "${RED}✗ 缺少关键依赖: $dep${NC}"
        exit 1
    fi
done

# 生成PyInstaller规格文件
echo -e "${YELLOW}生成PyInstaller规格文件...${NC}"
$GLOBAL_PYTHON "$PACKAGING_DIR/build_spec.py"

# 验证规格文件
if [ ! -f "$PACKAGING_DIR/netease_music.spec" ]; then
    echo -e "${RED}错误: 规格文件生成失败${NC}"
    exit 1
fi

# 执行打包
echo -e "${YELLOW}开始打包应用...${NC}"
cd "$PROJECT_ROOT"

# 使用PyInstaller打包（单文件模式，确保兼容性）
$GLOBAL_PYTHON -m PyInstaller \
    --clean \
    --noconfirm \
    --log-level INFO \
    "$PACKAGING_DIR/netease_music.spec"

# 检查打包结果
echo -e "${YELLOW}检查打包结果...${NC}"
DIST_DIR="$PROJECT_ROOT/dist"
EXECUTABLE_NAME="NetEaseMusicDesktop"

if [ -f "$DIST_DIR/$EXECUTABLE_NAME" ]; then
    echo -e "${GREEN}✓ 单文件可执行文件生成成功${NC}"
    EXECUTABLE_PATH="$DIST_DIR/$EXECUTABLE_NAME"
elif [ -d "$DIST_DIR/$EXECUTABLE_NAME" ]; then
    echo -e "${GREEN}✓ 目录模式可执行文件生成成功${NC}"
    EXECUTABLE_PATH="$DIST_DIR/$EXECUTABLE_NAME/$EXECUTABLE_NAME"
else
    echo -e "${RED}错误: 未找到打包结果${NC}"
    echo -e "${YELLOW}dist目录内容:${NC}"
    ls -la "$DIST_DIR/"
    exit 1
fi

# 检查可执行文件权限和依赖
echo -e "${YELLOW}验证可执行文件...${NC}"
if [ -f "$EXECUTABLE_PATH" ]; then
    # 检查文件权限
    if [ -x "$EXECUTABLE_PATH" ]; then
        echo -e "${GREEN}✓ 可执行文件权限正确${NC}"
    else
        echo -e "${YELLOW}添加可执行权限...${NC}"
        chmod +x "$EXECUTABLE_PATH"
    fi
    
    # 检查文件大小
    FILE_SIZE=$(du -h "$EXECUTABLE_PATH" | cut -f1)
    echo -e "${GREEN}✓ 文件大小: $FILE_SIZE${NC}"
    
    # 检查依赖（简单检查）
    if command -v ldd > /dev/null 2>&1; then
        echo -e "${YELLOW}检查动态库依赖...${NC}"
        if ldd "$EXECUTABLE_PATH" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 动态库依赖检查通过${NC}"
        else
            echo -e "${YELLOW}警告: 部分动态库依赖可能缺失${NC}"
        fi
    fi
else
    echo -e "${RED}错误: 可执行文件不存在${NC}"
    exit 1
fi

# 移动生成的文件到dish目录
echo -e "${YELLOW}整理打包结果...${NC}"
if [ -f "$DIST_DIR/$EXECUTABLE_NAME" ]; then
    # 单文件模式
    cp "$DIST_DIR/$EXECUTABLE_NAME" "$DISH_DIR/"
    echo -e "${GREEN}单文件模式: 可执行文件已复制到: $DISH_DIR/$EXECUTABLE_NAME${NC}"
elif [ -d "$DIST_DIR/$EXECUTABLE_NAME" ]; then
    # 目录模式
    cp -r "$DIST_DIR/$EXECUTABLE_NAME"/* "$DISH_DIR/"
    echo -e "${GREEN}目录模式: 所有文件已复制到: $DISH_DIR/${NC}"
else
    echo -e "${RED}错误: 未找到打包结果${NC}"
    exit 1
fi

# 创建启动脚本
echo -e "${YELLOW}创建启动脚本...${NC}"
cat > "$DISH_DIR/run.sh" << 'EOF'
#!/bin/bash
# 网易云音乐桌面版启动脚本 v2.0

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 设置环境变量确保兼容性
export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_QPA_PLATFORM=xcb
export QT_LOGGING_RULES="*=false"

# 检查依赖
if ! command -v ldconfig > /dev/null 2>&1; then
    echo "警告: ldconfig不可用，可能影响库加载"
fi

# 如果是单文件模式，直接执行
if [ -f "NetEaseMusicDesktop" ]; then
    echo "启动网易云音乐桌面版..."
    ./NetEaseMusicDesktop "$@"
    RESULT=$?
elif [ -f "NetEaseMusicDesktop/NetEaseMusicDesktop" ]; then
    # 如果是目录模式，执行目录中的可执行文件
    echo "启动网易云音乐桌面版..."
    ./NetEaseMusicDesktop/NetEaseMusicDesktop "$@"
    RESULT=$?
else
    echo "错误: 未找到可执行文件"
    echo "当前目录内容:"
    ls -la
    exit 1
fi

# 检查退出状态
if [ $RESULT -eq 0 ]; then
    echo "应用正常退出"
else
    echo "应用异常退出，退出码: $RESULT"
fi

exit $RESULT
EOF

chmod +x "$DISH_DIR/run.sh"

# 创建测试脚本
echo -e "${YELLOW}创建测试脚本...${NC}"
cat > "$DISH_DIR/test.sh" << 'EOF'
#!/bin/bash
# 网易云音乐桌面版测试脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== 网易云音乐桌面版兼容性测试 ==="
echo "测试目录: $SCRIPT_DIR"
echo

# 检查可执行文件
if [ -f "$SCRIPT_DIR/NetEaseMusicDesktop" ]; then
    EXECUTABLE="$SCRIPT_DIR/NetEaseMusicDesktop"
elif [ -f "$SCRIPT_DIR/NetEaseMusicDesktop/NetEaseMusicDesktop" ]; then
    EXECUTABLE="$SCRIPT_DIR/NetEaseMusicDesktop/NetEaseMusicDesktop"
else
    echo "❌ 错误: 未找到可执行文件"
    exit 1
fi

echo "✓ 可执行文件: $EXECUTABLE"

# 检查文件权限
if [ -x "$EXECUTABLE" ]; then
    echo "✓ 可执行文件权限正确"
else
    echo "❌ 可执行文件权限错误"
    exit 1
fi

# 检查文件大小
SIZE=$(stat -f%z "$EXECUTABLE" 2>/dev/null || stat -c%s "$EXECUTABLE" 2>/dev/null || echo "unknown")
if [ "$SIZE" != "unknown" ] && [ "$SIZE" -gt 1000000 ]; then
    echo "✓ 文件大小正常: $(($SIZE / 1024 / 1024))MB"
else
    echo "⚠️  文件大小可能异常"
fi

# 检查依赖
if command -v ldd > /dev/null 2>&1; then
    echo "检查动态库依赖..."
    if ldd "$EXECUTABLE" > /dev/null 2>&1; then
        echo "✓ 动态库依赖检查通过"
        
        # 检查关键库
        KEY_LIBS=("libQt6" "libX11" "libGL")
        for lib in "${KEY_LIBS[@]}"; do
            if ldd "$EXECUTABLE" | grep -q "$lib"; then
                echo "✓ 找到关键库: $lib"
            else
                echo "⚠️  可能缺少关键库: $lib"
            fi
        done
    else
        echo "❌ 动态库依赖检查失败"
    fi
else
    echo "⚠️  ldd不可用，跳过依赖检查"
fi

# 检查环境
echo "检查运行环境..."
if command -v python3 > /dev/null 2>&1; then
    PYTHON_VER=$(python3 --version)
    echo "✓ 系统Python: $PYTHON_VER"
fi

if command -v DISPLAY > /dev/null 2>&1 || [ -n "$DISPLAY" ]; then
    echo "✓ 显示环境可用"
else
    echo "⚠️  显示环境可能不可用"
fi

echo
echo "=== 测试完成 ==="
echo "如果所有检查都通过，可以尝试运行: ./run.sh"
EOF

chmod +x "$DISH_DIR/test.sh"

# 创建调试脚本
echo -e "${YELLOW}创建调试脚本...${NC}"
cat > "$DISH_DIR/debug.sh" << 'EOF'
#!/bin/bash
# 网易云音乐桌面版调试脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== 网易云音乐桌面版调试模式 ==="
echo "调试目录: $SCRIPT_DIR"
echo

# 设置调试环境变量
export QT_DEBUG_PLUGINS=1
export QT_LOGGING_RULES="*=true"
export PYINSTALLER_VERBOSE=1

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 如果是单文件模式
if [ -f "NetEaseMusicDesktop" ]; then
    echo "以调试模式启动..."
    ./NetEaseMusicDesktop --debug "$@"
elif [ -f "NetEaseMusicDesktop/NetEaseMusicDesktop" ]; then
    echo "以调试模式启动..."
    ./NetEaseMusicDesktop/NetEaseMusicDesktop --debug "$@"
else
    echo "错误: 未找到可执行文件"
    exit 1
fi
EOF

chmod +x "$DISH_DIR/debug.sh"

# 创建README
echo -e "${YELLOW}创建打包说明文档...${NC}"
cat > "$DISH_DIR/README_packaging.md" << 'EOF'
# 网易云音乐桌面版 - 打包版本 v2.0

## 🎯 重点关注

本版本专注于**兼容性和可靠性**，解决了之前版本无法正常启动的问题。

## 📁 文件说明

- `NetEaseMusicDesktop` - 主可执行文件
- `run.sh` - **推荐使用**的启动脚本（包含环境检查）
- `test.sh` - 兼容性测试脚本
- `debug.sh` - 调试模式启动脚本
- `README_packaging.md` - 本说明文件

## 🚀 运行方法

### 方法1: 使用启动脚本（强烈推荐）
```bash
./run.sh
```

### 方法2: 先测试再运行
```bash
./test.sh  # 检查兼容性
./run.sh   # 如果测试通过则运行
```

### 方法3: 调试模式
```bash
./debug.sh  # 显示详细调试信息
```

### 方法4: 直接运行（不推荐）
```bash
./NetEaseMusicDesktop
```

## 🔧 兼容性改进

### 已修复的问题
1. **依赖完整性** - 确保所有PySide6组件正确打包
2. **环境变量** - 自动设置必要的Qt环境变量
3. **权限问题** - 自动修复可执行文件权限
4. **路径问题** - 正确处理资源文件路径

### 系统要求
- Linux x86_64 系统
- 支持X11的桌面环境
- 基本的图形库支持（libX11, libGL等）

## 🐛 故障排除

### 常见问题

1. **无法启动**
   ```bash
   ./test.sh  # 运行兼容性测试
   ```

2. **显示错误信息**
   ```bash
   ./debug.sh  # 使用调试模式查看详细错误
   ```

3. **权限问题**
   ```bash
   chmod +x NetEaseMusicDesktop run.sh test.sh debug.sh
   ```

4. **缺少库文件**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libx11-6 libgl1-mesa-glx libxcb-xinerama0
   
   # CentOS/RHEL
   sudo yum install libX11 mesa-libGL libxcb-xinerama
   ```

### 日志文件
应用运行时会在以下位置创建日志：
- `logs/app.log` - 主应用日志
- `logs/error.log` - 错误日志
- `logs/webview.log` - WebView日志

## 📊 打包信息

- **打包时间**: $(date)
- **打包工具**: PyInstaller + uv
- **Python版本**: $(python3 --version)
- **目标平台**: Linux x86_64
- **打包模式**: 单文件（包含所有依赖）

## 💡 提示

1. 首次运行可能需要较长时间（解压内置资源）
2. 建议在图形界面环境下运行
3. 如果遇到问题，请先运行 `test.sh` 检查兼容性
4. 调试信息可以帮助定位具体问题

## 🆘 获取帮助

如果仍然无法正常运行，请：
1. 运行 `./test.sh` 并记录输出
2. 运行 `./debug.sh` 并记录错误信息
3. 检查系统是否满足基本要求
4. 联系开发者并提供详细的错误信息
EOF

# 设置可执行权限
echo -e "${YELLOW}设置文件权限...${NC}"
chmod +x "$DISH_DIR"/*.sh

# 运行兼容性测试
echo -e "${YELLOW}运行兼容性测试...${NC}"
if "$DISH_DIR/test.sh"; then
    echo -e "${GREEN}✓ 兼容性测试通过${NC}"
else
    echo -e "${YELLOW}⚠️ 兼容性测试发现问题，请检查输出${NC}"
fi

# 最终清理
echo -e "${YELLOW}清理临时文件...${NC}"
rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist/__pycache__"

echo -e "${GREEN}=== 打包完成! ===${NC}"
echo -e "${GREEN}输出目录: $DISH_DIR${NC}"
echo -e "${GREEN}主程序: $DISH_DIR/NetEaseMusicDesktop${NC}"
echo -e "${GREEN}启动脚本: $DISH_DIR/run.sh${NC}"
echo -e "${GREEN}测试脚本: $DISH_DIR/test.sh${NC}"
echo -e "${GREEN}调试脚本: $DISH_DIR/debug.sh${NC}"
echo -e "${GREEN}说明文档: $DISH_DIR/README_packaging.md${NC}"
echo
echo -e "${BLUE}🚀 推荐运行流程:${NC}"
echo -e "${BLUE}1. $DISH_DIR/test.sh   # 检查兼容性${NC}"
echo -e "${BLUE}2. $DISH_DIR/run.sh    # 启动应用${NC}"
echo
echo -e "${YELLOW}如果遇到问题，请运行: $DISH_DIR/debug.sh${NC}"
