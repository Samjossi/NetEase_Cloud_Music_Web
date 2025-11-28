# 网易云音乐打包工具 - GUI版本

## 概述

这是一个基于Tkinter的图形化打包管理器，提供了统一的界面来管理网易云音乐桌面版的各种打包模式。

## 功能特性

### 🎯 打包模式
1. **快速构建** - 生成Linux可执行文件 (约213MB，需要系统Python 3.12.3+)
2. **AppImage构建** - 生成AppImage便携版 (约300-400MB，自包含环境)
3. **依赖检查** - 检查系统环境和依赖
4. **测试构建** - 测试已构建的文件
5. **清理临时文件** - 清理构建缓存和临时文件

### 🛠️ GUI功能
- 🖥️ 友好的图形界面
- 📊 实时进度显示
- 📝 彩色日志输出
- ⏸️ 开始/停止控制
- 📁 一键打开输出目录
- 🔍 环境自动检查

## 使用方法

### 快速启动
```bash
# 方法1: 使用启动脚本
./packaging_04/start_packaging_gui.sh

# 方法2: 直接运行Python脚本
python3 packaging_04/scripts/packaging_gui.py
```

### 使用步骤
1. **启动GUI** - 运行启动脚本
2. **选择模式** - 选择要执行的打包模式
3. **开始打包** - 点击"开始打包"按钮
4. **查看进度** - 观察实时日志和进度
5. **获取结果** - 打包完成后查看输出文件

## 界面说明

### 打包模式区域
- 单选按钮选择不同的打包模式
- 每个模式都有详细的描述信息
- 自动显示文件大小和系统要求

### 进度显示
- 实时显示当前操作状态
- 动态进度条显示处理进度
- 清晰的状态文字提示

### 日志输出
- 带时间戳的彩色日志
- 不同级别的日志颜色区分
- 可清空日志内容
- 自动滚动到最新消息

### 控制按钮
- **开始打包** - 启动选定的打包模式
- **停止** - 中断正在进行的打包过程
- **打开输出目录** - 快速访问打包结果
- **清空日志** - 清除日志显示内容

## 输出文件

### 快速构建模式
```
packaging_04/dish/
├── NetEaseCloudMusic           # Linux可执行文件
├── README_quick_build.txt      # 使用说明
└── test_report_*.txt          # 测试报告
```

### AppImage构建模式
```
packaging_04/dish/
├── NetEaseCloudMusic-*.AppImage # AppImage便携版
├── NetEaseCloudMusic           # 可执行文件
└── PACKAGING_SUMMARY.md       # 打包文档
```

## 系统要求

### 基本要求
- Linux x86_64 操作系统
- Python 3.12.3 或更高版本
- Tkinter GUI支持 (通常随Python安装)

### 依赖要求
- **快速构建**: 需要系统Python 3.12.3+
- **AppImage构建**: 需要系统Python + appimage工具
- **依赖检查**: 基本的Linux开发工具

### 可选依赖
- PySide6 (用于应用运行)
- appimagetool (用于AppImage打包)
- UPX (用于文件压缩)

## 故障排除

### GUI启动失败
```bash
# 检查Python版本
python3 --version

# 检查Tkinter
python3 -c "import tkinter; print('Tkinter OK')"

# 检查权限
ls -la packaging_04/start_packaging_gui.sh
```

### 打包失败
1. **检查环境**: 使用"依赖检查"模式
2. **查看日志**: 注意错误信息和警告
3. **清理重试**: 使用"清理临时文件"后重新尝试

### 常见问题
- **权限错误**: 确保脚本有执行权限
- **路径错误**: 在正确的目录下运行
- **依赖缺失**: 安装必要的系统包

## 技术细节

### 文件结构
```
packaging_04/
├── scripts/
│   ├── packaging_gui.py          # GUI主程序
│   ├── quick_build.sh           # 快速构建脚本
│   ├── build_appimage.sh        # AppImage构建脚本
│   ├── check_dependencies.sh     # 依赖检查脚本
│   ├── test_build.sh           # 测试脚本
│   └── clean_temp_files.sh     # 清理脚本 (自动生成)
├── dish/                       # 输出目录
├── build_logs/                  # 构建日志
└── start_packaging_gui.sh       # 启动脚本
```

### 日志级别
- **INFO** (ℹ️) - 一般信息，黑色
- **SUCCESS** (✅) - 成功操作，绿色
- **WARNING** (⚠️) - 警告信息，橙色
- **ERROR** (❌) - 错误信息，红色

## 开发说明

### 扩展新模式
1. 在`scripts/`目录添加新的脚本
2. 在GUI的`run_packaging`方法中添加模式映射
3. 更新模式列表和描述
4. 测试新功能

### 自定义界面
GUI使用标准的Tkinter组件，易于修改：
- ttk.Frame - 主要容器
- ttk.Radiobutton - 模式选择
- ttk.Progressbar - 进度显示
- scrolledtext.ScrolledText - 日志输出

## 许可证

本打包工具遵循与主项目相同的许可证。

## 支持

如有问题，请：
1. 查看日志输出中的错误信息
2. 检查系统环境和依赖
3. 尝试清理后重新打包
4. 提交Issue到项目仓库

---

**版本**: 1.0.0  
**更新时间**: 2025-11-28  
**兼容性**: Linux x86_64, Python 3.12.3+
