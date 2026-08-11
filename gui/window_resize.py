#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无边框窗口八向边缘缩放控制器

依据 协议/自定义标题栏跨项目复用指南.md 实现：
- 递归安装事件过滤器 + ChildAdded 动态追踪，EdgeResizeController(window) 一行安装
  （指南原方案为 QApplication 级过滤器；本项目 PySide6 6.10 + QWebEngineView 下
  应用级 Python 过滤器在向 QQuickWindow 内部对象投递事件时崩溃，故改为递归安装）
- 窗口内缩 6px 热区，四边标志位按位或组合出四角
- 缩放优先交给 WM（startSystemResize），失败时手动 setGeometry 兜底
- hover 时对事件命中的叶子控件 setCursor（覆盖 WebView 等子控件自有光标）
- 最大化/全屏态热区整体禁用
"""

from PySide6.QtCore import Qt, QObject, QEvent, QRect
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget

from logger import get_logger


class EdgeResizeController(QObject):
    """为无边框主窗口补齐八向边缘缩放热区"""

    MARGIN = 6  # 热区宽度（窗口内缩像素）

    def __init__(self, window):
        super().__init__(window)
        self.logger = get_logger("window_resize")
        self._window = window
        # hover 移动事件沿父链上冒至开了 WA_MouseTracking 的主窗口
        window.setAttribute(Qt.WidgetAttribute.WA_MouseTracking, True)

        # 手动兜底缩放状态
        self._resize_edges = None
        self._start_geometry = None
        self._start_global = None

        # 当前设置了缩放光标的叶子控件（离开时需 unsetCursor 还原）
        self._cursor_widget = None

        self._install_recursive(window)

    def _install_recursive(self, widget):
        """递归给部件及其现有子孙装过滤器；后续新增子孙由 ChildAdded 追踪"""
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)

    # ---- 事件过滤 ----

    def eventFilter(self, watched, event):
        # 解释器退出阶段（atexit/GC）事件对象可能已半销毁，静默放行
        try:
            etype = event.type()
        except (RuntimeError, AttributeError):
            return False

        if not isinstance(watched, QWidget):
            return False

        # 动态新增的子控件（如 WebEngine 内部委托部件）：装上过滤器并向下递归
        if etype == QEvent.Type.ChildAdded:
            child = event.child()
            if isinstance(child, QWidget):
                try:
                    self._install_recursive(child)
                except RuntimeError:
                    pass
            return False

        if not self._is_in_window(watched):
            return False

        if etype == QEvent.Type.MouseButtonPress:
            return self._try_start_resize(watched, event)
        elif etype == QEvent.Type.MouseMove:
            if self._resize_edges is not None:
                self._do_manual_resize(event)
                return True
            self._update_hover_cursor(watched, event)
        elif etype == QEvent.Type.MouseButtonRelease:
            if self._resize_edges is not None:
                self._resize_edges = None
                self._start_geometry = None
                self._start_global = None
                return True
        elif etype == QEvent.Type.Leave:
            self._clear_hover_cursor()

        return False

    def _is_in_window(self, widget) -> bool:
        """事件源是否属于主窗口（含其子孙控件）"""
        if widget is self._window:
            return True
        return self._window.isAncestorOf(widget)

    # ---- 热区判定 ----

    def _edges_at(self, watched, event):
        """计算事件位置命中的边缘组合（Qt.Edges），未命中返回 None"""
        if self._window.isMaximized() or self._window.isFullScreen():
            return None  # 最大化/全屏态热区整体禁用

        pos = watched.mapTo(self._window, event.position().toPoint())
        rect = self._window.rect()
        if not rect.contains(pos):
            return None

        edges = Qt.Edge(0)
        if pos.x() < self.MARGIN:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() >= rect.width() - self.MARGIN:
            edges |= Qt.Edge.RightEdge
        if pos.y() < self.MARGIN:
            edges |= Qt.Edge.TopEdge
        elif pos.y() >= rect.height() - self.MARGIN:
            edges |= Qt.Edge.BottomEdge

        return edges if edges != Qt.Edge(0) else None

    # ---- 缩放发起 ----

    def _try_start_resize(self, watched, event) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        edges = self._edges_at(watched, event)
        if edges is None:
            return False

        handle = self._window.windowHandle()
        if handle is not None and handle.startSystemResize(edges):
            # WM 接管；吞掉按下，防边缘文本选择/焦点串扰
            return True

        # 兜底：记录起始几何与全局坐标，MouseMove 里手动 setGeometry
        self._resize_edges = edges
        self._start_geometry = self._window.geometry()
        self._start_global = event.globalPosition().toPoint()
        return True

    def _do_manual_resize(self, event):
        """手动兜底缩放：按边缘组合调整几何，钳制 minimumSize"""
        delta = event.globalPosition().toPoint() - self._start_global
        rect = QRect(self._start_geometry)
        edges = self._resize_edges

        if edges & Qt.Edge.LeftEdge:
            rect.setLeft(rect.left() + delta.x())
        if edges & Qt.Edge.RightEdge:
            rect.setRight(rect.right() + delta.x())
        if edges & Qt.Edge.TopEdge:
            rect.setTop(rect.top() + delta.y())
        if edges & Qt.Edge.BottomEdge:
            rect.setBottom(rect.bottom() + delta.y())

        # 钳制最小尺寸，防布局缩塌
        min_size = self._window.minimumSize()
        if rect.width() < min_size.width():
            if edges & Qt.Edge.LeftEdge:
                rect.setLeft(rect.right() - min_size.width() + 1)
            else:
                rect.setWidth(min_size.width())
        if rect.height() < min_size.height():
            if edges & Qt.Edge.TopEdge:
                rect.setTop(rect.bottom() - min_size.height() + 1)
            else:
                rect.setHeight(min_size.height())

        self._window.setGeometry(rect)

    # ---- hover 光标 ----

    _CURSOR_MAP = {
        Qt.Edge.LeftEdge | Qt.Edge.TopEdge: Qt.CursorShape.SizeFDiagCursor,
        Qt.Edge.RightEdge | Qt.Edge.BottomEdge: Qt.CursorShape.SizeFDiagCursor,
        Qt.Edge.RightEdge | Qt.Edge.TopEdge: Qt.CursorShape.SizeBDiagCursor,
        Qt.Edge.LeftEdge | Qt.Edge.BottomEdge: Qt.CursorShape.SizeBDiagCursor,
    }

    def _cursor_shape_for(self, edges):
        if edges in self._CURSOR_MAP:
            return self._CURSOR_MAP[edges]
        if edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
            return Qt.CursorShape.SizeHorCursor
        return Qt.CursorShape.SizeVerCursor

    def _update_hover_cursor(self, watched, event):
        edges = self._edges_at(watched, event)
        if edges is None:
            self._clear_hover_cursor()
            return

        cursor_shape = self._cursor_shape_for(edges)

        # 对事件命中的叶子控件 setCursor，覆盖 WebView 等子控件自有光标
        if self._cursor_widget is not watched:
            self._clear_hover_cursor()
            self._cursor_widget = watched
        watched.setCursor(QCursor(cursor_shape))  # 边⇄角滑动时同步更新形状

    def _clear_hover_cursor(self):
        if self._cursor_widget is not None:
            try:
                self._cursor_widget.unsetCursor()
            except RuntimeError:
                pass  # 控件可能已销毁
            self._cursor_widget = None
