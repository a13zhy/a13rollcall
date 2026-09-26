"""
A13课堂点名系统 - 插件UI注入工具
提供在主程序任何位置添加按钮、修改UI的便捷方法
"""

from PyQt5.QtWidgets import (QPushButton, QWidget, QHBoxLayout, QVBoxLayout,
                             QLabel, QFrame, QSizePolicy, QMenu, QAction)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon


class UIInjector:
    """UI注入工具类 - 帮助插件在主程序任何位置添加UI元素"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.injected_elements = []

    def find_widget_by_name(self, name):
        """按objectName查找控件"""
        return self.main_window.findChild(QWidget, name)

    def find_all_buttons(self):
        """查找所有按钮"""
        return self.main_window.findChildren(QPushButton)

    def find_button_by_text(self, text):
        """按文字查找按钮"""
        for btn in self.find_all_buttons():
            if btn.text() == text:
                return btn
        return None

    def add_button_to_layout(self, layout, text, callback, position=None,
                            style="primary", icon=None, tooltip=None,
                            width=None, height=None):
        """
        向指定布局添加按钮

        Args:
            layout: 目标布局 (QHBoxLayout/QVBoxLayout等)
            text: 按钮文字
            callback: 点击回调函数
            position: 插入位置 (None=末尾, 0=开头, 或指定索引)
            style: 按钮样式 (primary/success/warning/danger/ghost)
            icon: 图标 (QIcon或None)
            tooltip: 提示文字
            width: 按钮宽度
            height: 按钮高度

        Returns:
            QPushButton: 创建的按钮对象
        """
        btn = QPushButton(text)
        btn.clicked.connect(callback)

        if icon:
            btn.setIcon(icon)
        if tooltip:
            btn.setToolTip(tooltip)
        if width:
            btn.setFixedWidth(width)
        if height:
            btn.setFixedHeight(height)

        btn.setStyleSheet(self._get_button_style(style))
        btn.setCursor(Qt.PointingHandCursor)

        if position is not None:
            layout.insertWidget(position, btn)
        else:
            layout.addWidget(btn)

        self.injected_elements.append(btn)
        return btn

    def add_button_to_top_bar(self, text, callback, position=None, **kwargs):
        """
        向顶部栏添加按钮

        Args:
            text: 按钮文字
            callback: 点击回调
            position: 插入位置
            **kwargs: 其他参数 (style, icon, tooltip, width, height)

        Returns:
            QPushButton: 按钮对象
        """
        top_bar = self._get_top_bar()
        if not top_bar:
            return None

        layout = top_bar.layout()
        if not layout:
            layout = QHBoxLayout(top_bar)

        return self.add_button_to_layout(layout, text, callback, position, **kwargs)

    def add_button_to_bottom_bar(self, text, callback, position=None, **kwargs):
        """
        向底部状态栏添加按钮

        Returns:
            QPushButton: 按钮对象
        """
        bottom_bar = self._get_bottom_bar()
        if not bottom_bar:
            return None

        layout = bottom_bar.layout()
        if not layout:
            layout = QHBoxLayout(bottom_bar)

        return self.add_button_to_layout(layout, text, callback, position, **kwargs)

    def add_button_to_sidebar(self, text, callback, position=None, **kwargs):
        """
        向左侧边栏添加按钮

        Returns:
            QPushButton: 按钮对象
        """
        sidebar = self._get_sidebar()
        if not sidebar:
            return None

        layout = sidebar.layout()
        if not layout:
            layout = QVBoxLayout(sidebar)

        kwargs.setdefault("width", 120)
        return self.add_button_to_layout(layout, text, callback, position, **kwargs)

    def add_button_to_draw_area(self, text, callback, position=None, **kwargs):
        """
        向抽取区域添加按钮

        Returns:
            QPushButton: 按钮对象
        """
        draw_area = self._get_draw_area()
        if not draw_area:
            return None

        layout = draw_area.layout()
        if not layout:
            layout = QVBoxLayout(draw_area)

        return self.add_button_to_layout(layout, text, callback, position, **kwargs)

    def add_button_next_to(self, target_button, text, callback, side="right", **kwargs):
        """
        在指定按钮旁边添加按钮

        Args:
            target_button: 目标按钮 (QPushButton或按钮文字)
            text: 新按钮文字
            callback: 点击回调
            side: 位置 (right/left)
            **kwargs: 其他参数

        Returns:
            QPushButton: 新按钮对象
        """
        if isinstance(target_button, str):
            target_button = self.find_button_by_text(target_button)

        if not target_button:
            return None

        parent_layout = target_button.parent().layout()
        if not parent_layout:
            return None

        index = parent_layout.indexOf(target_button)
        if index < 0:
            return None

        position = index + 1 if side == "right" else index
        return self.add_button_to_layout(parent_layout, text, callback, position, **kwargs)

    def add_separator(self, layout, position=None):
        """
        向布局添加分隔线

        Args:
            layout: 目标布局
            position: 插入位置

        Returns:
            QFrame: 分隔线对象
        """
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet("color: #e0e0e0;")
        line.setFixedWidth(1)

        if position is not None:
            layout.insertWidget(position, line)
        else:
            layout.addWidget(line)

        self.injected_elements.append(line)
        return line

    def add_label(self, layout, text, position=None, style="normal", **kwargs):
        """
        向布局添加标签

        Args:
            layout: 目标布局
            text: 标签文字
            position: 插入位置
            style: 样式 (normal/title/subtitle/hint)

        Returns:
            QLabel: 标签对象
        """
        label = QLabel(text)
        label.setStyleSheet(self._get_label_style(style))

        if kwargs.get("alignment"):
            label.setAlignment(kwargs["alignment"])
        if kwargs.get("wordWrap"):
            label.setWordWrap(True)

        if position is not None:
            layout.insertWidget(position, label)
        else:
            layout.addWidget(label)

        self.injected_elements.append(label)
        return label

    def add_custom_widget(self, layout, widget, position=None):
        """
        向布局添加自定义控件

        Args:
            layout: 目标布局
            widget: 自定义控件
            position: 插入位置

        Returns:
            QWidget: 控件对象
        """
        if position is not None:
            layout.insertWidget(position, widget)
        else:
            layout.addWidget(widget)

        self.injected_elements.append(widget)
        return widget

    def modify_button(self, button, text=None, callback=None, style=None,
                     icon=None, tooltip=None):
        """
        修改现有按钮

        Args:
            button: 按钮对象或按钮文字
            text: 新文字 (None=不修改)
            callback: 新回调 (None=不修改, 会先断开旧连接)
            style: 新样式
            icon: 新图标
            tooltip: 新提示
        """
        if isinstance(button, str):
            button = self.find_button_by_text(button)

        if not button:
            return False

        if text is not None:
            button.setText(text)
        if callback is not None:
            try:
                button.clicked.disconnect()
            except Exception:
                pass
            button.clicked.connect(callback)
        if style is not None:
            button.setStyleSheet(self._get_button_style(style))
        if icon is not None:
            button.setIcon(icon)
        if tooltip is not None:
            button.setToolTip(tooltip)

        return True

    def hide_button(self, button):
        """隐藏按钮"""
        if isinstance(button, str):
            button = self.find_button_by_text(button)
        if button:
            button.hide()
            return True
        return False

    def show_button(self, button):
        """显示按钮"""
        if isinstance(button, str):
            button = self.find_button_by_text(button)
        if button:
            button.show()
            return True
        return False

    def add_menu_action(self, menu, text, callback, icon=None, shortcut=None):
        """
        向菜单添加菜单项

        Args:
            menu: QMenu对象
            text: 菜单项文字
            callback: 点击回调
            icon: 图标
            shortcut: 快捷键

        Returns:
            QAction: 菜单项对象
        """
        action = QAction(text, self.main_window)
        action.triggered.connect(callback)

        if icon:
            action.setIcon(icon)
        if shortcut:
            action.setShortcut(shortcut)

        menu.addAction(action)
        self.injected_elements.append(action)
        return action

    def create_floating_button(self, text, callback, x=100, y=100,
                              size=(80, 40), style="primary"):
        """
        创建悬浮按钮（可拖动）

        Args:
            text: 按钮文字
            callback: 点击回调
            x, y: 初始位置
            size: 按钮大小 (width, height)
            style: 按钮样式

        Returns:
            QPushButton: 悬浮按钮对象
        """
        btn = DraggableButton(text, self.main_window)
        btn.setFixedSize(*size)
        btn.move(x, y)
        btn.setStyleSheet(self._get_button_style(style))
        btn.clicked.connect(callback)
        btn.show()
        btn.raise_()

        self.injected_elements.append(btn)
        return btn

    def get_all_ui_elements(self):
        """获取所有UI元素的摘要（调试用）"""
        elements = []
        for btn in self.find_all_buttons():
            elements.append({
                "type": "QPushButton",
                "text": btn.text(),
                "objectName": btn.objectName(),
                "visible": btn.isVisible()
            })
        for label in self.main_window.findChildren(QLabel):
            elements.append({
                "type": "QLabel",
                "text": label.text()[:50],
                "objectName": label.objectName()
            })
        return elements

    def cleanup(self):
        """清理所有注入的元素"""
        for element in self.injected_elements:
            try:
                if hasattr(element, 'deleteLater'):
                    element.deleteLater()
                elif hasattr(element, 'setParent'):
                    element.setParent(None)
            except Exception:
                pass
        self.injected_elements.clear()

    def _get_top_bar(self):
        """获取顶部栏"""
        for name in ["top_bar", "title_bar", "header", "topBar"]:
            widget = self.find_widget_by_name(name)
            if widget:
                return widget
        # 尝试查找第一个QFrame作为顶部栏
        for frame in self.main_window.findChildren(QFrame):
            if frame.height() < 80 and frame.y() < 50:
                return frame
        return None

    def _get_bottom_bar(self):
        """获取底部状态栏"""
        from PyQt5.QtWidgets import QStatusBar
        for name in ["status_bar", "bottom_bar", "statusBar", "footer"]:
            widget = self.find_widget_by_name(name)
            if widget:
                return widget
        # 尝试查找QStatusBar
        status_bar = self.main_window.findChild(QStatusBar)
        if status_bar:
            return status_bar
        return None

    def _get_sidebar(self):
        """获取左侧边栏"""
        for name in ["sidebar", "side_bar", "left_panel", "leftBar"]:
            widget = self.find_widget_by_name(name)
            if widget:
                return widget
        return None

    def _get_draw_area(self):
        """获取抽取区域"""
        for name in ["draw_area", "drawArea", "center_widget", "centralWidget"]:
            widget = self.find_widget_by_name(name)
            if widget:
                return widget
        return self.main_window.centralWidget()

    def _get_button_style(self, style):
        """获取按钮样式"""
        styles = {
            "primary": """
                QPushButton {
                    background: #0067c0; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px;
                    font-size: 13px; font-weight: 600;
                }
                QPushButton:hover { background: #005a9e; }
                QPushButton:pressed { background: #004578; }
            """,
            "success": """
                QPushButton {
                    background: #107c10; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px;
                    font-size: 13px; font-weight: 600;
                }
                QPushButton:hover { background: #0e6c0e; }
            """,
            "warning": """
                QPushButton {
                    background: #ff8c00; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px;
                    font-size: 13px; font-weight: 600;
                }
                QPushButton:hover { background: #e67e00; }
            """,
            "danger": """
                QPushButton {
                    background: #d13438; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px;
                    font-size: 13px; font-weight: 600;
                }
                QPushButton:hover { background: #a8282c; }
            """,
            "ghost": """
                QPushButton {
                    background: transparent; color: #333; border: 1px solid #ccc;
                    border-radius: 6px; padding: 8px 16px;
                    font-size: 13px; font-weight: 500;
                }
                QPushButton:hover { background: #f0f0f0; border-color: #0067c0; color: #0067c0; }
            """,
            "small": """
                QPushButton {
                    background: #f0f0f0; color: #333; border: none;
                    border-radius: 4px; padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover { background: #e0e0e0; }
            """
        }
        return styles.get(style, styles["primary"])

    def _get_label_style(self, style):
        """获取标签样式"""
        styles = {
            "normal": "color: #333; font-size: 13px;",
            "title": "color: #0067c0; font-size: 18px; font-weight: 700;",
            "subtitle": "color: #666; font-size: 14px; font-weight: 600;",
            "hint": "color: #999; font-size: 11px;",
            "success": "color: #107c10; font-size: 13px; font-weight: 600;",
            "warning": "color: #ff8c00; font-size: 13px; font-weight: 600;",
            "danger": "color: #d13438; font-size: 13px; font-weight: 600;",
        }
        return styles.get(style, styles["normal"])


class DraggableButton(QPushButton):
    """可拖动的按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.dragging = False
        self.drag_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        super().mouseReleaseEvent(event)


__all__ = ['UIInjector', 'DraggableButton']
