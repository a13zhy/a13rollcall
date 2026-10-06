"""
A13课堂点名系统 - 插件UI注入工具（增强版）
提供在主程序任何位置添加UI元素、修改布局、添加标签页的完整能力
"""

from PyQt5.QtWidgets import (
    QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QSizePolicy, QMenu, QAction, QLineEdit, QComboBox, QCheckBox,
    QSlider, QProgressBar, QTextEdit, QListWidget, QListWidgetItem,
    QTabWidget, QScrollArea, QGroupBox, QFormLayout, QGridLayout,
    QSplitter, QToolBar, QStatusBar, QDockWidget, QMessageBox,
    QFileDialog, QColorDialog, QFontDialog, QInputDialog, QSpinBox,
    QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit, QCalendarWidget,
    QDial, QLCDNumber, QTableWidget, QTableWidgetItem, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QStackedWidget, QToolBox, QButtonGroup,
    QRadioButton, QPlainTextEdit, QGraphicsView, QGraphicsScene,
    QSystemTrayIcon, QMenuBar, QShortcut
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QObject, QRect
from PyQt5.QtGui import (
    QFont, QIcon, QColor, QPalette, QPixmap, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QFontDatabase, QCursor, QKeySequence
)
import os
import json


class UIInjector:
    """UI注入工具类 - 增强版，支持复杂控件、布局修改、标签页添加"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.injected_elements = []
        self._custom_tabs = []
        self._custom_panels = []

    # ==================== 查找控件 ====================

    def find_widget_by_name(self, name):
        return self.main_window.findChild(QWidget, name)

    def find_all_buttons(self):
        return self.main_window.findChildren(QPushButton)

    def find_button_by_text(self, text):
        for btn in self.find_all_buttons():
            if btn.text() == text:
                return btn
        return None

    def find_all_labels(self):
        return self.main_window.findChildren(QLabel)

    def find_label_by_text(self, text):
        for label in self.find_all_labels():
            if text in label.text():
                return label
        return None

    def find_layout_by_widget(self, widget):
        if widget and widget.parent():
            return widget.parent().layout()
        return None

    def get_all_ui_elements(self, include_layouts=True):
        elements = []
        for widget in self.main_window.findChildren(QWidget):
            elements.append({
                "type": type(widget).__name__,
                "objectName": widget.objectName(),
                "text": getattr(widget, 'text', lambda: '')() if callable(getattr(widget, 'text', None)) else '',
                "visible": widget.isVisible(),
                "enabled": widget.isEnabled(),
                "geometry": widget.geometry().getRect(),
            })
        return elements

    def get_main_window(self):
        return self.main_window

    def get_central_widget(self):
        return self.main_window.centralWidget()

    def get_status_bar(self):
        return self.main_window.statusBar()

    def get_menu_bar(self):
        return self.main_window.menuBar()

    # ==================== 添加按钮（基础） ====================

    def add_button_to_layout(self, layout, text, callback, position=None,
                            style="primary", icon=None, tooltip=None,
                            width=None, height=None):
        btn = QPushButton(text)
        btn.setStyleSheet(self._get_button_style(style))
        if icon:
            btn.setIcon(icon)
        if tooltip:
            btn.setToolTip(tooltip)
        if width:
            btn.setFixedWidth(width)
        if height:
            btn.setFixedHeight(height)
        btn.clicked.connect(callback)
        if position is not None:
            layout.insertWidget(position, btn)
        else:
            layout.addWidget(btn)
        self.injected_elements.append(btn)
        return btn

    def add_button_to_top_bar(self, text, callback, position=None, style="primary",
                              icon=None, tooltip=None, width=100, height=36):
        top_bar = self._get_top_bar()
        if not top_bar:
            return None
        layout = top_bar.layout()
        if not layout:
            layout = QHBoxLayout(top_bar)
        return self.add_button_to_layout(layout, text, callback, position, style, icon, tooltip, width, height)

    def add_button_to_bottom_bar(self, text, callback, position=None, style="ghost",
                                 icon=None, tooltip=None, width=90, height=32):
        bottom_bar = self._get_bottom_bar()
        if not bottom_bar:
            return None
        if isinstance(bottom_bar, QStatusBar):
            btn = QPushButton(text)
            btn.setStyleSheet(self._get_button_style(style))
            if tooltip:
                btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            bottom_bar.addPermanentWidget(btn)
            self.injected_elements.append(btn)
            return btn
        layout = bottom_bar.layout()
        if not layout:
            layout = QHBoxLayout(bottom_bar)
        return self.add_button_to_layout(layout, text, callback, position, style, icon, tooltip, width, height)

    def add_button_to_sidebar(self, text, callback, position=None, style="ghost",
                              icon=None, tooltip=None, width=120, height=40):
        sidebar = self._get_sidebar()
        if not sidebar:
            return None
        layout = sidebar.layout()
        if not layout:
            layout = QVBoxLayout(sidebar)
        return self.add_button_to_layout(layout, text, callback, position, style, icon, tooltip, width, height)

    def add_button_to_draw_area(self, text, callback, position=None, style="primary",
                                 icon=None, tooltip=None, width=120, height=48):
        draw_area = self._get_draw_area()
        if not draw_area:
            return None
        layout = draw_area.layout()
        if not layout:
            layout = QVBoxLayout(draw_area)
        return self.add_button_to_layout(layout, text, callback, position, style, icon, tooltip, width, height)

    def add_button_next_to(self, target_button, text, callback, side="right",
                           style="success", icon=None, tooltip=None, width=None, height=None):
        if isinstance(target_button, str):
            target_button = self.find_button_by_text(target_button)
        if not target_button:
            return None
        parent_layout = self.find_layout_by_widget(target_button)
        if not parent_layout:
            return None
        index = parent_layout.indexOf(target_button)
        position = index + 1 if side == "right" else index
        return self.add_button_to_layout(parent_layout, text, callback, position, style, icon, tooltip, width, height)

    def create_floating_button(self, text, callback, x=20, y=100,
                                size=(100, 40), style="warning", tooltip=None):
        btn = DraggableButton(text, self.main_window)
        btn.setStyleSheet(self._get_button_style(style))
        btn.setGeometry(x, y, size[0], size[1])
        if tooltip:
            btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        btn.show()
        self.injected_elements.append(btn)
        return btn

    # ==================== 添加复杂控件（新增） ====================

    def add_input_to_layout(self, layout, placeholder="", callback=None,
                           position=None, width=200, height=32, echo_normal=True):
        input_box = QLineEdit()
        input_box.setPlaceholderText(placeholder)
        input_box.setFixedHeight(height)
        if width:
            input_box.setFixedWidth(width)
        if not echo_normal:
            input_box.setEchoMode(QLineEdit.Password)
        if callback:
            input_box.textChanged.connect(callback)
        if position is not None:
            layout.insertWidget(position, input_box)
        else:
            layout.addWidget(input_box)
        self.injected_elements.append(input_box)
        return input_box

    def add_combo_to_layout(self, layout, items, callback=None, position=None,
                            width=150, height=32, current_index=0):
        combo = QComboBox()
        combo.addItems(items)
        combo.setFixedHeight(height)
        if width:
            combo.setFixedWidth(width)
        combo.setCurrentIndex(current_index)
        if callback:
            combo.currentIndexChanged.connect(callback)
        if position is not None:
            layout.insertWidget(position, combo)
        else:
            layout.addWidget(combo)
        self.injected_elements.append(combo)
        return combo

    def add_checkbox_to_layout(self, layout, text, callback=None, position=None,
                               checked=False, width=None):
        checkbox = QCheckBox(text)
        checkbox.setChecked(checked)
        if width:
            checkbox.setFixedWidth(width)
        if callback:
            checkbox.stateChanged.connect(callback)
        if position is not None:
            layout.insertWidget(position, checkbox)
        else:
            layout.addWidget(checkbox)
        self.injected_elements.append(checkbox)
        return checkbox

    def add_radio_to_layout(self, layout, text, callback=None, position=None,
                            checked=False, group=None):
        radio = QRadioButton(text)
        radio.setChecked(checked)
        if group:
            group.addButton(radio)
        if callback:
            radio.toggled.connect(callback)
        if position is not None:
            layout.insertWidget(position, radio)
        else:
            layout.addWidget(radio)
        self.injected_elements.append(radio)
        return radio

    def add_slider_to_layout(self, layout, min_val=0, max_val=100, value=50,
                             callback=None, position=None, orientation=Qt.Horizontal, width=200):
        slider = QSlider(orientation)
        slider.setRange(min_val, max_val)
        slider.setValue(value)
        if orientation == Qt.Horizontal and width:
            slider.setFixedWidth(width)
        if callback:
            slider.valueChanged.connect(callback)
        if position is not None:
            layout.insertWidget(position, slider)
        else:
            layout.addWidget(slider)
        self.injected_elements.append(slider)
        return slider

    def add_spinbox_to_layout(self, layout, min_val=0, max_val=100, value=0,
                              callback=None, position=None, width=100, step=1, prefix="", suffix=""):
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(value)
        spinbox.setSingleStep(step)
        spinbox.setFixedWidth(width)
        if prefix:
            spinbox.setPrefix(prefix)
        if suffix:
            spinbox.setSuffix(suffix)
        if callback:
            spinbox.valueChanged.connect(callback)
        if position is not None:
            layout.insertWidget(position, spinbox)
        else:
            layout.addWidget(spinbox)
        self.injected_elements.append(spinbox)
        return spinbox

    def add_progress_to_layout(self, layout, value=0, max_val=100, position=None,
                               width=200, height=20, text_visible=True):
        progress = QProgressBar()
        progress.setRange(0, max_val)
        progress.setValue(value)
        progress.setTextVisible(text_visible)
        progress.setFixedHeight(height)
        if width:
            progress.setFixedWidth(width)
        if position is not None:
            layout.insertWidget(position, progress)
        else:
            layout.addWidget(progress)
        self.injected_elements.append(progress)
        return progress

    def add_list_to_layout(self, layout, items=None, callback=None, position=None,
                           width=200, height=150, selection_mode=QListWidget.SingleSelection):
        list_widget = QListWidget()
        list_widget.setFixedHeight(height)
        if width:
            list_widget.setFixedWidth(width)
        list_widget.setSelectionMode(selection_mode)
        if items:
            list_widget.addItems(items)
        if callback:
            list_widget.itemClicked.connect(callback)
        if position is not None:
            layout.insertWidget(position, list_widget)
        else:
            layout.addWidget(list_widget)
        self.injected_elements.append(list_widget)
        return list_widget

    def add_table_to_layout(self, layout, rows=0, cols=0, headers=None,
                            position=None, width=400, height=200):
        table = QTableWidget(rows, cols)
        if headers:
            table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setFixedHeight(height)
        if width:
            table.setFixedWidth(width)
        if position is not None:
            layout.insertWidget(position, table)
        else:
            layout.addWidget(table)
        self.injected_elements.append(table)
        return table

    def add_textarea_to_layout(self, layout, placeholder="", callback=None,
                               position=None, width=300, height=100, read_only=False):
        textarea = QTextEdit()
        textarea.setPlaceholderText(placeholder)
        textarea.setReadOnly(read_only)
        textarea.setFixedHeight(height)
        if width:
            textarea.setFixedWidth(width)
        if callback:
            textarea.textChanged.connect(callback)
        if position is not None:
            layout.insertWidget(position, textarea)
        else:
            layout.addWidget(textarea)
        self.injected_elements.append(textarea)
        return textarea

    def add_label_to_layout(self, layout, text, style="normal", position=None,
                            width=None, height=None, alignment=None):
        label = QLabel(text)
        label.setStyleSheet(self._get_label_style(style))
        if width:
            label.setFixedWidth(width)
        if height:
            label.setFixedHeight(height)
        if alignment:
            label.setAlignment(alignment)
        if position is not None:
            layout.insertWidget(position, label)
        else:
            layout.addWidget(label)
        self.injected_elements.append(label)
        return label

    def add_separator(self, layout, position=None, orientation=Qt.Horizontal):
        line = QFrame()
        if orientation == Qt.Horizontal:
            line.setFrameShape(QFrame.HLine)
        else:
            line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        if position is not None:
            layout.insertWidget(position, line)
        else:
            layout.addWidget(line)
        self.injected_elements.append(line)
        return line

    def add_groupbox(self, layout, title, position=None):
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        if position is not None:
            layout.insertWidget(position, group)
        else:
            layout.addWidget(group)
        self.injected_elements.append(group)
        return group, group_layout

    def add_custom_widget(self, layout, widget, position=None):
        if position is not None:
            layout.insertWidget(position, widget)
        else:
            layout.addWidget(widget)
        self.injected_elements.append(widget)
        return widget

    # ==================== 添加标签页/面板（新增） ====================

    def add_tab_to_main(self, tab_title, icon=None):
        central = self.get_central_widget()
        if not central:
            return None
        tab_widget = central.findChild(QTabWidget)
        if not tab_widget:
            tab_widget = QTabWidget(central)
            layout = central.layout()
            if layout:
                layout.addWidget(tab_widget)
            else:
                new_layout = QVBoxLayout(central)
                new_layout.addWidget(tab_widget)
        new_tab = QWidget()
        tab_layout = QVBoxLayout(new_tab)
        if icon:
            index = tab_widget.addTab(new_tab, icon, tab_title)
        else:
            index = tab_widget.addTab(new_tab, tab_title)
        self._custom_tabs.append((tab_widget, new_tab, index))
        self.injected_elements.append(new_tab)
        return new_tab, tab_layout, index

    def add_panel_to_main(self, title, area=Qt.LeftDockWidgetArea, floating=False):
        dock = QDockWidget(title, self.main_window)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        dock.setWidget(content)
        self.main_window.addDockWidget(area, dock)
        if floating:
            dock.setFloating(True)
        self._custom_panels.append(dock)
        self.injected_elements.append(dock)
        return dock, content, content_layout

    def add_toolbar(self, title, area=Qt.TopToolBarArea):
        toolbar = QToolBar(title, self.main_window)
        toolbar.setObjectName(f"plugin_toolbar_{title}")
        self.main_window.addToolBar(area, toolbar)
        self.injected_elements.append(toolbar)
        return toolbar

    def add_status_widget(self, widget, permanent=True):
        status_bar = self.get_status_bar()
        if not status_bar:
            return None
        if permanent:
            status_bar.addPermanentWidget(widget)
        else:
            status_bar.addWidget(widget)
        self.injected_elements.append(widget)
        return widget

    # ==================== 菜单和快捷键（新增） ====================

    def add_menu_action(self, menu, text, callback, icon=None, shortcut=None, tooltip=None):
        action = QAction(text, self.main_window)
        if icon:
            action.setIcon(icon)
        if shortcut:
            action.setShortcut(shortcut)
        if tooltip:
            action.setToolTip(tooltip)
        action.triggered.connect(callback)
        menu.addAction(action)
        self.injected_elements.append(action)
        return action

    def add_menu(self, menu_bar, title, icon=None):
        menu = menu_bar.addMenu(title)
        if icon:
            menu.setIcon(icon)
        self.injected_elements.append(menu)
        return menu

    def add_shortcut(self, key_sequence, callback, context=Qt.WindowShortcut):
        shortcut = QShortcut(QKeySequence(key_sequence), self.main_window)
        shortcut.setContext(context)
        shortcut.activated.connect(callback)
        self.injected_elements.append(shortcut)
        return shortcut

    # ==================== 修改现有控件 ====================

    def modify_button(self, button, text=None, callback=None, style=None,
                      icon=None, tooltip=None, enabled=None, visible=None):
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
        if enabled is not None:
            button.setEnabled(enabled)
        if visible is not None:
            button.setVisible(visible)
        return True

    def modify_label(self, label, text=None, style=None, color=None, font_size=None):
        if isinstance(label, str):
            label = self.find_label_by_text(label)
        if not label:
            return False
        if text is not None:
            label.setText(text)
        if style is not None:
            label.setStyleSheet(self._get_label_style(style))
        if color is not None:
            label.setStyleSheet(f"color: {color};")
        if font_size is not None:
            font = label.font()
            font.setPointSize(font_size)
            label.setFont(font)
        return True

    def hide_button(self, button):
        return self.modify_button(button, visible=False)

    def show_button(self, button):
        return self.modify_button(button, visible=True)

    def disable_button(self, button):
        return self.modify_button(button, enabled=False)

    def enable_button(self, button):
        return self.modify_button(button, enabled=True)

    # ==================== 布局操作（新增） ====================

    def get_layout_of_widget(self, widget):
        if widget and widget.parent():
            return widget.parent().layout()
        return None

    def remove_widget_from_layout(self, layout, widget):
        if layout and widget:
            layout.removeWidget(widget)
            widget.setParent(None)
            return True
        return False

    def move_widget_in_layout(self, layout, widget, new_position):
        if not layout or not widget:
            return False
        current_index = layout.indexOf(widget)
        if current_index < 0:
            return False
        layout.removeWidget(widget)
        layout.insertWidget(new_position, widget)
        return True

    def swap_widgets_in_layout(self, layout, widget1, widget2):
        if not layout or not widget1 or not widget2:
            return False
        idx1 = layout.indexOf(widget1)
        idx2 = layout.indexOf(widget2)
        if idx1 < 0 or idx2 < 0:
            return False
        layout.removeWidget(widget1)
        layout.removeWidget(widget2)
        min_idx = min(idx1, idx2)
        layout.insertWidget(min_idx, widget2)
        layout.insertWidget(min_idx + 1, widget1)
        return True

    def insert_layout(self, parent_layout, position, orientation="vertical"):
        if orientation == "vertical":
            new_layout = QVBoxLayout()
        else:
            new_layout = QHBoxLayout()
        parent_layout.insertLayout(position, new_layout)
        return new_layout

    # ==================== 对话框和提示（新增） ====================

    def show_message_box(self, title, message, icon=QMessageBox.Information, buttons=QMessageBox.Ok):
        msg_box = QMessageBox(self.main_window)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(buttons)
        return msg_box.exec_()

    def show_input_dialog(self, title, label, default_text="", mode=QLineEdit.Normal):
        text, ok = QInputDialog.getText(self.main_window, title, label, mode, default_text)
        return text if ok else None

    def show_file_dialog(self, title, filter="所有文件 (*.*)", directory=""):
        file_path, _ = QFileDialog.getOpenFileName(self.main_window, title, directory, filter)
        return file_path

    def show_save_dialog(self, title, filter="所有文件 (*.*)", directory=""):
        file_path, _ = QFileDialog.getSaveFileName(self.main_window, title, directory, filter)
        return file_path

    def show_color_dialog(self, initial_color=QColor(255, 255, 255)):
        color = QColorDialog.getColor(initial_color, self.main_window)
        return color if color.isValid() else None

    def show_font_dialog(self, initial_font=None):
        if initial_font is None:
            initial_font = QFont()
        font, ok = QFontDialog.getFont(initial_font, self.main_window)
        return font if ok else None

    # ==================== 样式和主题（新增） ====================

    def get_app_style(self):
        return self.main_window.styleSheet()

    def set_app_style(self, style_sheet):
        self.main_window.setStyleSheet(style_sheet)

    def append_app_style(self, style_sheet):
        current = self.main_window.styleSheet()
        self.main_window.setStyleSheet(current + "\n" + style_sheet)

    def set_widget_style(self, widget, style_sheet):
        if widget:
            widget.setStyleSheet(style_sheet)

    def get_palette(self):
        return self.main_window.palette()

    def set_palette_color(self, role, color, group=QPalette.Active):
        palette = self.main_window.palette()
        palette.setColor(group, role, QColor(color))
        self.main_window.setPalette(palette)

    # ==================== 窗口操作（新增） ====================

    def set_window_title(self, title):
        self.main_window.setWindowTitle(title)

    def get_window_title(self):
        return self.main_window.windowTitle()

    def set_window_size(self, width, height):
        self.main_window.resize(width, height)

    def get_window_size(self):
        return self.main_window.size()

    def set_window_position(self, x, y):
        self.main_window.move(x, y)

    def get_window_position(self):
        return self.main_window.pos()

    def minimize_window(self):
        self.main_window.showMinimized()

    def maximize_window(self):
        self.main_window.showMaximized()

    def restore_window(self):
        self.main_window.showNormal()

    def set_window_opacity(self, opacity):
        self.main_window.setWindowOpacity(opacity)

    def set_window_on_top(self, on_top=True):
        flags = self.main_window.windowFlags()
        if on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.main_window.setWindowFlags(flags)
        self.main_window.show()

    # ==================== 定时器和动画（新增） ====================

    def create_timer(self, interval, callback, single_shot=False):
        timer = QTimer(self.main_window)
        timer.setInterval(interval)
        timer.setSingleShot(single_shot)
        timer.timeout.connect(callback)
        self.injected_elements.append(timer)
        return timer

    def start_timer(self, timer):
        if timer:
            timer.start()

    def stop_timer(self, timer):
        if timer:
            timer.stop()

    def delayed_call(self, milliseconds, callback):
        QTimer.singleShot(milliseconds, callback)

    # ==================== 资源管理（新增） ====================

    def load_icon(self, path):
        if os.path.exists(path):
            return QIcon(path)
        return None

    def load_pixmap(self, path):
        if os.path.exists(path):
            return QPixmap(path)
        return None

    def load_font(self, path):
        if os.path.exists(path):
            font_id = QFontDatabase.addApplicationFont(path)
            if font_id >= 0:
                return QFontDatabase.applicationFontFamilies(font_id)[0]
        return None

    def create_color(self, r, g, b, a=255):
        return QColor(r, g, b, a)

    def create_gradient(self, x1, y1, x2, y2, color1, color2):
        gradient = QLinearGradient(x1, y1, x2, y2)
        gradient.setColorAt(0, QColor(color1))
        gradient.setColorAt(1, QColor(color2))
        return gradient

    # ==================== 内部辅助方法 ====================

    def _get_top_bar(self):
        for name in ["top_bar", "title_bar", "header", "top_frame"]:
            widget = self.find_widget_by_name(name)
            if widget:
                return widget
        return None

    def _get_bottom_bar(self):
        from PyQt5.QtWidgets import QStatusBar
        for name in ["status_bar", "bottom_bar", "statusBar", "footer"]:
            widget = self.find_widget_by_name(name)
            if widget:
                return widget
        status_bar = self.main_window.findChild(QStatusBar)
        if status_bar:
            return status_bar
        return None

    def _get_sidebar(self):
        for name in ["sidebar", "side_panel", "left_panel", "nav_panel"]:
            widget = self.find_widget_by_name(name)
            if widget:
                return widget
        return None

    def _get_draw_area(self):
        for name in ["draw_area", "draw_widget", "central_area", "main_area"]:
            widget = self.find_widget_by_name(name)
            if widget:
                return widget
        return None

    def _get_button_style(self, style):
        styles = {
            "primary": """
                QPushButton { background: #0067c0; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 13px; }
                QPushButton:hover { background: #005a9e; }
                QPushButton:pressed { background: #004578; }
                QPushButton:disabled { background: #cccccc; color: #999999; }
            """,
            "success": """
                QPushButton { background: #107c10; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 13px; }
                QPushButton:hover { background: #0e6c0e; }
                QPushButton:pressed { background: #0a5c0a; }
            """,
            "warning": """
                QPushButton { background: #ca5010; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 13px; }
                QPushButton:hover { background: #b04810; }
            """,
            "danger": """
                QPushButton { background: #c42b1c; color: white; border: none;
                    border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 13px; }
                QPushButton:hover { background: #a82318; }
            """,
            "ghost": """
                QPushButton { background: transparent; color: #0067c0; border: 1px solid #0067c0;
                    border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 13px; }
                QPushButton:hover { background: #e5f1fb; }
            """,
            "small": """
                QPushButton { background: #f0f0f0; color: #333; border: 1px solid #d1d1d1;
                    border-radius: 4px; padding: 4px 10px; font-size: 11px; }
                QPushButton:hover { background: #e0e0e0; }
            """,
        }
        return styles.get(style, styles["primary"])

    def _get_label_style(self, style):
        styles = {
            "normal": "color: #333333; font-size: 13px;",
            "title": "color: #1a1a1a; font-size: 18px; font-weight: 700;",
            "subtitle": "color: #555555; font-size: 14px; font-weight: 600;",
            "hint": "color: #999999; font-size: 12px;",
            "success": "color: #107c10; font-size: 13px; font-weight: 600;",
            "warning": "color: #ca5010; font-size: 13px; font-weight: 600;",
            "danger": "color: #c42b1c; font-size: 13px; font-weight: 600;",
        }
        return styles.get(style, styles["normal"])

    # ==================== 清理 ====================

    def cleanup(self):
        for element in self.injected_elements:
            try:
                if hasattr(element, 'deleteLater'):
                    element.deleteLater()
                elif hasattr(element, 'close'):
                    element.close()
            except Exception:
                pass
        self.injected_elements = []
        self._custom_tabs = []
        self._custom_panels = []


class DraggableButton(QPushButton):
    """可拖动的按钮类"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._drag_position = None
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_position:
            self.move(event.globalPos() - self._drag_position)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_position = None
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(event)
