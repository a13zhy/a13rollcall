"""
A13课堂点名系统 - 插件安装程序
支持 .arcxpkg 格式（包含插件代码和第三方依赖库）
"""

import os
import sys
import json
import zipfile
import shutil
import tempfile
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTextEdit, QProgressBar,
    QGroupBox, QMessageBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap


class PluginInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A13课堂点名系统 - 插件安装程序")
        self.setMinimumSize(700, 600)
        self.setStyleSheet("""
            QMainWindow { background: #f3f3f3; }
            QLabel { color: #1a1a1a; }
            QPushButton {
                background: #0067c0; color: white; border: none;
                border-radius: 6px; padding: 10px 24px; font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background: #005a9e; }
            QPushButton:disabled { background: #cccccc; color: #999; }
            QPushButton#secondary {
                background: white; color: #0067c0; border: 1px solid #0067c0;
            }
            QPushButton#secondary:hover { background: #e5f1fb; }
            QTextEdit {
                background: white; border: 1px solid #d1d1d1; border-radius: 6px;
                padding: 10px; font-family: Consolas, monospace; font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #d1d1d1; border-radius: 6px; text-align: center;
                height: 24px; background: white;
            }
            QProgressBar::chunk { background: #0067c0; border-radius: 5px; }
            QGroupBox {
                border: 1px solid #d1d1d1; border-radius: 8px; margin-top: 12px;
                padding-top: 16px; background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 16px; padding: 0 8px;
                color: #0067c0; font-weight: 600;
            }
        """)

        self._temp_dir = None
        self._plugin_info = None
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 标题
        title = QLabel("📦 插件安装程序")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #0067c0;")
        layout.addWidget(title)

        subtitle = QLabel("支持安装 .arcxpkg 格式的插件包（包含插件代码和第三方依赖库）")
        subtitle.setStyleSheet("font-size: 13px; color: #666;")
        layout.addWidget(subtitle)

        # 步骤1：选择文件
        step1_group = QGroupBox("步骤 1：选择插件包")
        step1_layout = QVBoxLayout(step1_group)
        step1_layout.setSpacing(12)

        file_row = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("""
            QLabel { background: #f9f9f9; border: 1px dashed #ccc;
                     border-radius: 6px; padding: 12px; color: #999; }
        """)
        self.file_label.setMinimumHeight(48)
        file_row.addWidget(self.file_label, 1)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self.browse_btn)

        step1_layout.addLayout(file_row)
        layout.addWidget(step1_group)

        # 步骤2：插件信息
        self.info_group = QGroupBox("步骤 2：插件信息")
        self.info_layout = QVBoxLayout(self.info_group)
        self.info_layout.setSpacing(8)

        self.info_placeholder = QLabel("请先选择插件包文件")
        self.info_placeholder.setStyleSheet("color: #999; padding: 20px;")
        self.info_placeholder.setAlignment(Qt.AlignCenter)
        self.info_layout.addWidget(self.info_placeholder)

        self.info_content = QWidget()
        self.info_content_layout = QVBoxLayout(self.info_content)
        self.info_content_layout.setSpacing(6)
        self.info_content.hide()
        self.info_layout.addWidget(self.info_content)

        layout.addWidget(self.info_group)

        # 步骤3：安装进度
        self.progress_group = QGroupBox("步骤 3：安装进度")
        progress_layout = QVBoxLayout(self.progress_group)
        progress_layout.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("等待开始安装...")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        progress_layout.addWidget(self.status_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setPlaceholderText("安装日志将显示在这里...")
        progress_layout.addWidget(self.log_text)

        layout.addWidget(self.progress_group)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.install_btn = QPushButton("开始安装")
        self.install_btn.clicked.connect(self._start_install)
        self.install_btn.setEnabled(False)
        btn_row.addWidget(self.install_btn)

        self.close_btn = QPushButton("关闭")
        self.close_btn.setObjectName("secondary")
        self.close_btn.clicked.connect(self.close)
        btn_row.addWidget(self.close_btn)

        layout.addLayout(btn_row)

    def _log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {"INFO": "#333", "SUCCESS": "#107c10", "WARNING": "#ca5010", "ERROR": "#d13438"}.get(level, "#333")
        self.log_text.append(f'<span style="color:#888">[{timestamp}]</span> <span style="color:{color}">[{level}]</span> {message}')

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择插件包", "", "插件包 (*.arcxpkg *.zip);;所有文件 (*.*)"
        )
        if file_path:
            self._validate_package(file_path)

    def _validate_package(self, file_path):
        self._log(f"正在验证插件包：{os.path.basename(file_path)}")
        self.file_label.setText(os.path.basename(file_path))
        self.file_label.setStyleSheet("""
            QLabel { background: #e5f1fb; border: 1px solid #0067c0;
                     border-radius: 6px; padding: 12px; color: #0067c0; }
        """)

        try:
            # 创建临时目录
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = tempfile.mkdtemp(prefix="a13_plugin_")

            # 解压
            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(self._temp_dir)

            self._log("插件包解压成功")

            # 查找 plugin.arcx
            plugin_arcx = os.path.join(self._temp_dir, "plugin.arcx")
            if not os.path.exists(plugin_arcx):
                # 尝试查找根目录下的 .arcx 文件
                arcx_files = [f for f in os.listdir(self._temp_dir) if f.endswith('.arcx')]
                if arcx_files:
                    plugin_arcx = os.path.join(self._temp_dir, arcx_files[0])
                else:
                    raise Exception("未找到 plugin.arcx 文件")

            # 读取插件信息
            with open(plugin_arcx, 'r', encoding='utf-8') as f:
                plugin_data = json.load(f)

            meta = plugin_data.get('meta', {})
            self._plugin_info = {
                'name': meta.get('name', '未知插件'),
                'version': meta.get('version', '0.0.0'),
                'author': meta.get('author', '未知'),
                'description': meta.get('description', '无描述'),
                'type': meta.get('type', 'general'),
                'api_version': meta.get('api_version', '1.0'),
                'pages': meta.get('pages', []),
                'arcx_path': plugin_arcx,
            }

            # 检查依赖库
            libs_dir = os.path.join(self._temp_dir, "libs")
            has_libs = os.path.exists(libs_dir)
            lib_count = 0
            if has_libs:
                lib_count = len(os.listdir(libs_dir))
            self._plugin_info['has_libs'] = has_libs
            self._plugin_info['lib_count'] = lib_count
            self._plugin_info['libs_dir'] = libs_dir

            self._log(f"插件信息读取成功：{self._plugin_info['name']} v{self._plugin_info['version']}")
            if has_libs:
                self._log(f"检测到 {lib_count} 个第三方依赖库")

            self._show_plugin_info()
            self.install_btn.setEnabled(True)

        except Exception as e:
            self._log(f"插件包验证失败：{str(e)}", "ERROR")
            QMessageBox.critical(self, "验证失败", f"插件包验证失败：\n{str(e)}")
            self.install_btn.setEnabled(False)

    def _show_plugin_info(self):
        # 清除旧内容
        while self.info_content_layout.count():
            item = self.info_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        info = self._plugin_info

        # 插件名称和版本
        name_row = QHBoxLayout()
        name_label = QLabel(f"📦 {info['name']}")
        name_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #1a1a1a;")
        name_row.addWidget(name_label)

        version_label = QLabel(f"v{info['version']}")
        version_label.setStyleSheet("""
            QLabel { background: #0067c0; color: white; border-radius: 10px;
                     padding: 2px 10px; font-size: 12px; font-weight: 600; }
        """)
        name_row.addWidget(version_label)
        name_row.addStretch()
        self.info_content_layout.addLayout(name_row)

        # 作者
        author_label = QLabel(f"👤 作者：{info['author']}")
        author_label.setStyleSheet("color: #555; font-size: 13px;")
        self.info_content_layout.addWidget(author_label)

        # 类型
        type_label = QLabel(f"🏷️  类型：{info['type']}  |  API版本：{info['api_version']}")
        type_label.setStyleSheet("color: #555; font-size: 13px;")
        self.info_content_layout.addWidget(type_label)

        # 描述
        desc_label = QLabel(f"📝 {info['description']}")
        desc_label.setStyleSheet("color: #333; font-size: 13px; padding: 8px; background: #f9f9f9; border-radius: 6px;")
        desc_label.setWordWrap(True)
        self.info_content_layout.addWidget(desc_label)

        # 页面
        if info['pages']:
            pages_text = "、".join([p.get('title', p.get('key', '')) for p in info['pages']])
            pages_label = QLabel(f"📄 包含页面：{pages_text}")
            pages_label.setStyleSheet("color: #555; font-size: 13px;")
            self.info_content_layout.addWidget(pages_label)

        # 依赖库
        if info['has_libs']:
            libs_label = QLabel(f"📚 包含 {info['lib_count']} 个第三方依赖库（将自动安装到插件数据目录）")
            libs_label.setStyleSheet("""
                QLabel { color: #ca5010; font-size: 13px; padding: 8px;
                         background: #fff4ce; border-radius: 6px; }
            """)
            self.info_content_layout.addWidget(libs_label)

        self.info_placeholder.hide()
        self.info_content.show()

    def _start_install(self):
        if not self._plugin_info:
            return

        self.install_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self._log("开始安装插件...")

        QTimer.singleShot(100, self._do_install)

    def _do_install(self):
        try:
            info = self._plugin_info
            base_dir = os.path.dirname(os.path.abspath(__file__))
            plugins_dir = os.path.join(base_dir, "plugins")
            plugin_data_dir = os.path.join(plugins_dir, "data", info['name'])
            plugin_libs_dir = os.path.join(plugin_data_dir, "libs")

            # 确保目录存在
            os.makedirs(plugins_dir, exist_ok=True)
            os.makedirs(plugin_data_dir, exist_ok=True)

            self.progress_bar.setValue(20)
            self.status_label.setText("正在复制插件文件...")
            self._log(f"插件目录：{plugins_dir}")

            # 复制 plugin.arcx
            target_arcx = os.path.join(plugins_dir, f"{info['name']}.arcx")
            shutil.copy2(info['arcx_path'], target_arcx)
            self._log(f"✅ 插件文件已复制：{os.path.basename(target_arcx)}")

            self.progress_bar.setValue(50)

            # 复制依赖库
            if info['has_libs'] and os.path.exists(info['libs_dir']):
                self.status_label.setText("正在安装第三方依赖库...")
                self._log(f"依赖库目录：{plugin_libs_dir}")

                if os.path.exists(plugin_libs_dir):
                    shutil.rmtree(plugin_libs_dir)
                shutil.copytree(info['libs_dir'], plugin_libs_dir)

                lib_items = os.listdir(plugin_libs_dir)
                self._log(f"✅ 已安装 {len(lib_items)} 个依赖库：{', '.join(lib_items[:10])}")

            self.progress_bar.setValue(80)
            self.status_label.setText("正在完成安装...")

            # 写入安装记录
            install_record = {
                'name': info['name'],
                'version': info['version'],
                'author': info['author'],
                'install_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'has_libs': info['has_libs'],
                'lib_count': info['lib_count'],
            }
            record_file = os.path.join(plugin_data_dir, "install_record.json")
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(install_record, f, ensure_ascii=False, indent=2)

            self._log("✅ 安装记录已写入")

            self.progress_bar.setValue(100)
            self.status_label.setText("安装完成！")
            self._log(f"🎉 插件 {info['name']} v{info['version']} 安装成功！", "SUCCESS")

            QMessageBox.information(
                self, "安装成功",
                f"插件 {info['name']} v{info['version']} 安装成功！\n\n"
                f"请重启 A13课堂点名系统 以加载此插件。"
            )

        except Exception as e:
            self._log(f"安装失败：{str(e)}", "ERROR")
            QMessageBox.critical(self, "安装失败", f"插件安装失败：\n{str(e)}")
        finally:
            self.install_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            # 清理临时目录
            if self._temp_dir and os.path.exists(self._temp_dir):
                try:
                    shutil.rmtree(self._temp_dir, ignore_errors=True)
                except Exception:
                    pass

    def closeEvent(self, event):
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置应用图标
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = PluginInstaller()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
