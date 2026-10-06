# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 可视化页面编辑器
支持拖拽模块、实时预览、属性编辑
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox,
                             QListWidget, QListWidgetItem, QFrame, QScrollArea,
                             QSizePolicy, QMenu, QAction, QInputDialog, QColorDialog,
                             QSlider, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QDrag, QPixmap, QPainter, QBrush, QPen


MODULE_TYPES = [
    {"type": "switch", "name": "开关", "icon": "🔘", "desc": "布尔值开关", "default": True},
    {"type": "input", "name": "文本输入", "icon": "📝", "desc": "单行文本输入框", "default": ""},
    {"type": "textarea", "name": "多行文本", "icon": "📄", "desc": "多行文本输入框", "default": ""},
    {"type": "number", "name": "数字输入", "icon": "🔢", "desc": "数字输入框", "default": 0},
    {"type": "slider", "name": "滑块", "icon": "🎚️", "desc": "滑块选择器", "default": 50},
    {"type": "select", "name": "下拉选择", "icon": "📋", "desc": "下拉选择框", "default": ""},
    {"type": "color", "name": "颜色选择", "icon": "🎨", "desc": "颜色选择器", "default": "#0067c0"},
    {"type": "button", "name": "按钮", "icon": "🔘", "desc": "操作按钮", "default": ""},
    {"type": "divider", "name": "分割线", "icon": "➖", "desc": "视觉分割线", "default": ""},
    {"type": "info", "name": "信息文本", "icon": "ℹ️", "desc": "只读说明文本", "default": ""},
]


class DraggableModuleItem(QFrame):
    """可拖拽的模块项（工具箱中的）"""

    def __init__(self, module_type, parent=None):
        super().__init__(parent)
        self.module_type = module_type
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 2px solid #0067c0;
                background: #f0f7ff;
            }
        """)
        self.setCursor(Qt.OpenHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        icon_label = QLabel(module_type["icon"])
        icon_label.setStyleSheet("font-size: 20px;")
        icon_label.setFixedWidth(32)
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        name_label = QLabel(module_type["name"])
        name_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #333;")
        text_layout.addWidget(name_label)

        desc_label = QLabel(module_type["desc"])
        desc_label.setStyleSheet("font-size: 10px; color: #999;")
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"module:{self.module_type['type']}")
        mime_data.setData("application/x-a13-module", self.module_type["type"].encode())
        drag.setMimeData(mime_data)

        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        drag.exec_(Qt.CopyAction | Qt.MoveAction)


class DroppedModuleItem(QFrame):
    """已放置的模块项（编辑区域中的）"""

    delete_clicked = pyqtSignal(int)
    edit_clicked = pyqtSignal(int)
    move_up = pyqtSignal(int)
    move_down = pyqtSignal(int)

    def __init__(self, index, module_data, parent=None):
        super().__init__(parent)
        self.index = index
        self.module_data = module_data
        self.setFixedHeight(64)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 2px solid #0067c0;
            }
        """)
        self.setCursor(Qt.SizeAllCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        drag_handle = QLabel("⋮⋮")
        drag_handle.setStyleSheet("font-size: 16px; color: #ccc;")
        drag_handle.setFixedWidth(24)
        layout.addWidget(drag_handle)

        module_type = next((m for m in MODULE_TYPES if m["type"] == module_data.get("type", "input")), MODULE_TYPES[1])
        icon_label = QLabel(module_type["icon"])
        icon_label.setStyleSheet("font-size: 22px;")
        icon_label.setFixedWidth(32)
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        key_label = QLabel(module_data.get("key", "未设置key"))
        key_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #333;")
        text_layout.addWidget(key_label)

        type_label = QLabel(f"{module_type['name']} - {module_data.get('label', '未设置标签')}")
        type_label.setStyleSheet("font-size: 10px; color: #999;")
        text_layout.addWidget(type_label)

        layout.addLayout(text_layout, 1)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        up_btn = QPushButton("↑")
        up_btn.setFixedSize(28, 24)
        up_btn.setStyleSheet("QPushButton { background: #f0f0f0; border: none; border-radius: 4px; font-size: 12px; } QPushButton:hover { background: #e0e0e0; }")
        up_btn.clicked.connect(lambda: self.move_up.emit(self.index))
        btn_layout.addWidget(up_btn)

        down_btn = QPushButton("↓")
        down_btn.setFixedSize(28, 24)
        down_btn.setStyleSheet("QPushButton { background: #f0f0f0; border: none; border-radius: 4px; font-size: 12px; } QPushButton:hover { background: #e0e0e0; }")
        down_btn.clicked.connect(lambda: self.move_down.emit(self.index))
        btn_layout.addWidget(down_btn)

        layout.addLayout(btn_layout)

        edit_btn = QPushButton("编辑")
        edit_btn.setFixedSize(56, 32)
        edit_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: #1a76c8; }")
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.index))
        layout.addWidget(edit_btn)

        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(56, 32)
        delete_btn.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: #a02010; }")
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.index))
        layout.addWidget(delete_btn)

    def update_index(self, index):
        self.index = index


