# -*- mode: python ; coding: utf-8 -*-
"""
NetEaseMusicDesktop PyInstaller 规格文件（持久化版本）

相对旧版（构建期临时生成于 packaging/temp/）的改动：
- 路径可移植：用 SPECPATH 推导项目根，不再硬编码绝对路径
- hiddenimports 补齐新模块：gui.title_bar / gui.window_resize / pipewire_manager*
- datas 只保留 icon/（config/logger/gui 是 Python 包，走 imports，不再整体拷贝）
- 瘦身：
  * excludes 排除未用的 PySide6 子模块
  * 过滤 a.binaries：剔除未链接的 Qt 库家族（3D/Charts/Multimedia/Pdf/Quick3D 等）
  * 过滤 a.datas：剔除 Qt 翻译 .qm（应用自带中文 UI），WebEngine locales 只保留中英
  * strip=True 裁剪符号
依赖依据：ldd libQt6WebEngineCore / libQt6WebEngineWidgets / QtWebEngineProcess
实际链接 Core/Gui/Widgets/Network/DBus/OpenGL/Positioning/PrintSupport/
Qml(Meta/Models/WorkerScript)/Quick/QuickWidgets/WebChannel/WebEngine*，其余剔除。
"""

import os
import re

# ---- 路径（SPECPATH 为 spec 所在目录即 packaging/，项目根为其上一级）----
project_root = os.path.dirname(os.path.abspath(SPECPATH))
icon_dir = os.path.join(project_root, 'icon')

# ---- 数据文件：仅运行期按路径加载的图标（见 main.py base_path 逻辑）----
datas = [
    (icon_dir, 'icon'),
    (os.path.join(project_root, 'pyproject.toml'), '.'),
]

# ---- 隐藏导入 ----
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
    'gui.title_bar',
    'gui.window_resize',
    'profile_manager',
    'tray_manager',
    'pipewire_manager',
    'pipewire_manager_integration',
]

# ---- 排除未用的 Python 模块 ----
excludes = [
    # 科学计算/绘图（与本应用无关）
    'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas', 'PIL', 'cv2',
    # 未用的 PySide6 子模块
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DQuick',
    'PySide6.Qt3DRender',
    'PySide6.QtBluetooth', 'PySide6.QtCharts', 'PySide6.QtConcurrent',
    'PySide6.QtDataVisualization', 'PySide6.QtDesigner', 'PySide6.QtGraphs',
    'PySide6.QtGraphsWidgets', 'PySide6.QtHelp', 'PySide6.QtHttpServer',
    'PySide6.QtLocation', 'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetworkAuth', 'PySide6.QtNfc', 'PySide6.QtPdf',
    'PySide6.QtPdfWidgets', 'PySide6.QtPositioning',
    'PySide6.QtQuick3D', 'PySide6.QtQuickControls2', 'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSensors',
    'PySide6.QtSerialBus', 'PySide6.QtSerialPort', 'PySide6.QtSpatialAudio',
    'PySide6.QtSql', 'PySide6.QtStateMachine', 'PySide6.QtSvg',
    'PySide6.QtSvgWidgets', 'PySide6.QtTest', 'PySide6.QtTextToSpeech',
    'PySide6.QtUiTools', 'PySide6.QtWebSockets',
    'PySide6.QtXml',
]

# ---- 运行时文件过滤 ----

# 未链接的 Qt 库家族（按 libQt6 前缀匹配，命中即剔除）
_DROP_LIB_RE = re.compile(
    r'libQt6('
    r'3D|Bluetooth|Charts|Concurrent|DataVisualization|Designer|EglFS|EglFs'
    r'|Graphs|Help|HttpServer|Labs|Location|Multimedia|NetworkAuth|Nfc'
    r'|Pdf|Quick3D|QuickControls2|QuickDialogs2|QuickEffects|QuickLayouts'
    r'|QuickParticles|QuickShapes|QuickTemplates2|QuickTest'
    r'|RemoteObjects|Scxml|Sensors|SerialBus|SerialPort|SpatialAudio|Sql'
    r'|StateMachine|Svg|Test|TextToSpeech|UiTools|WebSockets|WebView|Xml'
    r')'
)

# 未用的 Qt 插件目录（按目标路径片段匹配）
_DROP_PLUGIN_DIRS = (
    '/plugins/sqldrivers/', '/plugins/sceneparsers/', '/plugins/renderers/',
    '/plugins/assetimporters/', '/plugins/qmltooling/', '/plugins/texttospeech/',
    '/plugins/sensors/', '/plugins/webview/', '/plugins/geometryloaders/',
    '/plugins/geoservices/', '/plugins/position/',
)

# WebEngine 界面语言只保留英文与简/繁中文（应用 UI 为中文，网页自身语言由站点决定）
_KEEP_WEBENGINE_LOCALES = ('en-US.pak', 'zh-CN.pak', 'zh-TW.pak')


def _keep_binary(dest_name: str) -> bool:
    name = os.path.basename(dest_name)
    if _DROP_LIB_RE.search(name):
        return False
    dest = dest_name.replace('\\', '/')
    if any(d in dest for d in _DROP_PLUGIN_DIRS):
        return False
    return True


def _keep_data(dest_name: str) -> bool:
    dest = dest_name.replace('\\', '/')
    if '/Qt/translations/' in dest:
        if '/qtwebengine_locales/' in dest:
            return os.path.basename(dest) in _KEEP_WEBENGINE_LOCALES
        return False  # Qt .qm 翻译全部剔除
    return True


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

# Analysis 后过滤：binaries 剔除未链接 Qt 库/插件，datas 剔除翻译文件
a.binaries = [b for b in a.binaries if _keep_binary(b[0])]
a.datas = [d for d in a.datas if _keep_data(d[0])]

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
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(icon_dir, 'icon_256x256.png'),
)
