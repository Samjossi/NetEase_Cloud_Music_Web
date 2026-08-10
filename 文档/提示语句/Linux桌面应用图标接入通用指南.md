# Linux 桌面应用图标接入通用指南（含 AppImage）

> **适用对象**：任意 Linux 桌面应用开发者。
> **目标**：让应用在窗口标题栏、任务栏、最小化后的任务栏项、Alt-Tab 切换器、应用菜单中**全部显示自定义图标**，而不是桌面环境的兜底「齿轮」图标。
> **原理一句话**：Linux 桌面图标不是单一开关，而是**三条独立链路**，断任何一条就退回系统默认图标（齿轮）。必须三条全通。

---

## 一、为什么是「三条链路」

桌面环境（KDE / GNOME 等）显示应用图标时，按场景分别走三条机制：

| # | 链路 | 管什么 | 断了的后果 |
|---|------|--------|-----------|
| 1 | **窗口图标**（代码内设置） | 窗口标题栏、X11 任务栏、Alt-Tab、最小化后的任务栏项 | 标题栏/任务栏显示齿轮 |
| 2 | **desktop 文件 + 图标文件**（打包/安装产物） | 应用菜单、启动器、dock 固定项 | 菜单里是齿轮 |
| 3 | **StartupWMClass / desktopFileName 关联** | 桌面环境把「运行中的窗口」对上「desktop 文件」，从而在任务栏/dock 显示正确图标 | 菜单里有图标，但运行起来任务栏仍是齿轮（最常见症状） |

三条链路互相独立、缺一不可。下面逐条给出做法。

---

## 二、链路 1：代码内设置窗口图标

应用启动时显式调用窗口图标 API，并**注册多尺寸**——Qt/系统会按场景（标题栏小尺寸、任务栏大尺寸）自动挑最近尺寸，杜绝单图缩放糊边。

以 Qt（PySide6 / C++ Qt 同理）为例：

```python
from PySide6.QtGui import QIcon

def build_app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 32, 48, 64, 128, 256):
        path = assets_dir / f"logo_{size}.png"
        if path.is_file():
            icon.addFile(str(path))
    return icon

app.setWindowIcon(build_app_icon())
```

要点：

- **多尺寸注册**，不要只 `QIcon("logo.png")` 单图；
- 图标文件需随包分发（打包时确认被收编进产物）；
- 全套缺失时应降级告警而非崩溃，让应用用系统默认图标继续跑。

其他框架对应 API：GTK 用 `gtk_window_set_icon` / `g_application` 资源；Electron 用 `BrowserWindow({ icon })`。

---

## 三、链路 2：desktop 文件 + 图标文件规范放置

提供一个符合 freedesktop 规范的 `.desktop` 文件：

```ini
[Desktop Entry]
Type=Application
Name=My App
Exec=my-app
Icon=my-app                # ← 与图标文件名（去扩展名）一致
Terminal=false
Categories=Development;
StartupWMClass=my-app      # ← 链路 3 的关键，见下节
StartupNotify=true
```

图标文件放置规范（两选一）：

1. **与 desktop 文件同级、文件名 = `Icon=` 值 + 扩展名**：`my-app.png`（AppImage AppDir 根目录采用此形态）；
2. **XDG 图标主题目录**：`~/.local/share/icons/hicolor/<尺寸>/apps/my-app.png`（传统安装形态采用）。

命名要求：`Icon=` 的值**不含扩展名、不含路径**，且必须与图标文件主名**逐字一致**（大小写敏感）。

---

## 四、链路 3：StartupWMClass 关联（最容易漏的一条）

桌面环境靠窗口的 `WM_CLASS`（X11）或 `desktop file name`（Wayland）把运行中的窗口关联到 desktop 文件。关联不上时，任务栏无法取到 desktop 文件里的图标，只能显示齿轮。

做法（两件都要）：

1. **desktop 文件里写 `StartupWMClass=<应用窗口的 WM_CLASS>`**，值必须与窗口实际 WM_CLASS 一致；
2. **代码内声明 desktop file name**（Qt 为例）：

```python
app.setDesktopFileName("my-app")   # Wayland 下靠它关联 my-app.desktop
```

排查工具：`xprop WM_CLASS` 后点击窗口，看实际 WM_CLASS 与 `StartupWMClass` 是否一致。

### ⚠️ X11 深坑：WM_CLASS 有两个字段，`setApplicationName` 只钉得住一个

X11 的 `WM_CLASS(STRING) = "instance", "class"` 由两个字段组成，Qt 下来源不同：

| 字段 | Qt 来源 | 风险 |
|------|---------|------|
| instance（res_name） | **`argv[0]` 主名** | 打包形态改变 `argv[0]` 时漂移：AppImage 下变成 `my_app.appimage`，含下划线/后缀/版本号 |
| class（res_class） | `setApplicationName()` | 显式设置后即固定 |

GNOME 匹配运行窗口与 desktop 文件时依赖该值，instance 失配同样关联失败 → 任务栏退回齿轮。**`setApplicationName("my-app")` 钉不住 instance**，必须在创建 `QApplication` **之前**改写 `argv[0]`：