class DropArea(QFrame):
    """放置区域"""

    module_dropped = pyqtSignal(str)
    module_reordered = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QFrame {
                background: #fafbfc;
                border: 2px dashed #d0d0d0;
                border-radius: 12px;
            }
        """)
        self.setMinimumHeight(400)

        self.empty_label = QLabel("将左侧模块拖拽到这里\n\n开始构建你的设置页面", self)
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("font-size: 16px; color: #bbb; line-height: 2;")
        self.empty_label.setGeometry(0, 0, self.width(), self.height())

    def resizeEvent(self, event):
        self.empty_label.setGeometry(0, 0, self.width(), self.height())

    def show_empty(self, show):
        self.empty_label.setVisible(show)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-a13-module"):
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background: #f0f7ff;
                    border: 2px dashed #0067c0;
                    border-radius: 12px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background: #fafbfc;
                border: 2px dashed #d0d0d0;
                border-radius: 12px;
            }
        """)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-a13-module"):
            module_type = bytes(event.mimeData().data("application/x-a13-module")).decode()
            self.module_dropped.emit(module_type)
            event.acceptProposedAction()
        self.setStyleSheet("""
            QFrame {
                background: #fafbfc;
                border: 2px dashed #d0d0d0;
                border-radius: 12px;
            }
        """)


