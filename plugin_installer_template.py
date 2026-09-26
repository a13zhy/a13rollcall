import sys
import os
import json
import base64
import zipfile
import io
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox,
                             QProgressBar, QTextEdit, QGroupBox, QFormLayout, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette

PLUGIN_NAME = "__PLUGIN_NAME__"
PLUGIN_VERSION = "__PLUGIN_VERSION__"
PLUGIN_AUTHOR = "__PLUGIN_AUTHOR__"
PLUGIN_DESC = "__PLUGIN_DESC__"
PLUGIN_DATA = "__PLUGIN_DATA__"


class PluginInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{PLUGIN_NAME} v{PLUGIN_VERSION} - 安装程序")
        self.setMinimumSize(600, 500)
        self.resize(650, 550)
        self._setup_ui()
        self._detect_plugins_dir()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 24, 30, 24)
        main_layout.setSpacing(16)

        title = QLabel(f"📦 {PLUGIN_NAME}")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0067c0;")
        main_layout.addWidget(title)

        version_label = QLabel(f"版本：{PLUGIN_VERSION}  |  作者：{PLUGIN_AUTHOR}")
        version_label.setStyleSheet("font-size: 13px; color: #666;")
        main_layout.addWidget(version_label)

        desc_label = QLabel(PLUGIN_DESC)
        desc_label.setStyleSheet("font-size: 13px; color: #555; line-height: 1.6;")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

        line = QLabel()
        line.setStyleSheet("background: #e0e0e0; max-height: 1px;")
        main_layout.addWidget(line)

        dir_group = QGroupBox("安装位置")
        dir_layout = QVBoxLayout(dir_group)

        dir_hint = QLabel("请选择 A13 课堂点名系统的 plugins 目录：")
        dir_hint.setStyleSheet("font-size: 12px; color: #666;")
        dir_layout.addWidget(dir_hint)

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("例如：D:\\a13rollcall_v6.8\\plugins")
        self.dir_input.setStyleSheet("QLineEdit { padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }")
        dir_row.addWidget(self.dir_input, 1)

        browse_btn = QPushButton("浏览...")
        browse_btn.setStyleSheet("QPushButton { background: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; padding: 8px 16px; font-size: 13px; } QPushButton:hover { background: #e0e0e0; }")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)

        dir_layout.addLayout(dir_row)
        main_layout.addWidget(dir_group)

        options_group = QGroupBox("安装选项")
        options_layout = QVBoxLayout(options_group)

        self.backup_check = QCheckBox("安装前备份已存在的同名插件")
        self.backup_check.setChecked(True)
        self.backup_check.setStyleSheet("font-size: 13px;")
        options_layout.addWidget(self.backup_check)

        self.create_shortcut_check = QCheckBox("在桌面创建插件说明快捷方式")
        self.create_shortcut_check.setChecked(False)
        self.create_shortcut_check.setStyleSheet("font-size: 13px;")
        options_layout.addWidget(self.create_shortcut_check)

        main_layout.addWidget(options_group)

        progress_group = QGroupBox("安装进度")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #ccc; border-radius: 4px; text-align: center; height: 24px; font-size: 12px; }
            QProgressBar::chunk { background: #0067c0; border-radius: 3px; }
        """)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit { background: #f8f8f8; border: 1px solid #e0e0e0; border-radius: 4px;
                       padding: 8px; font-family: Consolas, monospace; font-size: 11px; color: #555; }
        """)
        progress_layout.addWidget(self.log_text)

        main_layout.addWidget(progress_group, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("QPushButton { background: #f0f0f0; border: 1px solid #ccc; border-radius: 6px; padding: 10px 24px; font-size: 14px; font-weight: 600; } QPushButton:hover { background: #e0e0e0; }")
        self.cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(self.cancel_btn)

        self.install_btn = QPushButton("📥 安装")
        self.install_btn.setStyleSheet("QPushButton { background: #107c10; color: white; border: none; border-radius: 6px; padding: 10px 32px; font-size: 15px; font-weight: 700; } QPushButton:hover { background: #0e6c0e; }")
        self.install_btn.clicked.connect(self._install)
        btn_row.addWidget(self.install_btn)

        main_layout.addLayout(btn_row)

    def _detect_plugins_dir(self):
        possible_dirs = [
            os.path.join(os.path.dirname(sys.executable), "plugins"),
            os.path.join(os.getcwd(), "plugins"),
            "D:\\a13rollcall_v6.8\\plugins",
            "D:\\rollcall_tool_6.2TY\\plugins",
        ]
        for d in possible_dirs:
            if os.path.exists(d):
                self.dir_input.setText(d)
                self._log(f"自动检测到插件目录：{d}")
                return
        self._log("未自动检测到插件目录，请手动选择")

    def _browse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择插件目录", self.dir_input.text() or os.getcwd())
        if dir_path:
            self.dir_input.setText(dir_path)

    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def _install(self):
        target_dir = self.dir_input.text().strip()
        if not target_dir:
            QMessageBox.warning(self, "安装失败", "请选择插件目录！")
            return

        if not os.path.exists(target_dir):
            reply = QMessageBox.question(self, "目录不存在",
                                          f"目录 {target_dir} 不存在，是否创建？",
                                          QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(target_dir, exist_ok=True)
                except Exception as e:
                    QMessageBox.warning(self, "创建失败", f"创建目录失败：{str(e)}")
                    return
            else:
                return

        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(10)
        self._log("开始安装...")

        QTimer.singleShot(200, lambda: self._do_install(target_dir))

    def _do_install(self, target_dir):
        try:
            self.progress_bar.setValue(20)
            self._log(f"目标目录：{target_dir}")

            plugin_filename = f"{PLUGIN_NAME}.arcx"
            target_path = os.path.join(target_dir, plugin_filename)

            if os.path.exists(target_path) and self.backup_check.isChecked():
                backup_path = target_path + ".bak"
                self._log(f"备份已存在的插件：{backup_path}")
                shutil.copy2(target_path, backup_path)

            self.progress_bar.setValue(40)
            self._log("解压插件数据...")

            try:
                plugin_data = base64.b64decode(PLUGIN_DATA)
                with open(target_path, "wb") as f:
                    f.write(plugin_data)
            except Exception as e:
                self._log(f"直接写入失败，尝试zip解压：{str(e)}")
                plugin_data = base64.b64decode(PLUGIN_DATA)
                zip_buffer = io.BytesIO(plugin_data)
                with zipfile.ZipFile(zip_buffer, 'r') as zf:
                    for name in zf.namelist():
                        if name.endswith('.arcx'):
                            with zf.open(name) as src, open(target_path, 'wb') as dst:
                                dst.write(src.read())
                            break

            self.progress_bar.setValue(70)
            self._log(f"插件已写入：{target_path}")

            file_size = os.path.getsize(target_path)
            self._log(f"文件大小：{file_size / 1024:.1f} KB")

            if self.create_shortcut_check.isChecked():
                self._create_shortcut(target_path)

            self.progress_bar.setValue(90)
            self._log("验证安装...")

            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = data.get("meta", {})
                self._log(f"插件名称：{meta.get('name', '未知')}")
                self._log(f"插件版本：{meta.get('version', '未知')}")
                self._log(f"插件作者：{meta.get('author', '未知')}")
            except Exception as e:
                self._log(f"验证警告：{str(e)}")

            self.progress_bar.setValue(100)
            self._log("✅ 安装完成！")

            QMessageBox.information(self, "安装成功",
                                    f"✅ {PLUGIN_NAME} v{PLUGIN_VERSION} 安装成功！\n\n"
                                    f"安装位置：{target_path}\n\n"
                                    f"请重启 A13 课堂点名系统以加载插件。")
            self.close()

        except Exception as e:
            self._log(f"❌ 安装失败：{str(e)}")
            QMessageBox.warning(self, "安装失败", f"安装过程中出现错误：{str(e)}")
            self.install_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)

    def _create_shortcut(self, target_path):
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, f"{PLUGIN_NAME} 说明.txt")
            with open(shortcut_path, "w", encoding="utf-8") as f:
                f.write(f"{PLUGIN_NAME} v{PLUGIN_VERSION}\n")
                f.write(f"作者：{PLUGIN_AUTHOR}\n")
                f.write(f"描述：{PLUGIN_DESC}\n\n")
                f.write(f"插件文件位置：{target_path}\n\n")
                f.write("使用说明：\n")
                f.write("1. 重启 A13 课堂点名系统\n")
                f.write("2. 打开设置 -> 插件管理\n")
                f.write(f"3. 找到 {PLUGIN_NAME} 并启用\n")
            self._log(f"已创建桌面说明：{shortcut_path}")
        except Exception as e:
            self._log(f"创建桌面说明失败：{str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#fafafa"))
    palette.setColor(QPalette.WindowText, QColor("#333"))
    app.setPalette(palette)

    window = PluginInstaller()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