```python
sys.argv[0] = "my-app"               # 先于 QApplication，钉死 instance
app = QApplication(sys.argv)
app.setApplicationName("my-app")     # 钉死 class
```

踩坑实例（Pixiv Toolkit，2026-08）：onedir 形态 `argv[0]` 主名恰好等于应用名，三链路巧合全通；换 AppImage 形态后 instance 变为 `pixiv_toolkit.appimage`，与 `StartupWMClass=pixiv-toolkit` 失配，最小化后任务栏退回齿轮。详见 `2026-0807-0904_AppImage任务栏齿轮图标根因修复报告.md`。

**排查顺序建议：链路 3 → 1 → 2**——`xprop WM_CLASS` 一条命令即可锁定本类最常见故障，优先于翻打包产物。

---

## 五、AppImage 打包专项

AppImage 是只读 squashfs，图标接入在上述三条之外有打包侧要求。**AppDir 组装时必须做到**：

```
MyApp.AppDir/
├── AppRun                  # 启动脚本
├── my-app.desktop          # ← AppDir 根，含 Icon=my-app 与 StartupWMClass=my-app
├── my-app.png              # ← AppDir 根，文件名与 Icon= 值一致
└── usr/bin/...             # 应用本体
```

- desktop 文件与图标文件**都在 AppDir 根目录**，这是 appimagetool / 集成工具约定的位置；
- 构建脚本里用 `cat > AppDir/my-app.desktop` 直接生成，并把图标源文件 `cp` 成约定名；
- 冒烟验证：打包后 `--appimage-extract` 解包，断言 desktop 文件与 png 存在。

**运行时还需集成工具**（AppImageLauncher / appimaged 等）把 desktop 文件和图标解出注册到系统菜单。AppImage 本体只提供素材，注册动作由集成工具完成——用户直接双击运行 AppImage 而不集成时，菜单图标不会自动出现，但窗口/任务栏图标（链路 1）仍然有效，因为那是代码内设置的。

---

## 六、验证清单（交付前逐项确认）

- [ ] 窗口标题栏显示自定义图标
- [ ] 任务栏（含最小化后）显示自定义图标
- [ ] Alt-Tab 切换器显示自定义图标
- [ ] 应用菜单/启动器显示自定义图标
- [ ] 运行中的窗口在 dock/任务栏与菜单图标一致（StartupWMClass 关联成功）
- [ ] 打包产物解包核对：desktop 文件、各尺寸图标均在包内
- [ ] `xprop WM_CLASS` 实测值 = desktop 文件 `StartupWMClass` 值

---

## 七、故障排查速查

| 症状 | 最可能原因 | 修法 |
|------|-----------|------|
| 标题栏是齿轮 | 链路 1：没调 `setWindowIcon`，或图标文件没打进包 | 代码内注册图标；核对打包收编 |
| 菜单里是齿轮 | 链路 2：`Icon=` 与图标文件名不符，或图标没放对位置 | 逐字核对命名与放置规范 |
| 菜单有图标、运行时任务栏是齿轮 | 链路 3：StartupWMClass 不匹配 / 缺 `setDesktopFileName` | `xprop` 实测 WM_CLASS **两个字段**后对齐；AppImage 下重点查 instance 是否被 `argv[0]` 污染（见 §四深坑） |
| 仅某种打包形态（AppImage）下是齿轮，开发态正常 | 链路 3：`argv[0]` 主名被打包形态改变，WM_CLASS instance 漂移 | `QApplication` 创建前改写 `sys.argv[0]`（见 §四深坑） |
| 图标糊边 | 只注册了单张图被强制缩放 | 多尺寸注册 |
| AppImage 菜单无图标 | 未用集成工具集成 | 安装 AppImageLauncher 或手动注册 desktop 文件 |

---

## 八、落地参照实例

**Zen Studio：**

- 窗口图标：`main.py` `build_app_icon()`（多尺寸注册）+ `app.setWindowIcon()` + `app.setDesktopFileName("zen-studio")`
- AppDir 组装：`building/build_appimage.sh` 生成 `zen-studio.desktop`（含 `StartupWMClass=zen-studio`）并拷贝 `assets/logo/logo_256.png` 为 `zen-studio.png`
- 图标源文件：`assets/logo/`（多尺寸 logo 族）

**Pixiv Toolkit：**

- 窗口图标：`app.py` `build_app_icon()`（多尺寸注册）+ `app.setWindowIcon()` + `app.setDesktopFileName("pixiv-toolkit")`
- WM_CLASS 双字段钉死：`QApplication` 创建前 `sys.argv[0] = "pixiv-toolkit"`（§四深坑的实战修复）
- AppDir 组装：`打包/build_appimage.sh` 生成 `pixiv-toolkit.desktop` 并拷贝 `asset/icons/logo_256.png` 为 `pixiv-toolkit.png`，另备 hicolor 多尺寸
