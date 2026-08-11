#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自绘标题栏部件（无边框窗口方案）

依据 协议/自定义标题栏跨项目复用指南.md 实现：
- 左侧 Logo + 固定标题，右侧最小化/最大化/关闭三按钮
- 拖拽移动优先交给 WM（startSystemMove），失败时手动兜底
- 双击切换最大化，最大化态拖拽按比例还原并跟随光标
- 本项目无主题体系，配色使用模块级常量，预留 apply_theme 接口
"""

import os
import sys

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton

from logger import get_logger


TITLE_BAR_HEIGHT = 32

# 配色令牌包（bg/text/hover/close_hover），本项目固定一组
TITLE_BAR_COLORS = {
    "bg": "#c20c0c",            # 网易云品牌红
    "text": "#ffffff",
    "hover": "#a70b0b",
    "close_hover": "#e81123",   # 跨主题通用警示红
}

_QSS_TEMPLATE = """
TitleBar {{
    background: {bg};
}}
TitleBar QLabel {{
    color: {text};
    background: transparent;
}}
TitleBar QToolButton {{
    background: transparent;
    border: none;
    color: {text};
    font-size: 14px;
}}
TitleBar QToolButton:hover {{
    background: {hover};
}}
TitleBar QToolButton#closeButton:hover {{
    background: {close_hover};
    color: #ffffff;
}}
"""


def _resource_path(relative: str) -> str:
    """兼容 PyInstaller 打包的资源路径"""
    base_path = getattr(sys, "_MEIPASS", os.getcwd())
    return os.path.join(base_path, relative)


class TitleBar(QWidget):
    """自绘标题栏：Logo + 标题 + 三按钮，支持拖拽/双击/最大化图标同步"""

    def __init__(self, window):
        super().__init__(window)
        self.logger = get_logger("title_bar")
        self._window = window
        self._drag_offset = None  # 手动兜底拖拽偏移

        self.setFixedHeight(TITLE_BAR_HEIGHT)
        # QSS background 对 QWidget 需显式开启样式绘制，否则背景色不生效
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._build_ui()
        self.apply_theme(TITLE_BAR_COLORS)

        # 监听窗口状态变化，同步最大化按钮图标（任务栏还原、WM 快捷键等外部途径）
        window.installEventFilter(self)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(6)

        # Logo（PNG）
        self._logo_label = QLabel(self)
        icon_path = _resource_path("icon/icon_32x32.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(
                20, 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._logo_label.setPixmap(pixmap)
        else:
            self.logger.warning(f"标题栏Logo文件不存在: {icon_path}")
        layout.addWidget(self._logo_label)

        # 固定标题（不跟随网页标题，网页标题仍走 setWindowTitle 供任务栏使用）
        self._title_label = QLabel("网易云音乐", self)
        layout.addWidget(self._title_label)

        layout.addStretch(1)

        # 三按钮：定宽 46、NoFocus
        self._min_button = self._make_button("—", "最小化")
        self._max_button = self._make_button("□", "最大化/还原")
        self._close_button = self._make_button("×", "关闭")
        self._close_button.setObjectName("closeButton")

        self._min_button.clicked.connect(self._window.showMinimized)
        self._max_button.clicked.connect(self.toggle_maximize)
        # 直连 close()，走主窗口既有 closeEvent（托盘最小化/确认弹窗逻辑不变）
        self._close_button.clicked.connect(self._window.close)

        layout.addWidget(self._min_button)
        layout.addWidget(self._max_button)
        layout.addWidget(self._close_button)

    def _make_button(self, text: str, tooltip: str) -> QToolButton:
        button = QToolButton(self)
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(46, TITLE_BAR_HEIGHT)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setCursor(Qt.CursorShape.ArrowCursor)
        return button

    def apply_theme(self, colors: dict):
        """按配色令牌包重建内联 QSS（本项目暂固定一组，预留主题接线口）"""
        self.setStyleSheet(_QSS_TEMPLATE.format(**colors))

    # ---- 最大化 ----

    def toggle_maximize(self):
        """最大化/还原统一入口（按钮与双击共用）"""
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def _sync_max_button(self):
        self._max_button.setText("❐" if self._window.isMaximized() else "□")

    def eventFilter(self, watched, event):
        if watched is self._window and event.type() == QEvent.Type.WindowStateChange:
            self._sync_max_button()
        return super().eventFilter(watched, event)

    # ---- 拖拽移动 ----

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        window = self._window
        if window.isMaximized():
            self._restore_for_drag(event)

        handle = window.windowHandle()
        if handle is not None and handle.startSystemMove():
            return  # WM 接管

        # 兜底：WM 不支持时记录偏移，mouseMove 里手动跟随
        self._drag_offset = (
            event.globalPosition().toPoint() - window.frameGeometry().topLeft()
        )

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_offset)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()
            return
        super().mouseDoubleClickEvent(event)

    def _restore_for_drag(self, event):
        """最大化态按下：按比例还原窗口，使光标接续拖拽位置不变"""
        window = self._window
        ratio = event.position().x() / max(self.width(), 1)
        window.showNormal()
        new_x = event.globalPosition().x() - ratio * window.width()
        new_y = event.globalPosition().y() - TITLE_BAR_HEIGHT // 2
        window.move(int(new_x), int(new_y))