class ModuleEditDialog(QFrame):
    """模块属性编辑面板"""

    data_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = {}
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e5e5;
                border-radius: 10px;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("模块属性编辑")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0067c0;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        self.form_layout = QFormLayout(content)
        self.form_layout.setSpacing(10)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("例如：enabled")
        self.key_input.setStyleSheet("QLineEdit { padding: 6px 10px; border: 1px solid #ddd; border-radius: 5px; }")
        self.form_layout.addRow("配置键名*：", self.key_input)

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("显示给用户的标签")
        self.label_input.setStyleSheet("QLineEdit { padding: 6px 10px; border: 1px solid #ddd; border-radius: 5px; }")
        self.form_layout.addRow("显示标签：", self.label_input)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("选项说明（可选）")
        self.desc_input.setStyleSheet("QLineEdit { padding: 6px 10px; border: 1px solid #ddd; border-radius: 5px; }")
        self.form_layout.addRow("说明文字：", self.desc_input)

        self.type_combo = QComboBox()
        for m in MODULE_TYPES:
            self.type_combo.addItem(f"{m['icon']} {m['name']}", m["type"])
        self.type_combo.setStyleSheet("QComboBox { padding: 6px 10px; border: 1px solid #ddd; border-radius: 5px; }")
        self.form_layout.addRow("模块类型：", self.type_combo)

        self.default_input = QLineEdit()
        self.default_input.setPlaceholderText("默认值")
        self.default_input.setStyleSheet("QLineEdit { padding: 6px 10px; border: 1px solid #ddd; border-radius: 5px; }")
        self.form_layout.addRow("默认值：", self.default_input)

        self.options_input = QTextEdit()
        self.options_input.setPlaceholderText("下拉选项，每行一个（仅下拉选择需要）")
        self.options_input.setMaximumHeight(80)
        self.options_input.setStyleSheet("QTextEdit { padding: 6px 10px; border: 1px solid #ddd; border-radius: 5px; }")
        self.form_layout.addRow("选项列表：", self.options_input)

        self.min_input = QSpinBox()
        self.min_input.setRange(-99999, 99999)
        self.min_input.setValue(0)
        self.form_layout.addRow("最小值：", self.min_input)

        self.max_input = QSpinBox()
        self.max_input.setRange(-99999, 99999)
        self.max_input.setValue(100)
        self.form_layout.addRow("最大值：", self.max_input)

        self.step_input = QSpinBox()
        self.step_input.setRange(1, 1000)
        self.step_input.setValue(1)
        self.form_layout.addRow("步长：", self.step_input)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        save_btn = QPushButton("保存修改")
        save_btn.setStyleSheet("QPushButton { background: #107c10; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: 600; } QPushButton:hover { background: #0e6c0e; }")
        save_btn.clicked.connect(self._save_data)
        layout.addWidget(save_btn)

    def load_data(self, data):
        self.current_data = data.copy()
        self.key_input.setText(data.get("key", ""))
        self.label_input.setText(data.get("label", ""))
        self.desc_input.setText(data.get("desc", ""))

        module_type = data.get("type", "input")
        index = self.type_combo.findData(module_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        default_val = data.get("default", "")
        self.default_input.setText(str(default_val))

        options = data.get("options", [])
        if options:
            self.options_input.setPlainText("\n".join(options))

        self.min_input.setValue(data.get("min", 0))
        self.max_input.setValue(data.get("max", 100))
        self.step_input.setValue(data.get("step", 1))

    def _save_data(self):
        if not self.key_input.text().strip():
            return

        data = {
            "key": self.key_input.text().strip(),
            "label": self.label_input.text().strip(),
            "desc": self.desc_input.text().strip(),
            "type": self.type_combo.currentData(),
            "default": self.default_input.text(),
            "min": self.min_input.value(),
            "max": self.max_input.value(),
            "step": self.step_input.value(),
        }

        options_text = self.options_input.toPlainText().strip()
        if options_text:
            data["options"] = [line.strip() for line in options_text.split("\n") if line.strip()]

        self.data_changed.emit(data)


class VisualPageEditor(QWidget):
    """可视化页面编辑器主组件"""

    page_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page_data = {"title": "", "description": "", "items": []}
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        toolbox = QFrame()
        toolbox.setFixedWidth(220)
        toolbox.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e5e5;
                border-radius: 10px;
            }
        """)
        toolbox_layout = QVBoxLayout(toolbox)
        toolbox_layout.setContentsMargins(12, 12, 12, 12)
        toolbox_layout.setSpacing(8)

        toolbox_title = QLabel("模块工具箱")
        toolbox_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0067c0;")
        toolbox_layout.addWidget(toolbox_title)

        toolbox_hint = QLabel("拖拽模块到中间区域")
        toolbox_hint.setStyleSheet("font-size: 11px; color: #999;")
        toolbox_layout.addWidget(toolbox_hint)

        toolbox_scroll = QScrollArea()
        toolbox_scroll.setWidgetResizable(True)
        toolbox_scroll.setStyleSheet("QScrollArea { border: none; }")
        toolbox_content = QWidget()
        toolbox_content_layout = QVBoxLayout(toolbox_content)
        toolbox_content_layout.setSpacing(8)

        for module_type in MODULE_TYPES:
            item = DraggableModuleItem(module_type)
            toolbox_content_layout.addWidget(item)

        toolbox_content_layout.addStretch()
        toolbox_scroll.setWidget(toolbox_content)
        toolbox_layout.addWidget(toolbox_scroll, 1)

        main_layout.addWidget(toolbox)

        center_layout = QVBoxLayout()
        center_layout.setSpacing(10)

        page_info = QFrame()
        page_info.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e5e5;
                border-radius: 10px;
            }
        """)
        page_info_layout = QHBoxLayout(page_info)
        page_info_layout.setContentsMargins(12, 10, 12, 10)
        page_info_layout.setSpacing(10)

        page_info_layout.addWidget(QLabel("页面标题："))
        self.page_title_input = QLineEdit()
        self.page_title_input.setPlaceholderText("例如：我的插件设置")
        self.page_title_input.setStyleSheet("QLineEdit { padding: 6px 10px; border: 1px solid #ddd; border-radius: 5px; }")
        self.page_title_input.textChanged.connect(self._on_page_info_changed)
        page_info_layout.addWidget(self.page_title_input, 1)

        page_info_layout.addWidget(QLabel("描述："))
        self.page_desc_input = QLineEdit()
        self.page_desc_input.setPlaceholderText("页面描述（可选）")
        self.page_desc_input.setStyleSheet("QLineEdit { padding: 6px 10px; border: 1px solid #ddd; border-radius: 5px; }")
        self.page_desc_input.textChanged.connect(self._on_page_info_changed)
        page_info_layout.addWidget(self.page_desc_input, 1)

        center_layout.addWidget(page_info)

        self.drop_area = DropArea()
        self.drop_area.module_dropped.connect(self._on_module_dropped)
        center_layout.addWidget(self.drop_area, 1)

        self.modules_container = QWidget()
        self.modules_layout = QVBoxLayout(self.modules_container)
        self.modules_layout.setContentsMargins(12, 12, 12, 12)
        self.modules_layout.setSpacing(8)
        self.modules_layout.addStretch()

        self.drop_area_layout = QVBoxLayout(self.drop_area)
        self.drop_area_layout.setContentsMargins(0, 0, 0, 0)
        self.drop_area_layout.addWidget(self.modules_container)

        center_layout.addWidget(self.drop_area, 1)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)
        main_layout.addWidget(center_widget, 1)

        self.edit_panel = ModuleEditDialog()
        self.edit_panel.setFixedWidth(280)
        self.edit_panel.data_changed.connect(self._on_module_edited)
        main_layout.addWidget(self.edit_panel)

        self._refresh_modules()

    def _on_page_info_changed(self):
        self.page_data["title"] = self.page_title_input.text()
        self.page_data["description"] = self.page_desc_input.text()
        self.page_changed.emit(self.page_data)

    def _on_module_dropped(self, module_type):
        module_template = next((m for m in MODULE_TYPES if m["type"] == module_type), None)
        if not module_template:
            return

        new_module = {
            "type": module_type,
            "key": f"item_{len(self.page_data['items']) + 1}",
            "label": module_template["name"],
            "desc": "",
            "default": module_template["default"],
        }

        if module_type == "select":
            new_module["options"] = ["选项1", "选项2", "选项3"]
        elif module_type == "slider" or module_type == "number":
            new_module["min"] = 0
            new_module["max"] = 100
            new_module["step"] = 1

        self.page_data["items"].append(new_module)
        self._refresh_modules()
        self.page_changed.emit(self.page_data)

    def _on_module_edited(self, data):
        if hasattr(self, '_editing_index') and self._editing_index is not None:
            if 0 <= self._editing_index < len(self.page_data["items"]):
                self.page_data["items"][self._editing_index] = data
                self._refresh_modules()
                self.page_changed.emit(self.page_data)

    def _delete_module(self, index):
        if 0 <= index < len(self.page_data["items"]):
            del self.page_data["items"][index]
            self._refresh_modules()
            self.page_changed.emit(self.page_data)

    def _edit_module(self, index):
        if 0 <= index < len(self.page_data["items"]):
            self._editing_index = index
            self.edit_panel.load_data(self.page_data["items"][index])

    def _move_up(self, index):
        if index > 0:
            items = self.page_data["items"]
            items[index], items[index - 1] = items[index - 1], items[index]
            self._refresh_modules()
            self.page_changed.emit(self.page_data)

    def _move_down(self, index):
        items = self.page_data["items"]
        if index < len(items) - 1:
            items[index], items[index + 1] = items[index + 1], items[index]
            self._refresh_modules()
            self.page_changed.emit(self.page_data)

    def _refresh_modules(self):
        while self.modules_layout.count() > 1:
            item = self.modules_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items = self.page_data.get("items", [])
        self.drop_area.show_empty(len(items) == 0)

        for i, module_data in enumerate(items):
            module_widget = DroppedModuleItem(i, module_data)
            module_widget.delete_clicked.connect(self._delete_module)
            module_widget.edit_clicked.connect(self._edit_module)
            module_widget.move_up.connect(self._move_up)
            module_widget.move_down.connect(self._move_down)
            self.modules_layout.insertWidget(i, module_widget)

    def load_page(self, page_data):
        self.page_data = page_data if page_data else {"title": "", "description": "", "items": []}
        self.page_title_input.setText(self.page_data.get("title", ""))
        self.page_desc_input.setText(self.page_data.get("description", ""))
        self._editing_index = None
        self._refresh_modules()

    def get_page(self):
        return self.page_data
