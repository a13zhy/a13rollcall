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
                             QScrollArea, QFrame, QSplitter)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ArcxPackager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A13插件打包工具 - .arcx 生成器")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        self._code_content = ""
        self._pages = []
        self._libs_dir = os.path.join(tempfile.gettempdir(), "a13_plugin_libs")
        self._ensure_libs_dir()
        self._setup_ui()
        self._load_defaults()

    def _ensure_libs_dir(self):
        if not os.path.exists(self._libs_dir):
            os.makedirs(self._libs_dir)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        title = QLabel("🔧 A13插件打包工具")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0067c0;")
        main_layout.addWidget(title)

        subtitle = QLabel("将 Python 插件代码打包成 .arcx 格式，支持多页面配置、默认设置、元数据编辑")
        subtitle.setStyleSheet("font-size: 13px; color: #666666;")
        main_layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e0e0e0; border-radius: 8px; }
            QTabBar::tab { padding: 10px 20px; margin-right: 4px; border-radius: 6px 6px 0 0; font-size: 13px; }
            QTabBar::tab:selected { background: #0067c0; color: white; }
            QTabBar::tab:!selected { background: #f0f0f0; color: #333; }
        """)
        main_layout.addWidget(self.tabs, 1)

        self._build_meta_tab()
        self._build_code_tab()
        self._build_pages_tab()
        self._build_config_tab()
        self._build_libs_tab()
        self._build_preview_tab()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.load_template_btn = QPushButton("📂 加载示例模板")
        self.load_template_btn.setStyleSheet("QPushButton { background: #666; color: white; border: none; border-radius: 6px; padding: 12px 24px; font-weight: 600; font-size: 14px; }")
        self.load_template_btn.clicked.connect(self._load_template)
        btn_layout.addWidget(self.load_template_btn)

        self.package_btn = QPushButton("📦 打包成 .arcx")
        self.package_btn.setStyleSheet("QPushButton { background: #107c10; color: white; border: none; border-radius: 6px; padding: 12px 32px; font-weight: 700; font-size: 15px; } QPushButton:hover { background: #0e6c0e; }")
        self.package_btn.clicked.connect(self._package)
        btn_layout.addWidget(self.package_btn)

        self.installer_btn = QPushButton("🚀 生成安装程序")
        self.installer_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 12px 32px; font-weight: 700; font-size: 15px; } QPushButton:hover { background: #005a9e; }")
        self.installer_btn.clicked.connect(self._generate_installer)
        btn_layout.addWidget(self.installer_btn)

        self.arcxpkg_btn = QPushButton("📚 打包含依赖(.arcxpkg)")
        self.arcxpkg_btn.setStyleSheet("QPushButton { background: #ca5010; color: white; border: none; border-radius: 6px; padding: 12px 32px; font-weight: 700; font-size: 15px; } QPushButton:hover { background: #b04810; }")
        self.arcxpkg_btn.clicked.connect(self._generate_arcxpkg)
        btn_layout.addWidget(self.arcxpkg_btn)

        main_layout.addLayout(btn_layout)

    def _build_meta_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        group = QGroupBox("插件元数据")
        group.setStyleSheet("QGroupBox { font-weight: 700; font-size: 14px; border: 1px solid #e0e0e0; border-radius: 8px; margin-top: 12px; padding-top: 16px; }")
        form = QFormLayout(group)
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：示例插件")
        form.addRow("插件名称*：", self.name_input)

        self.version_input = QLineEdit()
        self.version_input.setText("1.0.0")
        form.addRow("版本号：", self.version_input)

        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("例如：张三")
        form.addRow("作者：", self.author_input)

        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setPlaceholderText("简要描述插件的功能和用途")
        form.addRow("描述：", self.desc_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["general", "tool", "theme", "data", "ui"])
        form.addRow("插件类型：", self.type_combo)

        self.api_spin = QSpinBox()
        self.api_spin.setRange(1, 10)
        self.api_spin.setValue(2)
        form.addRow("API版本：", self.api_spin)

        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "📝 元数据")

    def _build_code_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        btn_row = QHBoxLayout()
        self.load_code_btn = QPushButton("📂 加载 Python 文件")
        self.load_code_btn.clicked.connect(self._load_code_file)
        btn_row.addWidget(self.load_code_btn)

        self.paste_code_btn = QPushButton("📋 粘贴代码")
        self.paste_code_btn.clicked.connect(self._paste_code)
        btn_row.addWidget(self.paste_code_btn)

        self.clear_code_btn = QPushButton("🗑️ 清空")
        self.clear_code_btn.clicked.connect(lambda: self.code_editor.clear())
        btn_row.addWidget(self.clear_code_btn)
        btn_row.addStretch()

        self.code_path_label = QLabel("未加载文件")
        self.code_path_label.setStyleSheet("color: #888; font-size: 12px;")
        btn_row.addWidget(self.code_path_label)

        layout.addLayout(btn_row)

        self.code_editor = QTextEdit()
        self.code_editor.setStyleSheet("""
            QTextEdit { background: #1e1e1e; color: #d4d4d4; border: 1px solid #3d3d3d; border-radius: 6px;
                       padding: 12px; font-family: Consolas, monospace; font-size: 12px; }
        """)
        self.code_editor.setPlaceholderText("在此粘贴或加载插件 Python 代码...\n\n必需函数：\ndef main(context):\n    return {'status': 'success'}\n\n可选函数：\ndef build_page_settings(context, parent=None):\n    # 构建设置页面\n    return QWidget()")
        layout.addWidget(self.code_editor, 1)

        self.tabs.addTab(tab, "💻 代码编辑")

    def _build_pages_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        hint = QLabel("配置插件的设置页面，每个页面对应代码中的 build_page_<key> 函数")
        hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint)

        self.pages_list = QListWidget()
        self.pages_list.setStyleSheet("QListWidget { background: #fafafa; border: 1px solid #e5e5e5; border-radius: 6px; padding: 4px; } QListWidget::item { padding: 10px; border-radius: 4px; }")
        layout.addWidget(self.pages_list, 1)

        btn_row = QHBoxLayout()
        self.add_page_btn = QPushButton("➕ 添加页面")
        self.add_page_btn.clicked.connect(self._add_page)
        btn_row.addWidget(self.add_page_btn)

        self.remove_page_btn = QPushButton("➖ 删除选中")
        self.remove_page_btn.clicked.connect(self._remove_page)
        btn_row.addWidget(self.remove_page_btn)

        self.edit_page_btn = QPushButton("✏️ 编辑选中")
        self.edit_page_btn.clicked.connect(self._edit_page)
        btn_row.addWidget(self.edit_page_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.tabs.addTab(tab, "📄 页面配置")

    def _build_config_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        hint = QLabel("配置插件的默认设置项（JSON 格式），插件运行时可通过 context.get_config/set_config 访问")
        hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint)

        self.config_editor = QTextEdit()
        self.config_editor.setStyleSheet("""
            QTextEdit { background: #1e1e1e; color: #d4d4d4; border: 1px solid #3d3d3d; border-radius: 6px;
                       padding: 12px; font-family: Consolas, monospace; font-size: 12px; }
        """)
        self.config_editor.setPlaceholderText('{\n  "key1": "value1",\n  "key2": true,\n  "key3": 123\n}')
        layout.addWidget(self.config_editor, 1)

        btn_row = QHBoxLayout()
        self.format_json_btn = QPushButton("✨ 格式化 JSON")
        self.format_json_btn.clicked.connect(self._format_json)
        btn_row.addWidget(self.format_json_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.tabs.addTab(tab, "⚙️ 默认配置")

    def _build_preview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        hint = QLabel("预览打包后的 .arcx 文件结构（JSON 格式）")
        hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint)

        self.preview_editor = QTextEdit()
        self.preview_editor.setReadOnly(True)
        self.preview_editor.setStyleSheet("""
            QTextEdit { background: #f5f5f5; color: #333; border: 1px solid #e0e0e0; border-radius: 6px;
                       padding: 12px; font-family: Consolas, monospace; font-size: 11px; }
        """)
        layout.addWidget(self.preview_editor, 1)

        btn_row = QHBoxLayout()
        self.refresh_preview_btn = QPushButton("🔄 刷新预览")
        self.refresh_preview_btn.clicked.connect(self._refresh_preview)
        btn_row.addWidget(self.refresh_preview_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.tabs.addTab(tab, "👁️ 预览")

    def _load_defaults(self):
        self._pages = [
            {"key": "settings", "title": "插件设置", "icon": "settings"},
            {"key": "about", "title": "关于插件", "icon": "info"},
        ]
        self._refresh_pages_list()
        self.config_editor.setPlainText('{\n  "example_key": "example_value"\n}')

    def _load_template(self):
        template_path = os.path.join(BASE_DIR, "plugins", "示例插件.arcx")
        if not os.path.exists(template_path):
            QMessageBox.warning(self, "未找到模板", "示例插件模板不存在，请先运行主程序生成。")
            return
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("meta", {})
            self.name_input.setText(meta.get("name", ""))
            self.version_input.setText(meta.get("version", "1.0.0"))
            self.author_input.setText(meta.get("author", ""))
            self.desc_input.setPlainText(meta.get("description", ""))
            self.type_combo.setCurrentText(meta.get("type", "general"))
            self.api_spin.setValue(meta.get("api_version", 2))
            self.code_editor.setPlainText(data.get("code", ""))
            self._pages = meta.get("pages", [])
            self._refresh_pages_list()
            self.config_editor.setPlainText(json.dumps(data.get("config", {}), indent=2, ensure_ascii=False))
            self.code_path_label.setText("已加载：示例插件.arcx")
            QMessageBox.information(self, "加载成功", "示例插件模板已加载，可以在此基础上修改。")
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"加载模板失败：{str(e)}")

    def _load_code_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 Python 文件", "", "Python Files (*.py);;All Files (*.*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.code_editor.setPlainText(content)
            self.code_path_label.setText(f"已加载：{os.path.basename(path)}")
            if not self.name_input.text():
                self.name_input.setText(os.path.splitext(os.path.basename(path))[0])
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"加载文件失败：{str(e)}")

    def _paste_code(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.code_editor.setPlainText(text)
            self.code_path_label.setText("已从剪贴板粘贴")
        else:
            QMessageBox.information(self, "剪贴板为空", "剪贴板中没有文本内容。")

    def _add_page(self):
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("添加页面")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        key_input = QLineEdit()
        key_input.setPlaceholderText("例如：settings")
        form.addRow("页面Key*：", key_input)
        title_input = QLineEdit()
        title_input.setPlaceholderText("例如：插件设置")
        form.addRow("页面标题*：", title_input)
        icon_input = QComboBox()
        icon_input.addItems(["settings", "info", "zap", "puzzle", "chart", "book", "users", "palette", "database", "keyboard"])
        form.addRow("图标：", icon_input)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec_() == QDialog.Accepted:
            key = key_input.text().strip()
            title = title_input.text().strip()
            if not key or not title:
                QMessageBox.warning(self, "输入不完整", "请填写页面Key和标题。")
                return
            self._pages.append({"key": key, "title": title, "icon": icon_input.currentText()})
            self._refresh_pages_list()

    def _remove_page(self):
        current = self.pages_list.currentRow()
        if current < 0:
            QMessageBox.warning(self, "未选中", "请先选择要删除的页面。")
            return
        self._pages.pop(current)
        self._refresh_pages_list()

    def _edit_page(self):
        current = self.pages_list.currentRow()
        if current < 0:
            QMessageBox.warning(self, "未选中", "请先选择要编辑的页面。")
            return
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        page = self._pages[current]
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑页面")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        key_input = QLineEdit(page["key"])
        form.addRow("页面Key*：", key_input)
        title_input = QLineEdit(page["title"])
        form.addRow("页面标题*：", title_input)
        icon_input = QComboBox()
        icon_input.addItems(["settings", "info", "zap", "puzzle", "chart", "book", "users", "palette", "database", "keyboard"])
        icon_input.setCurrentText(page.get("icon", "settings"))
        form.addRow("图标：", icon_input)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec_() == QDialog.Accepted:
            page["key"] = key_input.text().strip()
            page["title"] = title_input.text().strip()
            page["icon"] = icon_input.currentText()
            self._refresh_pages_list()

    def _refresh_pages_list(self):
        self.pages_list.clear()
        for page in self._pages:
            item = QListWidgetItem(f"📄 {page['title']}  (key: {page['key']}, icon: {page.get('icon', 'settings')})")
            self.pages_list.addItem(item)

    def _format_json(self):
        try:
            content = self.config_editor.toPlainText()
            if not content.strip():
                return
            data = json.loads(content)
            self.config_editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "JSON 格式错误", f"JSON 格式错误：{str(e)}")

    def _build_arcx_data(self):
        name = self.name_input.text().strip()
        if not name:
            return None, "请填写插件名称"
        code = self.code_editor.toPlainText()
        if not code.strip():
            return None, "请填写或加载插件代码"
        try:
            config = json.loads(self.config_editor.toPlainText()) if self.config_editor.toPlainText().strip() else {}
        except json.JSONDecodeError as e:
            return None, f"默认配置 JSON 格式错误：{str(e)}"

        data = {
            "meta": {
                "name": name,
                "version": self.version_input.text().strip() or "1.0.0",
                "author": self.author_input.text().strip() or "匿名",
                "description": self.desc_input.toPlainText().strip(),
                "type": self.type_combo.currentText(),
                "api_version": self.api_spin.value(),
                "has_settings_page": len(self._pages) > 0,
                "pages": self._pages,
                "config": config
            },
            "code": code,
            "config": config,
            "enabled": True,
            "installed_at": datetime.now().isoformat()
        }
        return data, None

    def _refresh_preview(self):
        data, error = self._build_arcx_data()
        if error:
            self.preview_editor.setPlainText(f"❌ {error}")
            return
        preview = json.dumps(data, indent=2, ensure_ascii=False)
        if len(preview) > 5000:
            preview = preview[:5000] + "\n\n... (代码过长，已截断)"
        self.preview_editor.setPlainText(preview)

    def _package(self):
        data, error = self._build_arcx_data()
        if error:
            QMessageBox.warning(self, "打包失败", error)
            return
        default_name = f"{data['meta']['name']}.arcx"
        default_path = os.path.join(BASE_DIR, "plugins", default_name)
        path, _ = QFileDialog.getSaveFileName(self, "保存 .arcx 文件", default_path, "ARCX 插件文件 (*.arcx)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            size = os.path.getsize(path)
            QMessageBox.information(self, "打包成功",
                                    f"✅ 插件打包成功！\n\n"
                                    f"文件：{path}\n"
                                    f"大小：{size / 1024:.1f} KB\n\n"
                                    f"将此文件放到 plugins 目录，重启软件即可加载。")
        except Exception as e:
            QMessageBox.warning(self, "打包失败", f"保存文件失败：{str(e)}")

    def _generate_installer(self):
        data, error = self._build_arcx_data()
        if error:
            QMessageBox.warning(self, "生成失败", error)
            return

        meta = data['meta']
        plugin_name = meta['name']
        plugin_version = meta['version']
        plugin_author = meta.get('author', '匿名')
        plugin_desc = meta.get('description', '')

        template_path = os.path.join(BASE_DIR, "plugin_installer_template.py")
        if not os.path.exists(template_path):
            QMessageBox.warning(self, "模板缺失", f"安装程序模板不存在：{template_path}")
            return

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            plugin_json = json.dumps(data, ensure_ascii=False)
            plugin_data_b64 = base64.b64encode(plugin_json.encode('utf-8')).decode('utf-8')

            installer_code = template
            installer_code = installer_code.replace("__PLUGIN_NAME__", plugin_name)
            installer_code = installer_code.replace("__PLUGIN_VERSION__", plugin_version)
            installer_code = installer_code.replace("__PLUGIN_AUTHOR__", plugin_author)
            installer_code = installer_code.replace("__PLUGIN_DESC__", plugin_desc)
            installer_code = installer_code.replace('"__PLUGIN_DATA__"', f'"{plugin_data_b64}"')

            default_name = f"{plugin_name}_installer.py"
            default_path = os.path.join(BASE_DIR, default_name)
            path, _ = QFileDialog.getSaveFileName(self, "保存安装程序", default_path, "Python 文件 (*.py)")
            if not path:
                return

            with open(path, "w", encoding="utf-8") as f:
                f.write(installer_code)

            size = os.path.getsize(path)
            QMessageBox.information(self, "生成成功",
                                    f"✅ 安装程序生成成功！\n\n"
                                    f"文件：{path}\n"
                                    f"大小：{size / 1024:.1f} KB\n\n"
                                    f"运行方式：\n"
                                    f"python {os.path.basename(path)}\n\n"
                                    f"如需打包成 exe，请使用 PyInstaller：\n"
                                    f"pyinstaller --onefile --windowed --name {plugin_name}安装程序 {os.path.basename(path)}")
        except Exception as e:
            import traceback
            QMessageBox.warning(self, "生成失败", f"生成安装程序失败：{str(e)}\n\n{traceback.format_exc()}")

    def _generate_arcxpkg(self):
        data, error = self._build_arcx_data()
        if error:
            QMessageBox.warning(self, "打包失败", error)
            return

        meta = data['meta']
        plugin_name = meta['name']
        plugin_version = meta['version']

        libs_dir = QFileDialog.getExistingDirectory(
            self,
            "选择第三方依赖库目录（libs文件夹）\n\n该目录下应包含需要随插件一起分发的Python库，例如：\n- requests/\n- urllib3/\n- numpy/\n\n如果没有依赖库，请取消此步骤",
            BASE_DIR
        )

        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="a13_arcxpkg_")

        try:
            plugin_arcx_path = os.path.join(temp_dir, "plugin.arcx")
            with open(plugin_arcx_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            lib_count = 0
            if libs_dir and os.path.exists(libs_dir):
                target_libs = os.path.join(temp_dir, "libs")
                shutil.copytree(libs_dir, target_libs)
                lib_count = len(os.listdir(target_libs))

            install_config = {
                "plugin_name": plugin_name,
                "plugin_version": plugin_version,
                "has_libs": lib_count > 0,
                "lib_count": lib_count,
                "pack_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "format_version": "1.0"
            }
            with open(os.path.join(temp_dir, "install.json"), "w", encoding="utf-8") as f:
                json.dump(install_config, f, ensure_ascii=False, indent=2)

            default_name = f"{plugin_name}_v{plugin_version}.arcxpkg"
            default_path = os.path.join(BASE_DIR, default_name)
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存插件包", default_path, "插件包 (*.arcxpkg)"
            )
            if not save_path:
                return

            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zf.write(file_path, arcname)

            size = os.path.getsize(save_path)
            lib_info = f"\n包含 {lib_count} 个第三方依赖库" if lib_count > 0 else "\n不包含第三方依赖库"
            QMessageBox.information(
                self, "打包成功",
                f"✅ 插件包打包成功！\n\n"
                f"文件：{save_path}\n"
                f"大小：{size / 1024:.1f} KB"
                f"{lib_info}\n\n"
                f"安装方式：\n"
                f"1. 运行 plugin_installer.py\n"
                f"2. 选择此 .arcxpkg 文件\n"
                f"3. 点击开始安装\n"
                f"4. 重启主程序"
            )
        except Exception as e:
            import traceback
            QMessageBox.warning(self, "打包失败", f"生成插件包失败：{str(e)}\n\n{traceback.format_exc()}")
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ArcxPackager()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
