# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 可视化插件打包工具
将 Python 插件代码打包成 .arcx 格式，支持多页面配置、默认设置、元数据编辑
"""

import sys
import os
import json
import shutil
import base64
import zipfile
import tempfile
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QTextEdit, QFileDialog,
                             QMessageBox, QTabWidget, QCheckBox, QSpinBox, QComboBox,
                             QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
                             QScrollArea, QFrame, QSplitter, QProgressBar, QStackedWidget,
                             QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPainter, QBrush, QPen

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class StepIndicator(QWidget):
    """步骤指示器"""
    step_clicked = pyqtSignal(int)

    def __init__(self, steps, parent=None):
        super().__init__(parent)
        self.steps = steps
        self.current_step = 0
        self.completed_steps = set()
        self.setFixedHeight(80)
        self.setMinimumWidth(600)

    def set_current_step(self, step):
        self.current_step = step
        self.update()

    def set_completed(self, step):
        self.completed_steps.add(step)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        step_count = len(self.steps)
        step_width = w / step_count
        circle_radius = 18
        line_y = h // 2 - 10

        for i in range(step_count - 1):
            x1 = int(i * step_width + step_width / 2 + circle_radius + 5)
            x2 = int((i + 1) * step_width + step_width / 2 - circle_radius - 5)
            if i in self.completed_steps:
                painter.setPen(QPen(QColor("#107c10"), 3))
            else:
                painter.setPen(QPen(QColor("#e0e0e0"), 3))
            painter.drawLine(x1, line_y, x2, line_y)

        for i, step_name in enumerate(self.steps):
            cx = int(i * step_width + step_width / 2)
            cy = line_y

            if i in self.completed_steps:
                painter.setBrush(QBrush(QColor("#107c10")))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(cx - circle_radius, cy - circle_radius, circle_radius * 2, circle_radius * 2)
                painter.setPen(QPen(QColor("white"), 3))
                painter.drawLine(cx - 6, cy, cx - 2, cy + 5)
                painter.drawLine(cx - 2, cy + 5, cx + 7, cy - 5)
            elif i == self.current_step:
                painter.setBrush(QBrush(QColor("#0067c0")))
                painter.setPen(QPen(QColor("#0067c0"), 3))
                painter.drawEllipse(cx - circle_radius, cy - circle_radius, circle_radius * 2, circle_radius * 2)
                painter.setPen(QPen(QColor("white"), 2))
                painter.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
                painter.drawText(cx - circle_radius, cy - circle_radius, circle_radius * 2, circle_radius * 2, Qt.AlignCenter, str(i + 1))
            else:
                painter.setBrush(QBrush(QColor("white")))
                painter.setPen(QPen(QColor("#cccccc"), 2))
                painter.drawEllipse(cx - circle_radius, cy - circle_radius, circle_radius * 2, circle_radius * 2)
                painter.setPen(QPen(QColor("#999999"), 2))
                painter.setFont(QFont("Microsoft YaHei", 12))
                painter.drawText(cx - circle_radius, cy - circle_radius, circle_radius * 2, circle_radius * 2, Qt.AlignCenter, str(i + 1))

            if i == self.current_step:
                painter.setPen(QColor("#0067c0"))
                painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
            elif i in self.completed_steps:
                painter.setPen(QColor("#107c10"))
                painter.setFont(QFont("Microsoft YaHei", 10))
            else:
                painter.setPen(QColor("#999999"))
                painter.setFont(QFont("Microsoft YaHei", 10))
            painter.drawText(int(cx - step_width / 2), cy + circle_radius + 8, int(step_width), 20, Qt.AlignCenter, step_name)

        painter.end()


class ModernCard(QFrame):
    """现代化卡片"""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e5e5;
                border-radius: 10px;
            }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 16)
        self._layout.setSpacing(12)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #0067c0;")
            self._layout.addWidget(title_label)

    def add_widget(self, widget):
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)

    def add_stretch(self):
        self._layout.addStretch()


class ArcxPackager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A13可视化插件打包工具")
        self.setMinimumSize(1100, 780)
        self.resize(1200, 820)
        self._code_content = ""
        self._pages = []
        self._libs = []
        self._icons = []
        self._libs_dir = os.path.join(tempfile.gettempdir(), "a13_plugin_libs")
        self._ensure_libs_dir()
        self._steps = ["元数据", "插件代码", "页面配置", "默认设置", "依赖库", "图标资源", "预览打包"]
        self._current_step = 0
        self._setup_ui()
        self._load_defaults()

    def _ensure_libs_dir(self):
        if not os.path.exists(self._libs_dir):
            os.makedirs(self._libs_dir)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0067c0, stop:1 #0078d4);
                border: none;
            }
        """)
        header.setFixedHeight(90)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)
        header_layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_label = QLabel("A13 可视化插件打包工具")
        title_label.setStyleSheet("font-size: 22px; font-weight: 800; color: white;")
        title_row.addWidget(title_label)
        title_row.addStretch()

        version_label = QLabel("v2.0 可视化版")
        version_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8); padding: 4px 12px; background: rgba(255,255,255,0.15); border-radius: 10px;")
        title_row.addWidget(version_label)
        header_layout.addLayout(title_row)

        subtitle = QLabel("将 Python 插件代码打包成 .arcx 格式，支持多页面配置、默认设置、依赖库、图标资源")
        subtitle.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.85);")
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header)

        step_container = QFrame()
        step_container.setStyleSheet("background: #f8f9fa; border-bottom: 1px solid #e5e5e5;")
        step_container.setFixedHeight(90)
        step_layout = QHBoxLayout(step_container)
        step_layout.setContentsMargins(30, 10, 30, 10)

        self.step_indicator = StepIndicator(self._steps)
        step_layout.addWidget(self.step_indicator)
        main_layout.addWidget(step_container)

        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("QStackedWidget { background: #f0f2f5; }")
        content_layout.addWidget(self.stacked_widget, 1)

        main_layout.addWidget(content_container, 1)

        footer = QFrame()
        footer.setStyleSheet("background: white; border-top: 1px solid #e5e5e5;")
        footer.setFixedHeight(70)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(30, 12, 30, 12)
        footer_layout.setSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("完成度: %p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: #f5f5f5;
                height: 22px;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0067c0, stop:1 #0078d4);
                border-radius: 5px;
            }
        """)
        self.progress_bar.setFixedWidth(250)
        footer_layout.addWidget(self.progress_bar)

        footer_layout.addStretch()

        self.prev_btn = QPushButton("上一步")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background: #e5e5e5; }
            QPushButton:disabled { background: #f5f5f5; color: #ccc; }
        """)
        self.prev_btn.clicked.connect(self._prev_step)
        self.prev_btn.setEnabled(False)
        footer_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("下一步")
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: #0067c0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 28px;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover { background: #1a76c8; }
        """)
        self.next_btn.clicked.connect(self._next_step)
        footer_layout.addWidget(self.next_btn)

        self.package_btn = QPushButton("打包成 .arcx")
        self.package_btn.setStyleSheet("""
            QPushButton {
                background: #107c10;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 32px;
                font-weight: 700;
                font-size: 14px;
            }
            QPushButton:hover { background: #0e6c0e; }
        """)
        self.package_btn.clicked.connect(self._package)
        self.package_btn.setVisible(False)
        footer_layout.addWidget(self.package_btn)

        main_layout.addWidget(footer)

        self._build_all_pages()
        self._update_step_ui()

    def _build_all_pages(self):
        self._build_meta_page()
        self._build_code_page()
        self._build_pages_page()
        self._build_config_page()
        self._build_libs_page()
        self._build_icons_page()
        self._build_preview_page()

    def _build_meta_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        card = ModernCard("插件元数据")
        form = QFormLayout()
        form.setSpacing(12)

        self.plugin_name = QLineEdit()
        self.plugin_name.setPlaceholderText("例如：课堂回声洞")
        self.plugin_name.setStyleSheet("QLineEdit { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; } QLineEdit:focus { border-color: #0067c0; }")
        form.addRow("插件名称*：", self.plugin_name)

        self.plugin_id = QLineEdit()
        self.plugin_id.setPlaceholderText("例如：echo_hole（唯一标识）")
        self.plugin_id.setStyleSheet("QLineEdit { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; } QLineEdit:focus { border-color: #0067c0; }")
        form.addRow("插件ID*：", self.plugin_id)

        self.plugin_version = QLineEdit("1.0.0")
        self.plugin_version.setStyleSheet("QLineEdit { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; } QLineEdit:focus { border-color: #0067c0; }")
        form.addRow("版本号：", self.plugin_version)

        self.plugin_author = QLineEdit()
        self.plugin_author.setPlaceholderText("作者名称")
        self.plugin_author.setStyleSheet("QLineEdit { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; } QLineEdit:focus { border-color: #0067c0; }")
        form.addRow("作者：", self.plugin_author)

        self.plugin_description = QTextEdit()
        self.plugin_description.setPlaceholderText("插件功能描述...")
        self.plugin_description.setMaximumHeight(80)
        self.plugin_description.setStyleSheet("QTextEdit { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; } QTextEdit:focus { border-color: #0067c0; }")
        form.addRow("描述：", self.plugin_description)

        self.plugin_category = QComboBox()
        self.plugin_category.addItems(["工具", "娱乐", "教学", "数据", "其他"])
        self.plugin_category.setStyleSheet("QComboBox { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }")
        form.addRow("分类：", self.plugin_category)

        card.add_layout(form)
        scroll_layout.addWidget(card)

        info_card = ModernCard("提示")
        info_text = QLabel("插件ID是插件的唯一标识，安装后会作为文件夹名称。请使用英文、数字和下划线，不要使用中文和特殊字符。")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 12px; color: #666; line-height: 1.6;")
        info_card.add_widget(info_text)
        scroll_layout.addWidget(info_card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self.stacked_widget.addWidget(page)

    def _build_code_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        btn_row = QHBoxLayout()
        load_btn = QPushButton("从文件加载代码")
        load_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; } QPushButton:hover { background: #1a76c8; }")
        load_btn.clicked.connect(self._load_code_file)
        btn_row.addWidget(load_btn)

        paste_btn = QPushButton("粘贴代码")
        paste_btn.setStyleSheet("QPushButton { background: #666; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; } QPushButton:hover { background: #555; }")
        paste_btn.clicked.connect(self._paste_code)
        btn_row.addWidget(paste_btn)

        template_btn = QPushButton("加载示例模板")
        template_btn.setStyleSheet("QPushButton { background: #8764b8; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; } QPushButton:hover { background: #7a56a8; }")
        template_btn.clicked.connect(self._load_template)
        btn_row.addWidget(template_btn)

        btn_row.addStretch()

        self.code_status = QLabel("未加载代码")
        self.code_status.setStyleSheet("font-size: 12px; color: #999;")
        btn_row.addWidget(self.code_status)

        layout.addLayout(btn_row)

        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("在此粘贴或输入插件 Python 代码...\n\n插件代码需要定义 main() 函数，接收 plugin_context 参数。")
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 12px;
                font-family: Consolas, Monaco, monospace;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.code_editor, 1)

        self.stacked_widget.addWidget(page)

    def _build_pages_page(self):
        from visual_page_editor import VisualPageEditor
        page = QWidget()
        page.setStyleSheet("background: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        pages_bar = QFrame()
        pages_bar.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e5e5;
                border-radius: 10px;
            }
        """)
        pages_bar_layout = QHBoxLayout(pages_bar)
        pages_bar_layout.setContentsMargins(12, 8, 12, 8)
        pages_bar_layout.setSpacing(8)

        pages_bar_layout.addWidget(QLabel("页面："))
        self.page_selector = QComboBox()
        self.page_selector.setStyleSheet("QComboBox { padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; min-width: 200px; }")
        self.page_selector.currentIndexChanged.connect(self._on_page_selected)
        pages_bar_layout.addWidget(self.page_selector)

        add_page_btn = QPushButton("+ 添加页面")
        add_page_btn.setStyleSheet("QPushButton { background: #107c10; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; } QPushButton:hover { background: #0e6c0e; }")
        add_page_btn.clicked.connect(self._add_page)
        pages_bar_layout.addWidget(add_page_btn)

        rename_page_btn = QPushButton("重命名")
        rename_page_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; } QPushButton:hover { background: #1a76c8; }")
        rename_page_btn.clicked.connect(self._rename_page)
        pages_bar_layout.addWidget(rename_page_btn)

        remove_page_btn = QPushButton("删除页面")
        remove_page_btn.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; } QPushButton:hover { background: #a02010; }")
        remove_page_btn.clicked.connect(self._remove_page)
        pages_bar_layout.addWidget(remove_page_btn)

        pages_bar_layout.addStretch()

        page_count_label = QLabel("共 0 个页面")
        page_count_label.setStyleSheet("font-size: 12px; color: #999;")
        self.page_count_label = page_count_label
        pages_bar_layout.addWidget(page_count_label)

        layout.addWidget(pages_bar)

        self.page_editor = VisualPageEditor()
        self.page_editor.page_changed.connect(self._on_page_edited)
        layout.addWidget(self.page_editor, 1)

        self.stacked_widget.addWidget(page)
        self._refresh_page_selector()

    def _build_config_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        card = ModernCard("默认设置（JSON 格式）")
        config_layout = QVBoxLayout()
        config_layout.setSpacing(10)

        hint = QLabel("定义插件的默认配置项，用户可以在设置中修改。使用 JSON 格式。")
        hint.setStyleSheet("font-size: 12px; color: #666;")
        config_layout.addWidget(hint)

        self.config_editor = QTextEdit()
        self.config_editor.setPlaceholderText('{\n  "enabled": true,\n  "interval": 5,\n  "message": "你好"\n}')
        self.config_editor.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 12px;
                font-family: Consolas, Monaco, monospace;
                font-size: 13px;
            }
        """)
        config_layout.addWidget(self.config_editor, 1)

        format_btn = QPushButton("格式化 JSON")
        format_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }")
        format_btn.clicked.connect(self._format_json)
        config_layout.addWidget(format_btn, alignment=Qt.AlignRight)

        card.add_layout(config_layout)
        layout.addWidget(card, 1)

        self.stacked_widget.addWidget(page)

    def _build_libs_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        card = ModernCard("依赖库文件")
        libs_layout = QVBoxLayout()
        libs_layout.setSpacing(10)

        hint = QLabel("如果插件依赖额外的 Python 库（.py 文件），可以在这里添加。打包时会一起包含在 .arcxpkg 中。")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 12px; color: #666; line-height: 1.6;")
        libs_layout.addWidget(hint)

        self.libs_list = QListWidget()
        self.libs_list.setStyleSheet("QListWidget { background: white; border: 1px solid #e5e5e5; border-radius: 8px; padding: 4px; } QListWidget::item { padding: 10px; border-bottom: 1px solid #f0f0f0; }")
        libs_layout.addWidget(self.libs_list, 1)

        libs_btn_row = QHBoxLayout()
        add_lib_btn = QPushButton("添加库文件")
        add_lib_btn.setStyleSheet("QPushButton { background: #107c10; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }")
        add_lib_btn.clicked.connect(self._add_lib_file)
        libs_btn_row.addWidget(add_lib_btn)

        remove_lib_btn = QPushButton("移除选中")
        remove_lib_btn.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }")
        remove_lib_btn.clicked.connect(self._remove_lib_file)
        libs_btn_row.addWidget(remove_lib_btn)

        clear_lib_btn = QPushButton("清空")
        clear_lib_btn.setStyleSheet("QPushButton { background: #666; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }")
        clear_lib_btn.clicked.connect(self._clear_lib_files)
        libs_btn_row.addWidget(clear_lib_btn)

        libs_btn_row.addStretch()
        self.libs_count_label = QLabel("共 0 个文件")
        self.libs_count_label.setStyleSheet("font-size: 12px; color: #999;")
        libs_btn_row.addWidget(self.libs_count_label)

        libs_layout.addLayout(libs_btn_row)
        card.add_layout(libs_layout)
        layout.addWidget(card, 1)

        self.stacked_widget.addWidget(page)

    def _build_icons_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        card = ModernCard("图标资源")
        icons_layout = QVBoxLayout()
        icons_layout.setSpacing(10)

        hint = QLabel("添加插件需要的图标文件（.svg, .png, .ico）。插件可以通过 plugin_context.get_icon_path('文件名') 获取图标路径。")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 12px; color: #666; line-height: 1.6;")
        icons_layout.addWidget(hint)

        self.icons_list = QListWidget()
        self.icons_list.setStyleSheet("QListWidget { background: white; border: 1px solid #e5e5e5; border-radius: 8px; padding: 4px; } QListWidget::item { padding: 10px; border-bottom: 1px solid #f0f0f0; }")
        icons_layout.addWidget(self.icons_list, 1)

        icons_btn_row = QHBoxLayout()
        add_icon_btn = QPushButton("添加图标文件")
        add_icon_btn.setStyleSheet("QPushButton { background: #107c10; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }")
        add_icon_btn.clicked.connect(self._add_icon_file)
        icons_btn_row.addWidget(add_icon_btn)

        remove_icon_btn = QPushButton("移除选中")
        remove_icon_btn.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }")
        remove_icon_btn.clicked.connect(self._remove_icon_file)
        icons_btn_row.addWidget(remove_icon_btn)

        clear_icon_btn = QPushButton("清空")
        clear_icon_btn.setStyleSheet("QPushButton { background: #666; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }")
        clear_icon_btn.clicked.connect(self._clear_icon_files)
        icons_btn_row.addWidget(clear_icon_btn)

        icons_btn_row.addStretch()
        self.icons_count_label = QLabel("共 0 个文件")
        self.icons_count_label.setStyleSheet("font-size: 12px; color: #999;")
        icons_btn_row.addWidget(self.icons_count_label)

        icons_layout.addLayout(icons_btn_row)
        card.add_layout(icons_layout)
        layout.addWidget(card, 1)

        self.stacked_widget.addWidget(page)

    def _build_preview_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        splitter = QSplitter(Qt.Horizontal)

        left_card = ModernCard("打包信息预览")
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)

        self.preview_info = QLabel("点击「刷新预览」查看打包信息")
        self.preview_info.setWordWrap(True)
        self.preview_info.setStyleSheet("font-size: 13px; color: #555; line-height: 1.8;")
        left_layout.addWidget(self.preview_info, 1)

        refresh_btn = QPushButton("刷新预览")
        refresh_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; }")
        refresh_btn.clicked.connect(self._refresh_preview)
        left_layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)

        left_card.add_layout(left_layout)
        splitter.addWidget(left_card)

        right_card = ModernCard("JSON 结构预览")
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        self.preview_json = QTextEdit()
        self.preview_json.setReadOnly(True)
        self.preview_json.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 12px;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
            }
        """)
        right_layout.addWidget(self.preview_json, 1)

        right_card.add_layout(right_layout)
        splitter.addWidget(right_card)

        splitter.setSizes([400, 600])
        layout.addWidget(splitter, 1)

        action_row = QHBoxLayout()
        action_row.addStretch()

        self.installer_btn = QPushButton("生成安装程序")
        self.installer_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 12px 28px; font-weight: 700; font-size: 14px; } QPushButton:hover { background: #005a9e; }")
        self.installer_btn.clicked.connect(self._generate_installer)
        action_row.addWidget(self.installer_btn)

        self.arcxpkg_btn = QPushButton("打包含依赖(.arcxpkg)")
        self.arcxpkg_btn.setStyleSheet("QPushButton { background: #ca5010; color: white; border: none; border-radius: 6px; padding: 12px 28px; font-weight: 700; font-size: 14px; } QPushButton:hover { background: #b04810; }")
        self.arcxpkg_btn.clicked.connect(self._generate_arcxpkg)
        action_row.addWidget(self.arcxpkg_btn)

        layout.addLayout(action_row)

        self.stacked_widget.addWidget(page)

    def _prev_step(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step_ui()

    def _next_step(self):
        if self._current_step < len(self._steps) - 1:
            self._current_step += 1
            self._update_step_ui()

    def _update_step_ui(self):
        self.stacked_widget.setCurrentIndex(self._current_step)
        self.step_indicator.set_current_step(self._current_step)

        for i in range(self._current_step):
            self.step_indicator.set_completed(i)

        self.prev_btn.setEnabled(self._current_step > 0)

        if self._current_step == len(self._steps) - 1:
            self.next_btn.setVisible(False)
            self.package_btn.setVisible(True)
            self._refresh_preview()
        else:
            self.next_btn.setVisible(True)
            self.package_btn.setVisible(False)
            self.next_btn.setText("下一步")

        progress = int((self._current_step + 1) / len(self._steps) * 100)
        self.progress_bar.setValue(progress)

    def _load_defaults(self):
        self.config_editor.setPlainText('{\n  "enabled": true\n}')

    def _load_template(self):
        template = '''# A13 插件示例模板
# 插件需要定义 main() 函数，接收 plugin_context 参数

def main(plugin_context):
    """
    插件主函数
    plugin_context: 插件上下文，提供各种API
    """
    # 获取插件配置
    config = plugin_context.get_config()
    enabled = config.get("enabled", True)

    if not enabled:
        return

    # 记录日志
    plugin_context.log_info("插件已启动")

    # 添加设置页面
    plugin_context.add_settings_page(
        title="示例插件设置",
        description="这是一个示例插件的设置页面",
        items=[
            {"key": "enabled", "type": "switch", "label": "启用插件", "default": True},
            {"key": "message", "type": "input", "label": "提示消息", "default": "你好"},
        ]
    )

    # 注册事件监听
    def on_draw_result(name, text):
        plugin_context.log_info(f"抽取结果: {name}")

    plugin_context.on("draw_result", on_draw_result)

    plugin_context.log_info("示例插件加载完成")
'''
        self.code_editor.setPlainText(template)
        self.code_status.setText("已加载示例模板")
        self.plugin_name.setText("示例插件")
        self.plugin_id.setText("example_plugin")
        self.plugin_author.setText("A13")
        self.plugin_description.setPlainText("这是一个示例插件，展示了插件的基本结构和API用法。")

    def _load_code_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择插件代码文件", "", "Python Files (*.py)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.code_editor.setPlainText(f.read())
                self.code_status.setText(f"已加载: {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.warning(self, "加载失败", f"加载代码文件失败：{str(e)}")

    def _paste_code(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.code_editor.setPlainText(text)
            self.code_status.setText("已从剪贴板粘贴")
        else:
            QMessageBox.information(self, "提示", "剪贴板中没有文本内容")

    def _add_page(self):
        from PyQt5.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(self, "添加页面", "页面标题：", text=f"设置页面 {len(self._pages) + 1}")
        if ok and title:
            new_page = {"title": title, "description": "", "items": []}
            self._pages.append(new_page)
            self._refresh_page_selector()
            self.page_selector.setCurrentIndex(len(self._pages) - 1)

    def _remove_page(self):
        index = self.page_selector.currentIndex()
        if index >= 0 and index < len(self._pages):
            reply = QMessageBox.question(self, "确认删除", f"确定要删除页面「{self._pages[index]['title']}」吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self._pages[index]
                self._refresh_page_selector()
                if self._pages:
                    self.page_selector.setCurrentIndex(min(index, len(self._pages) - 1))

    def _rename_page(self):
        index = self.page_selector.currentIndex()
        if index >= 0 and index < len(self._pages):
            from PyQt5.QtWidgets import QInputDialog
            title, ok = QInputDialog.getText(self, "重命名页面", "新页面标题：", text=self._pages[index]["title"])
            if ok and title:
                self._pages[index]["title"] = title
                self._refresh_page_selector()
                self.page_selector.setCurrentIndex(index)

    def _refresh_page_selector(self):
        self.page_selector.blockSignals(True)
        self.page_selector.clear()
        for i, page in enumerate(self._pages):
            self.page_selector.addItem(f"{i+1}. {page['title']} ({len(page.get('items', []))}项)")
        self.page_selector.blockSignals(False)
        self.page_count_label.setText(f"共 {len(self._pages)} 个页面")

        if self._pages:
            current = min(self.page_selector.currentIndex(), len(self._pages) - 1)
            if current < 0:
                current = 0
            self.page_editor.load_page(self._pages[current])
        else:
            self.page_editor.load_page({"title": "", "description": "", "items": []})

    def _on_page_selected(self, index):
        if 0 <= index < len(self._pages):
            self.page_editor.load_page(self._pages[index])

    def _on_page_edited(self, page_data):
        index = self.page_selector.currentIndex()
        if 0 <= index < len(self._pages):
            self._pages[index] = page_data
            self._refresh_page_selector()
            self.page_selector.setCurrentIndex(index)

    def _format_json(self):
        try:
            text = self.config_editor.toPlainText()
            data = json.loads(text)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.config_editor.setPlainText(formatted)
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "格式错误", f"JSON 格式错误：{str(e)}")

    def _add_lib_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择库文件", "", "Python Files (*.py)")
        for path in paths:
            if path not in self._libs:
                self._libs.append(path)
        self._update_libs_list()

    def _remove_lib_file(self):
        row = self.libs_list.currentRow()
        if row >= 0 and row < len(self._libs):
            del self._libs[row]
            self._update_libs_list()

    def _clear_lib_files(self):
        self._libs.clear()
        self._update_libs_list()

    def _update_libs_list(self):
        self.libs_list.clear()
        for path in self._libs:
            self.libs_list.addItem(os.path.basename(path))
        self.libs_count_label.setText(f"共 {len(self._libs)} 个文件")

    def _add_icon_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择图标文件", "", "Image Files (*.svg *.png *.ico *.jpg)")
        for path in paths:
            if path not in self._icons:
                self._icons.append(path)
        self._update_icons_list()

    def _remove_icon_file(self):
        row = self.icons_list.currentRow()
        if row >= 0 and row < len(self._icons):
            del self._icons[row]
            self._update_icons_list()

    def _clear_icon_files(self):
        self._icons.clear()
        self._update_icons_list()

    def _update_icons_list(self):
        self.icons_list.clear()
        for path in self._icons:
            self.icons_list.addItem(os.path.basename(path))
        self.icons_count_label.setText(f"共 {len(self._icons)} 个文件")

    def _build_arcx_data(self):
        code = self.code_editor.toPlainText()
        code_b64 = base64.b64encode(code.encode("utf-8")).decode("utf-8")

        try:
            config = json.loads(self.config_editor.toPlainText())
        except:
            config = {}

        data = {
            "format": "a13-plugin",
            "version": "1.0",
            "metadata": {
                "name": self.plugin_name.text(),
                "id": self.plugin_id.text(),
                "version": self.plugin_version.text(),
                "author": self.plugin_author.text(),
                "description": self.plugin_description.toPlainText(),
                "category": self.plugin_category.currentText(),
                "created": datetime.now().isoformat(),
            },
            "code": code_b64,
            "config": config,
            "pages": self._pages,
            "libs": [os.path.basename(p) for p in self._libs],
            "icons": [os.path.basename(p) for p in self._icons],
        }
        return data

    def _refresh_preview(self):
        data = self._build_arcx_data()
        meta = data["metadata"]

        info_text = f"""
插件名称：{meta['name'] or '（未填写）'}
插件ID：{meta['id'] or '（未填写）'}
版本：{meta['version']}
作者：{meta['author'] or '（未填写）'}
分类：{meta['category']}

代码行数：{len(self.code_editor.toPlainText().splitlines())} 行
配置项：{len(data.get('config', {}))} 个
页面数：{len(self._pages)} 个
依赖库：{len(self._libs)} 个
图标资源：{len(self._icons)} 个

创建时间：{meta['created']}
        """
        self.preview_info.setText(info_text.strip())

        preview_data = {k: v for k, v in data.items() if k != "code"}
        preview_data["code"] = f"<base64 encoded, {len(data['code'])} chars>"
        self.preview_json.setPlainText(json.dumps(preview_data, indent=2, ensure_ascii=False))

    def _package(self):
        if not self.plugin_name.text():
            QMessageBox.warning(self, "提示", "请填写插件名称")
            self._current_step = 0
            self._update_step_ui()
            return
        if not self.plugin_id.text():
            QMessageBox.warning(self, "提示", "请填写插件ID")
            self._current_step = 0
            self._update_step_ui()
            return
        if not self.code_editor.toPlainText().strip():
            QMessageBox.warning(self, "提示", "请添加插件代码")
            self._current_step = 1
            self._update_step_ui()
            return

        data = self._build_arcx_data()
        default_name = f"{data['metadata']['id']}_v{data['metadata']['version']}.arcx"
        path, _ = QFileDialog.getSaveFileName(self, "保存插件", default_name, "A13 Plugin (*.arcx)")
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "打包成功", f"插件已打包到：\n{path}\n\n可以在主程序中安装使用。")
        except Exception as e:
            QMessageBox.warning(self, "打包失败", f"打包失败：{str(e)}")

    def _generate_installer(self):
        QMessageBox.information(self, "提示", "安装程序生成功能请使用 plugin_installer.py")

    def _generate_arcxpkg(self):
        if not self._libs and not self._icons:
            QMessageBox.information(self, "提示", "当前没有依赖库或图标资源，无需打包含依赖版本。普通 .arcx 已足够。")
            return

        data = self._build_arcx_data()
        default_name = f"{data['metadata']['id']}_v{data['metadata']['version']}.arcxpkg"
        path, _ = QFileDialog.getSaveFileName(self, "保存含依赖插件", default_name, "A13 Plugin Package (*.arcxpkg)")
        if not path:
            return

        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                arcx_data = json.dumps(data, indent=2, ensure_ascii=False)
                zf.writestr("plugin.arcx", arcx_data)

                for lib_path in self._libs:
                    zf.write(lib_path, f"libs/{os.path.basename(lib_path)}")

                for icon_path in self._icons:
                    zf.write(icon_path, f"icons/{os.path.basename(icon_path)}")

            QMessageBox.information(self, "打包成功", f"含依赖插件已打包到：\n{path}\n\n包含 {len(self._libs)} 个依赖库，{len(self._icons)} 个图标资源。")
        except Exception as e:
            QMessageBox.warning(self, "打包失败", f"打包失败：{str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei", 10))

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f0f2f5"))
    palette.setColor(QPalette.WindowText, QColor("#333333"))
    palette.setColor(QPalette.Base, QColor("white"))
    palette.setColor(QPalette.AlternateBase, QColor("#f8f9fa"))
    palette.setColor(QPalette.ToolTipBase, QColor("white"))
    palette.setColor(QPalette.ToolTipText, QColor("#333333"))
    palette.setColor(QPalette.Text, QColor("#333333"))
    palette.setColor(QPalette.Button, QColor("#f0f0f0"))
    palette.setColor(QPalette.ButtonText, QColor("#333333"))
    palette.setColor(QPalette.BrightText, QColor("red"))
    palette.setColor(QPalette.Link, QColor("#0067c0"))
    palette.setColor(QPalette.Highlight, QColor("#0067c0"))
    palette.setColor(QPalette.HighlightedText, QColor("white"))
    app.setPalette(palette)

    app.setStyleSheet("""
        QWidget { font-family: "Microsoft YaHei"; }
        QToolTip { background: #2b2b2b; color: white; border: none; padding: 5px 8px; border-radius: 4px; }
        QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
        QScrollBar::handle:vertical { background: #c1c1c1; border-radius: 5px; min-height: 30px; }
        QScrollBar::handle:vertical:hover { background: #a8a8a8; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
        QScrollBar::handle:horizontal { background: #c1c1c1; border-radius: 5px; min-width: 30px; }
        QScrollBar::handle:horizontal:hover { background: #a8a8a8; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
    """)

    icon_path = os.path.join(BASE_DIR, "app.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = ArcxPackager()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
