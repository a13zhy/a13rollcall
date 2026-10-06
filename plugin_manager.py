import os
import json
import sys
import traceback
from datetime import datetime
from collections import defaultdict


class PluginLogger:
    def __init__(self, plugin_name, log_dir):
        self.plugin_name = plugin_name
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, f"{plugin_name}.log")
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _write(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass

    def info(self, message):
        self._write("INFO", message)

    def warning(self, message):
        self._write("WARNING", message)

    def error(self, message):
        self._write("ERROR", message)

    def debug(self, message):
        self._write("DEBUG", message)

    def get_logs(self, lines=100):
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            return all_lines[-lines:]
        except Exception:
            return []

    def clear(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)


class PluginDataManager:
    def __init__(self, plugin_name, data_dir):
        self.plugin_name = plugin_name
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "config.json")
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def load_config(self):
        if not os.path.exists(self.config_file):
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_config(self, config):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def get(self, key, default=None):
        config = self.load_config()
        return config.get(key, default)

    def set(self, key, value):
        config = self.load_config()
        config[key] = value
        return self.save_config(config)

    def get_data_file(self, filename):
        return os.path.join(self.data_dir, filename)

    def read_data(self, filename):
        file_path = self.get_data_file(filename)
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def write_data(self, filename, content):
        file_path = self.get_data_file(filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def read_json(self, filename):
        content = self.read_data(filename)
        if content:
            try:
                return json.loads(content)
            except Exception:
                return None
        return None

    def write_json(self, filename, data):
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2)
            return self.write_data(filename, content)
        except Exception:
            return False


class ArcxParser:
    MAGIC = "ARCX"
    VERSION = 1

    @staticmethod
    def parse(file_path):
        if not os.path.exists(file_path):
            return None, "文件不存在"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content.startswith("ARCX"):
                return ArcxParser._parse_binary(content)
            else:
                data = json.loads(content)
                return ArcxParser._validate(data), None
        except json.JSONDecodeError as e:
            return None, f"JSON 解析错误：{str(e)}"
        except Exception as e:
            return None, f"解析失败：{str(e)}"

    @staticmethod
    def _parse_binary(content):
        try:
            lines = content.split("\n")
            meta = {}
            code_start = -1
            for i, line in enumerate(lines):
                if line.startswith("META:"):
                    meta_part = line[5:].strip()
                    meta = json.loads(meta_part)
                elif line.startswith("CODE:"):
                    code_start = i + 1
                    break
            code = "\n".join(lines[code_start:]) if code_start > 0 else ""
            data = {
                "meta": meta,
                "code": code,
                "config": meta.get("config", {})
            }
            return ArcxParser._validate(data), None
        except Exception as e:
            return None, f"二进制格式解析失败：{str(e)}"

    @staticmethod
    def _validate(data):
        required = ["meta", "code"]
        for key in required:
            if key not in data:
                data[key] = {} if key == "meta" else ""
        meta = data.get("meta", {})
        meta.setdefault("name", "未命名插件")
        meta.setdefault("version", "1.0.0")
        meta.setdefault("author", "未知")
        meta.setdefault("description", "")
        meta.setdefault("type", "general")
        meta.setdefault("api_version", 1)
        meta.setdefault("has_settings_page", False)
        meta.setdefault("settings_page_title", "")
        data["meta"] = meta
        data.setdefault("config", {})
        data.setdefault("enabled", True)
        data.setdefault("installed_at", datetime.now().isoformat())
        return data

    @staticmethod
    def create_arcx(name, description, code, config=None, author="自定义", version="1.0.0", has_settings_page=False):
        data = {
            "meta": {
                "name": name,
                "version": version,
                "author": author,
                "description": description,
                "type": "general",
                "api_version": 1,
                "has_settings_page": has_settings_page,
                "settings_page_title": name,
                "config": config or {}
            },
            "code": code,
            "config": config or {}
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


class PluginContext:
    def __init__(self, plugin, app, plugin_mgr):
        self.plugin = plugin
        self.app = app
        self.plugin_mgr = plugin_mgr
        self._variables = {}
        self._ui_elements = []
        self._event_handlers = defaultdict(list)
        self._loaded_libs = []
        plugin_name = plugin["meta"]["name"]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(base_dir, "plugins", "data", plugin_name)
        self.libs_dir = os.path.join(self.data_dir, "libs")
        self.log_dir = os.path.join(base_dir, "plugins", "logs")
        self.logger = PluginLogger(plugin_name, self.log_dir)
        self.data = PluginDataManager(plugin_name, self.data_dir)
        self._load_plugin_libs()
        self.logger.info(f"插件上下文初始化完成，数据目录：{self.data_dir}")

    def _load_plugin_libs(self):
        """加载插件自带的依赖库到sys.path"""
        if os.path.exists(self.libs_dir):
            if self.libs_dir not in sys.path:
                sys.path.insert(0, self.libs_dir)
                self._loaded_libs.append(self.libs_dir)
                self.logger.info(f"已加载插件依赖库目录：{self.libs_dir}")
            # 检查libs目录下的内容
            try:
                lib_items = os.listdir(self.libs_dir)
                self.logger.info(f"插件依赖库包含 {len(lib_items)} 个项目：{', '.join(lib_items[:10])}")
            except Exception as e:
                self.logger.warning(f"读取依赖库目录失败：{e}")

    def get_libs_dir(self):
        """获取插件依赖库目录"""
        return self.libs_dir

    def get_icons_dir(self):
        """获取插件图标资源目录"""
        return os.path.join(self.data_dir, "icons")

    def has_icon(self, icon_name):
        """检查插件是否包含某个图标"""
        icons_dir = self.get_icons_dir()
        for ext in ['.ico', '.png', '.svg']:
            icon_path = os.path.join(icons_dir, icon_name + ext)
            if os.path.exists(icon_path):
                return True
        return os.path.exists(os.path.join(icons_dir, icon_name))

    def get_icon_path(self, icon_name):
        """获取插件图标的完整路径"""
        icons_dir = self.get_icons_dir()
        for ext in ['.ico', '.png', '.svg']:
            icon_path = os.path.join(icons_dir, icon_name + ext)
            if os.path.exists(icon_path):
                return icon_path
        direct_path = os.path.join(icons_dir, icon_name)
        if os.path.exists(direct_path):
            return direct_path
        return None

    def list_icons(self):
        """列出插件自带的所有图标"""
        icons_dir = self.get_icons_dir()
        if not os.path.exists(icons_dir):
            return []
        try:
            return [f for f in os.listdir(icons_dir) if f.endswith(('.ico', '.png', '.svg'))]
        except Exception:
            return []

    def load_icon(self, icon_name):
        """加载插件图标为 QIcon"""
        try:
            from PyQt5.QtGui import QIcon
            icon_path = self.get_icon_path(icon_name)
            if icon_path:
                return QIcon(icon_path)
        except Exception as e:
            self.logger.error(f"加载图标失败: {e}")
        return None

    def has_lib(self, lib_name):
        """检查插件是否自带某个依赖库"""
        lib_path = os.path.join(self.libs_dir, lib_name)
        return os.path.exists(lib_path) or os.path.exists(lib_path + ".py")

    def list_libs(self):
        """列出插件自带的所有依赖库"""
        if not os.path.exists(self.libs_dir):
            return []
        try:
            return os.listdir(self.libs_dir)
        except Exception:
            return []

    def set(self, key, value):
        self._variables[key] = value
        self.logger.debug(f"设置变量 {key} = {value}")

    def get(self, key, default=None):
        return self._variables.get(key, default)

    def show_message(self, title, message):
        from PyQt5.QtWidgets import QMessageBox
        from PyQt5.QtCore import Qt
        self.logger.info(f"显示消息框：{title}")
        try:
            box = QMessageBox(self._app.activeWindow() if getattr(self, "_app", None) else None)
            box.setWindowTitle(title)
            box.setText(message)
            box.setIcon(QMessageBox.Information)
            box.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            box.show()
        except Exception:
            QMessageBox.information(None, title, message)

    def show_custom_dialog(self, title, content, buttons=None):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        self.logger.info(f"显示自定义对话框：{title}")
        dlg = QDialog()
        dlg.setWindowTitle(title)
        dlg.setMinimumSize(400, 300)
        layout = QVBoxLayout(dlg)
        if isinstance(content, str):
            label = QLabel(content)
            label.setWordWrap(True)
            layout.addWidget(label)
        btn_layout = QHBoxLayout()
        buttons = buttons or ["确定"]
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            btn.clicked.connect(dlg.accept)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        dlg.exec_()
        return True

    def get_config(self, key, default=None):
        return self.data.get(key, default)

    def set_config(self, key, value):
        self.logger.info(f"保存配置 {key} = {value}")
        return self.data.set(key, value)

    def is_frozen(self):
        """检测是否在打包环境（PyInstaller）中运行"""
        return getattr(sys, 'frozen', False)

    def get_app_dir(self):
        """获取应用程序目录（兼容打包环境和源码运行）"""
        if self.is_frozen():
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def get_python_version(self):
        """获取Python版本信息"""
        return {
            "version": sys.version,
            "version_info": {
                "major": sys.version_info.major,
                "minor": sys.version_info.minor,
                "micro": sys.version_info.micro,
            },
            "executable": sys.executable,
            "frozen": self.is_frozen()
        }

    def check_dependency(self, module_name):
        """检查依赖模块是否可用"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    def get_available_modules(self):
        """获取常用模块的可用状态"""
        common_modules = [
            "os", "sys", "json", "re", "math", "random", "datetime",
            "subprocess", "threading", "socket", "urllib", "http",
            "PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets",
            "numpy", "requests", "PIL", "cv2", "pandas", "matplotlib",
            "websockets", "flask", "serial", "pygame"
        ]
        available = {}
        for module in common_modules:
            available[module] = self.check_dependency(module)
        return available

    def get_resource_path(self, relative_path):
        """获取资源文件路径（兼容打包环境）"""
        if self.is_frozen():
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else self.get_app_dir()
            return os.path.join(base_path, relative_path)
        return os.path.join(self.get_app_dir(), relative_path)

    def get_students(self):
        if hasattr(self.app, '_students'):
            return self.app._students
        return []

    def get_current_student(self):
        if hasattr(self.app, '_current_student'):
            return self.app._current_student
        return None

    def get_draw_state(self):
        is_drawing = False
        drawn_count = 0
        remaining = 0
        if hasattr(self.app, '_is_drawing'):
            is_drawing = self.app._is_drawing
        if hasattr(self.app, '_drawn_students'):
            drawn_count = len(self.app._drawn_students)
        students = self.get_students()
        remaining = max(0, len(students) - drawn_count)
        return {
            "is_drawing": is_drawing,
            "drawn_count": drawn_count,
            "remaining": remaining,
            "total": len(students),
            "current": self.get_current_student(),
            "last_result": self.get_last_draw_result(),
        }

    def get_all_stats(self):
        stats = {
            "已背过": 0,
            "未背熟": 0,
            "未背过": 0,
            "未标记": 0,
        }
        try:
            if hasattr(self.app, 'data_mgr') and self.app.data_mgr:
                if hasattr(self.app.data_mgr, 'get_status_stats'):
                    data_stats = self.app.data_mgr.get_status_stats()
                    if data_stats:
                        stats.update(data_stats)
                elif hasattr(self.app.data_mgr, 'status_stats'):
                    stats.update(self.app.data_mgr.status_stats)
        except Exception as e:
            self.logger.error(f"获取统计失败: {e}")
        return stats

    def get_drawn_students(self):
        if hasattr(self.app, '_drawn_students'):
            return list(self.app._drawn_students)
        return []

    def get_remaining_students(self):
        all_students = self.get_students()
        drawn = self.get_drawn_students()
        return [s for s in all_students if s not in drawn]

    def get_last_draw_result(self):
        if hasattr(self.app, '_last_draw_result') and self.app._last_draw_result:
            return self.app._last_draw_result
        return None

    def get_window_state(self):
        is_drawing = False
        is_minimized = False
        is_quick_mode = False
        state = "main"
        current_window = "主界面"

        if hasattr(self.app, '_is_drawing'):
            is_drawing = self.app._is_drawing
        if hasattr(self.app, 'isMinimized'):
            try:
                is_minimized = self.app.isMinimized()
            except Exception:
                pass
        if hasattr(self.app, '_quick_mode'):
            is_quick_mode = self.app._quick_mode

        if is_minimized:
            state = "minimized"
            current_window = "最小化"
        elif is_drawing:
            state = "drawing"
            current_window = "正在抽取"
        elif is_quick_mode:
            state = "quick"
            current_window = "快捷抽取"
        else:
            state = "main"
            current_window = "主界面"

        return {
            "state": state,
            "is_drawing": is_drawing,
            "is_minimized": is_minimized,
            "is_quick_mode": is_quick_mode,
            "current_window": current_window
        }

    def trigger_draw(self):
        self.logger.info("触发抽取")
        if hasattr(self.app, '_start_draw'):
            self.app._start_draw()

    def add_status_bar_text(self, text):
        self.logger.debug(f"状态栏文本：{text}")
        if hasattr(self.app, 'statusBar'):
            self.app.statusBar().showMessage(text, 5000)

    def log(self, message):
        self.logger.info(message)

    def log_info(self, message):
        self.logger.info(message)

    def log_error(self, message):
        self.logger.error(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_debug(self, message):
        self.logger.debug(message)

    def log_success(self, message):
        self.logger.info(f"✅ {message}")

    def log_failure(self, message):
        self.logger.error(f"❌ {message}")

    def register_event_handler(self, event_name, handler):
        self._event_handlers[event_name].append(handler)
        self.logger.info(f"注册事件处理器：{event_name}")

    def emit_event(self, event_name, *args, **kwargs):
        self.logger.debug(f"触发事件：{event_name}")
        for handler in self._event_handlers.get(event_name, []):
            try:
                handler(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"事件处理器执行错误：{str(e)}")

    def get_logs(self, lines=100):
        return self.logger.get_logs(lines)

    def clear_logs(self):
        self.logger.clear()
        self.logger.info("日志已清空")

    def get_app_config(self, key, default=None):
        if hasattr(self.app, 'config_mgr') and self.app.config_mgr:
            try:
                value = self.app.config_mgr.get(key)
                if value is not None:
                    return value
            except Exception:
                pass
        return default

    def set_app_config(self, key, value):
        if hasattr(self.app, 'config_mgr') and self.app.config_mgr:
            self.app.config_mgr.set(key, value)
            self.logger.info(f"修改应用配置 {key} = {value}")
            return True
        return False

    def restart_application(self, delay=1000):
        self.logger.info("请求重启应用")
        if hasattr(self.app, '_restart_application'):
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(delay, self.app._restart_application)
            return True
        return False

    def get_theme(self):
        if hasattr(self.app, 'theme_mgr') and self.app.theme_mgr:
            if hasattr(self.app.theme_mgr, 'current_theme'):
                return self.app.theme_mgr.current_theme
            if hasattr(self.app.theme_mgr, '_current_theme'):
                return self.app.theme_mgr._current_theme
        return "light"

    def set_theme(self, theme_name):
        if hasattr(self.app, 'theme_mgr') and self.app.theme_mgr:
            self.app.theme_mgr.set_theme(theme_name)
            self.logger.info(f"切换主题到 {theme_name}")
            return True
        return False

    def get_class_name(self):
        if hasattr(self.app, '_get_class_name'):
            return self.app._get_class_name()
        return "课堂点名"

    def show_toast(self, message, duration=2000):
        self.logger.info(f"显示提示：{message}")
        if hasattr(self.app, '_show_toast'):
            self.app._show_toast(message, duration)
            return True
        return False

    def render_markdown(self, markdown_text):
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from main_qt import MarkdownRenderer
            return MarkdownRenderer.render(markdown_text)
        except Exception as e:
            self.logger.error(f"Markdown 渲染失败：{str(e)}")
            return markdown_text

    def create_markdown_view(self, parent=None):
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from main_qt import MarkdownView
            return MarkdownView(parent)
        except Exception as e:
            self.logger.error(f"创建 Markdown 视图失败：{str(e)}")
            from PyQt5.QtWidgets import QTextEdit
            view = QTextEdit(parent)
            view.setReadOnly(True)
            return view

    def get_plugin_pages(self):
        meta = self.plugin.get("meta", {})
        return meta.get("pages", [])

    def build_plugin_page(self, page_key, parent=None):
        try:
            code = self.plugin.get("code", "")
            if not code.strip():
                self.logger.error(f"插件代码为空")
                return None
            exec_globals = self._get_exec_globals()
            try:
                exec(code, exec_globals)
            except Exception as e:
                self.logger.error(f"执行插件代码失败：{str(e)}\n{traceback.format_exc()}")
                return None
            func_name = f"build_page_{page_key}"
            if func_name not in exec_globals:
                available = [k for k in exec_globals.keys() if k.startswith('build_')]
                self.logger.error(f"未找到函数 {func_name}，可用函数：{available}")
                return None
            func = exec_globals[func_name]
            if not callable(func):
                self.logger.error(f"{func_name} 不是可调用对象")
                return None
            try:
                if parent:
                    return func(self, parent)
                return func(self)
            except Exception as e:
                self.logger.error(f"调用 {func_name} 失败：{str(e)}\n{traceback.format_exc()}")
                return None
        except Exception as e:
            self.logger.error(f"构建插件页面 {page_key} 失败：{str(e)}\n{traceback.format_exc()}")
            return None

    def _get_exec_globals(self):
        import datetime as _dt_module
        from datetime import datetime, timedelta, date
        import os
        import sys
        import json
        import time
        import random
        import math
        import re
        import traceback
        import hashlib
        import csv
        import collections
        import urllib.request
        from pathlib import Path
        from typing import List, Dict, Optional, Tuple, Any, Callable
        try:
            from PyQt5.QtCore import (Qt, QTimer, QUrl, QThread, pyqtSignal,
                                      QObject, QSize, QPoint, QRect)
            from PyQt5.QtWidgets import (QWidget, QDialog, QMessageBox, QInputDialog,
                                         QLineEdit, QTextEdit, QLabel, QPushButton,
                                         QVBoxLayout, QHBoxLayout, QFormLayout,
                                         QListWidget, QListWidgetItem, QComboBox,
                                         QCheckBox, QSpinBox, QDoubleSpinBox,
                                         QTableWidget, QTableWidgetItem, QHeaderView,
                                         QFileDialog, QProgressBar, QGroupBox,
                                         QTabWidget, QScrollArea, QFrame, QApplication)
            from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont, QPalette
            _qt_ok = True
        except Exception:
            _qt_ok = False

        def _plugin_print(*args, **kwargs):
            message = " ".join(str(a) for a in args)
            self.logger.info(message)
        g = {
            'context': self,
            'plugin': self.plugin,
            'app': self.app,
            'print': _plugin_print,
            '__name__': 'plugin_exec',
            'datetime': datetime,
            'timedelta': timedelta,
            'date': date,
            'datetime_module': _dt_module,
            'os': os,
            'sys': sys,
            'json': json,
            'time': time,
            'random': random,
            'math': math,
            're': re,
            'traceback': traceback,
            'hashlib': hashlib,
            'csv': csv,
            'urllib_request': urllib.request,
            'collections': collections,
            'Path': Path,
            'List': List,
            'Dict': Dict,
            'Optional': Optional,
            'Tuple': Tuple,
            'Any': Any,
            'Callable': Callable,
        }
        if _qt_ok:
            g.update({
                'Qt': Qt, 'QTimer': QTimer, 'QUrl': QUrl, 'QThread': QThread,
                'QObject': QObject, 'pyqtSignal': pyqtSignal, 'QSize': QSize,
                'QPoint': QPoint, 'QRect': QRect,
                'QWidget': QWidget, 'QDialog': QDialog, 'QMessageBox': QMessageBox,
                'QInputDialog': QInputDialog, 'QLineEdit': QLineEdit,
                'QTextEdit': QTextEdit, 'QLabel': QLabel, 'QPushButton': QPushButton,
                'QVBoxLayout': QVBoxLayout, 'QHBoxLayout': QHBoxLayout,
                'QFormLayout': QFormLayout, 'QListWidget': QListWidget,
                'QListWidgetItem': QListWidgetItem, 'QComboBox': QComboBox,
                'QCheckBox': QCheckBox, 'QSpinBox': QSpinBox,
                'QDoubleSpinBox': QDoubleSpinBox, 'QTableWidget': QTableWidget,
                'QTableWidgetItem': QTableWidgetItem, 'QHeaderView': QHeaderView,
                'QFileDialog': QFileDialog, 'QProgressBar': QProgressBar,
                'QGroupBox': QGroupBox, 'QTabWidget': QTabWidget,
                'QScrollArea': QScrollArea, 'QFrame': QFrame,
                'QApplication': QApplication,
                'QIcon': QIcon, 'QPixmap': QPixmap, 'QColor': QColor,
                'QFont': QFont, 'QPalette': QPalette,
            })
        return g

    # ==================== 插件间通信（新增） ====================

    def call_plugin(self, plugin_name, function_name, *args, **kwargs):
        if not self.plugin_mgr:
            return None, "插件管理器不可用"
        target_plugin = self.plugin_mgr.get_plugin(plugin_name)
        if not target_plugin:
            return None, f"插件 {plugin_name} 不存在"
        if not target_plugin.get("enabled", True):
            return None, f"插件 {plugin_name} 已禁用"
        try:
            target_context = self.plugin_mgr.get_context(plugin_name, self.app)
            if not target_context:
                return None, f"无法获取插件 {plugin_name} 的上下文"
            code = target_plugin.get("code", "")
            exec_globals = target_context._get_exec_globals()
            exec(code, exec_globals)
            if function_name not in exec_globals:
                return None, f"插件 {plugin_name} 中没有函数 {function_name}"
            func = exec_globals[function_name]
            if not callable(func):
                return None, f"{function_name} 不是可调用对象"
            result = func(target_context, *args, **kwargs)
            self.logger.info(f"调用插件 {plugin_name}.{function_name} 成功")
            return result, None
        except Exception as e:
            error_msg = f"调用插件 {plugin_name}.{function_name} 失败：{str(e)}"
            self.logger.error(error_msg)
            return None, error_msg

    def get_plugin_list(self):
        if not self.plugin_mgr:
            return []
        plugins = self.plugin_mgr.get_all_plugins()
        return [{
            "name": p["meta"].get("name", ""),
            "version": p["meta"].get("version", "0.0.0"),
            "author": p["meta"].get("author", ""),
            "description": p["meta"].get("description", ""),
            "enabled": p.get("enabled", True),
            "has_settings": p["meta"].get("has_settings_page", False),
        } for p in plugins]

    def is_plugin_enabled(self, plugin_name):
        if not self.plugin_mgr:
            return False
        plugin = self.plugin_mgr.get_plugin(plugin_name)
        return plugin.get("enabled", True) if plugin else False

    def share_data(self, key, value, global_scope=False):
        if global_scope and self.plugin_mgr:
            if not hasattr(self.plugin_mgr, '_shared_data'):
                self.plugin_mgr._shared_data = {}
            self.plugin_mgr._shared_data[key] = value
            self.logger.info(f"共享数据（全局）: {key}")
        else:
            self.set(f"shared_{key}", value)
            self.logger.info(f"共享数据（插件内）: {key}")

    def get_shared_data(self, key, default=None, global_scope=False):
        if global_scope and self.plugin_mgr:
            if hasattr(self.plugin_mgr, '_shared_data'):
                return self.plugin_mgr._shared_data.get(key, default)
            return default
        return self.get(f"shared_{key}", default)

    def broadcast_event(self, event_name, data=None):
        if not self.plugin_mgr:
            return 0
        if not hasattr(self.plugin_mgr, '_event_bus'):
            self.plugin_mgr._event_bus = {}
        handlers = self.plugin_mgr._event_bus.get(event_name, [])
        count = 0
        for handler in handlers:
            try:
                handler(data)
                count += 1
            except Exception as e:
                self.logger.error(f"事件处理器执行失败：{str(e)}")
        self.logger.info(f"广播事件 {event_name}，触发 {count} 个处理器")
        return count

    def listen_event(self, event_name, handler):
        if not self.plugin_mgr:
            return False
        if not hasattr(self.plugin_mgr, '_event_bus'):
            self.plugin_mgr._event_bus = {}
        if event_name not in self.plugin_mgr._event_bus:
            self.plugin_mgr._event_bus[event_name] = []
        self.plugin_mgr._event_bus[event_name].append(handler)
        self.logger.info(f"监听事件 {event_name}")
        return True

    def unlisten_event(self, event_name, handler=None):
        if not self.plugin_mgr or not hasattr(self.plugin_mgr, '_event_bus'):
            return False
        if event_name not in self.plugin_mgr._event_bus:
            return False
        if handler:
            try:
                self.plugin_mgr._event_bus[event_name].remove(handler)
                return True
            except ValueError:
                return False
        else:
            del self.plugin_mgr._event_bus[event_name]
            return True

    # ==================== 核心功能扩展（新增） ====================

    def register_draw_mode(self, mode_name, mode_info):
        if not hasattr(self, '_custom_draw_modes'):
            self._custom_draw_modes = {}
        self._custom_draw_modes[mode_name] = mode_info
        self.logger.info(f"注册抽取模式: {mode_name}")
        return True

    def get_draw_modes(self):
        return getattr(self, '_custom_draw_modes', {})

    def register_mark_status(self, status_name, status_info):
        if not hasattr(self, '_custom_mark_statuses'):
            self._custom_mark_statuses = {}
        self._custom_mark_statuses[status_name] = status_info
        self.logger.info(f"注册标记状态: {status_name}")
        return True

    def get_mark_statuses(self):
        return getattr(self, '_custom_mark_statuses', {})

    def register_shortcut(self, key_sequence, callback, description=""):
        try:
            from PyQt5.QtWidgets import QShortcut
            from PyQt5.QtGui import QKeySequence
            shortcut = QShortcut(QKeySequence(key_sequence), self.app)
            shortcut.activated.connect(callback)
            if not hasattr(self, '_custom_shortcuts'):
                self._custom_shortcuts = []
            self._custom_shortcuts.append((shortcut, key_sequence, description))
            self.logger.info(f"注册快捷键: {key_sequence} - {description}")
            return True
        except Exception as e:
            self.logger.error(f"注册快捷键失败: {str(e)}")
            return False

    def get_shortcuts(self):
        return getattr(self, '_custom_shortcuts', [])

    def set_draw_algorithm(self, algorithm_func):
        self._custom_draw_algorithm = algorithm_func
        self.logger.info("设置自定义抽取算法")
        return True

    def get_draw_algorithm(self):
        return getattr(self, '_custom_draw_algorithm', None)

    def add_student(self, student_name):
        if hasattr(self.app, '_students'):
            if student_name not in self.app._students:
                self.app._students.append(student_name)
                self.logger.info(f"添加学生: {student_name}")
                return True
        return False

    def remove_student(self, student_name):
        if hasattr(self.app, '_students'):
            if student_name in self.app._students:
                self.app._students.remove(student_name)
                self.logger.info(f"移除学生: {student_name}")
                return True
        return False

    def add_text(self, title, content):
        if hasattr(self.app, '_texts'):
            self.app._texts.append({"title": title, "content": content})
            self.logger.info(f"添加课文: {title}")
            return True
        return False

    # ==================== 设置项集成增强（新增） ====================

    def register_setting_category(self, category_name, category_info):
        if not hasattr(self, '_custom_setting_categories'):
            self._custom_setting_categories = {}
        self._custom_setting_categories[category_name] = category_info
        self.logger.info(f"注册设置分类: {category_name}")
        return True

    def get_setting_categories(self):
        return getattr(self, '_custom_setting_categories', {})

    def register_setting_item(self, category, item_key, item_info):
        if not hasattr(self, '_custom_setting_items'):
            self._custom_setting_items = {}
        if category not in self._custom_setting_items:
            self._custom_setting_items[category] = {}
        self._custom_setting_items[category][item_key] = item_info
        self.logger.info(f"注册设置项: {category}.{item_key}")
        return True

    def get_setting_items(self, category=None):
        items = getattr(self, '_custom_setting_items', {})
        if category:
            return items.get(category, {})
        return items

    def get_app_config(self, section, key, default=None):
        if hasattr(self.app, 'config_mgr'):
            return self.app.config_mgr.get(section, key, default)
        return default

    def set_app_config(self, section, key, value):
        if hasattr(self.app, 'config_mgr'):
            self.app.config_mgr.set(section, key, value)
            self.logger.info(f"设置应用配置: {section}.{key} = {value}")
            return True
        return False

    # ==================== 热重载（新增） ====================

    def reload_self(self):
        plugin_name = self.plugin["meta"]["name"]
        if self.plugin_mgr:
            try:
                self.plugin_mgr.unload_plugin(plugin_name)
                self.plugin_mgr.load_plugin(plugin_name)
                self.logger.info(f"插件 {plugin_name} 热重载成功")
                return True
            except Exception as e:
                self.logger.error(f"热重载失败: {str(e)}")
                return False
        return False

    def reload_plugin(self, plugin_name):
        if self.plugin_mgr:
            try:
                self.plugin_mgr.unload_plugin(plugin_name)
                self.plugin_mgr.load_plugin(plugin_name)
                self.logger.info(f"插件 {plugin_name} 已重载")
                return True
            except Exception as e:
                self.logger.error(f"重载插件 {plugin_name} 失败: {str(e)}")
                return False
        return False

    def unload_self(self):
        plugin_name = self.plugin["meta"]["name"]
        if self.plugin_mgr:
            return self.plugin_mgr.unload_plugin(plugin_name)
        return False

    def load_plugin_by_path(self, file_path):
        if self.plugin_mgr:
            return self.plugin_mgr.load_plugin_from_file(file_path)
        return False, "插件管理器不可用"

    # ==================== 网络和文件API增强（新增） ====================

    def http_get(self, url, headers=None, timeout=10):
        try:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8'), response.status, None
        except Exception as e:
            return None, None, str(e)

    def http_post(self, url, data=None, headers=None, timeout=10):
        try:
            import urllib.request
            import urllib.parse
            if data and isinstance(data, dict):
                data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers or {})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8'), response.status, None
        except Exception as e:
            return None, None, str(e)

    def http_download(self, url, save_path, timeout=30):
        try:
            import urllib.request
            urllib.request.urlretrieve(url, save_path)
            return True, None
        except Exception as e:
            return False, str(e)

    def read_file(self, file_path, encoding='utf-8'):
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read(), None
        except Exception as e:
            return None, str(e)

    def write_file(self, file_path, content, encoding='utf-8'):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True, None
        except Exception as e:
            return False, str(e)

    def append_file(self, file_path, content, encoding='utf-8'):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
            return True, None
        except Exception as e:
            return False, str(e)

    def file_exists(self, file_path):
        return os.path.exists(file_path)

    def delete_file(self, file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            return False

    def list_directory(self, dir_path):
        try:
            return os.listdir(dir_path), None
        except Exception as e:
            return None, str(e)

    def create_directory(self, dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            return True
        except Exception as e:
            return False

    def get_file_info(self, file_path):
        try:
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "is_dir": os.path.isdir(file_path),
                "is_file": os.path.isfile(file_path),
            }, None
        except Exception as e:
            return None, str(e)

    def execute_command(self, command, timeout=30, shell=True):
        try:
            import subprocess
            result = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=timeout)
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }, None
        except Exception as e:
            return None, str(e)

    # ==================== 数据库API（新增） ====================

    def init_database(self, db_name="plugin_data"):
        try:
            import sqlite3
            db_path = os.path.join(self.data_dir, f"{db_name}.db")
            conn = sqlite3.connect(db_path)
            if not hasattr(self, '_db_connections'):
                self._db_connections = {}
            self._db_connections[db_name] = conn
            self.logger.info(f"数据库初始化: {db_name}")
            return True, None
        except Exception as e:
            return False, str(e)

    def db_execute(self, db_name, sql, params=None):
        try:
            if not hasattr(self, '_db_connections') or db_name not in self._db_connections:
                return None, "数据库未初始化"
            conn = self._db_connections[db_name]
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.fetchall(), None
        except Exception as e:
            return None, str(e)

    def db_query(self, db_name, sql, params=None):
        return self.db_execute(db_name, sql, params)

    def close_database(self, db_name):
        try:
            if hasattr(self, '_db_connections') and db_name in self._db_connections:
                self._db_connections[db_name].close()
                del self._db_connections[db_name]
                return True
            return False
        except Exception as e:
            return False

    # ==================== 调试和性能监控（新增） ====================

    def start_performance_monitor(self):
        import time
        self._perf_start_time = time.time()
        self._perf_counter = 0
        self.logger.info("性能监控已启动")
        return True

    def log_performance(self, operation_name):
        import time
        if not hasattr(self, '_perf_start_time'):
            return None
        elapsed = time.time() - self._perf_start_time
        self._perf_counter += 1
        self.logger.info(f"[性能] {operation_name}: {elapsed*1000:.2f}ms (第{self._perf_counter}次)")
        return elapsed

    def get_memory_usage(self):
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            try:
                import resource
                return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            except Exception:
                return None

    def get_cpu_usage(self):
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return None

    def set_log_level(self, level):
        self._log_level = level
        self.logger.info(f"日志级别设置为: {level}")

    def get_logs(self, lines=100, level=None):
        all_logs = self.logger.get_logs(lines * 2)
        if level:
            all_logs = [l for l in all_logs if f"[{level}]" in l]
        return all_logs[-lines:]

    def clear_logs(self):
        try:
            if os.path.exists(self.logger.log_file):
                with open(self.logger.log_file, 'w') as f:
                    f.write("")
                return True
        except Exception:
            pass
        return False

    # ==================== 资源访问增强（新增） ====================

    def get_main_window(self):
        return self.app

    def get_central_widget(self):
        if hasattr(self.app, 'centralWidget'):
            return self.app.centralWidget()
        return None

    def get_all_widgets(self):
        if hasattr(self.app, 'findChildren'):
            from PyQt5.QtWidgets import QWidget
            return self.app.findChildren(QWidget)
        return []

    def get_widget_by_name(self, name):
        if hasattr(self.app, 'findChild'):
            from PyQt5.QtWidgets import QWidget
            return self.app.findChild(QWidget, name)
        return None

    def get_widgets_by_class(self, class_name):
        widgets = self.get_all_widgets()
        return [w for w in widgets if type(w).__name__ == class_name]

    def get_ui_injector(self):
        try:
            from plugin_ui_injector import UIInjector
            return UIInjector(self.app)
        except Exception as e:
            self.logger.error(f"获取UI注入器失败: {str(e)}")
            return None

    def load_resource(self, relative_path):
        resource_path = os.path.join(self.get_app_dir(), relative_path)
        if os.path.exists(resource_path):
            with open(resource_path, 'rb') as f:
                return f.read()
        return None

    def save_resource(self, relative_path, data):
        resource_path = os.path.join(self.data_dir, relative_path)
        try:
            os.makedirs(os.path.dirname(resource_path), exist_ok=True)
            with open(resource_path, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            self.logger.error(f"保存资源失败: {str(e)}")
            return False

    def get_resource_path(self, relative_path):
        return os.path.join(self.data_dir, relative_path)

    # ==================== 应用控制（新增） ====================

    def restart_application(self):
        if hasattr(self.app, '_restart_application'):
            self.app._restart_application()
            return True
        return False

    def quit_application(self):
        if hasattr(self.app, 'close'):
            self.app.close()
            return True
        return False

    def minimize_application(self):
        if hasattr(self.app, 'showMinimized'):
            self.app.showMinimized()
            return True
        return False

    def maximize_application(self):
        if hasattr(self.app, 'showMaximized'):
            self.app.showMaximized()
            return True
        return False

    def set_window_title(self, title):
        if hasattr(self.app, 'setWindowTitle'):
            self.app.setWindowTitle(title)
            return True
        return False

    def set_window_size(self, width, height):
        if hasattr(self.app, 'resize'):
            self.app.resize(width, height)
            return True
        return False

    def set_window_on_top(self, on_top=True):
        if hasattr(self.app, 'setWindowFlags'):
            from PyQt5.QtCore import Qt
            flags = self.app.windowFlags()
            if on_top:
                flags |= Qt.WindowStaysOnTopHint
            else:
                flags &= ~Qt.WindowStaysOnTopHint
            self.app.setWindowFlags(flags)
            self.app.show()
            return True
        return False

    def show_toast(self, message, duration=2500, color="#0067c0"):
        try:
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import QTimer, Qt
            toast = QLabel(message, self.app)
            toast.setStyleSheet(f"background: {color}; color: white; padding: 12px 24px; border-radius: 8px; font-size: 13px; font-weight: 600;")
            toast.setAlignment(Qt.AlignCenter)
            toast.adjustSize()
            x = (self.app.width() - toast.width()) // 2
            y = 100
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(duration, toast.close)
            return True
        except Exception as e:
            self.logger.error(f"显示Toast失败: {str(e)}")
            return False


class PluginManager:
    def __init__(self, config_mgr):
        self.config_mgr = config_mgr
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.plugins_dir = os.path.join(self.base_dir, "plugins")
        self.plugins_data_dir = os.path.join(self.plugins_dir, "data")
        self.plugins_log_dir = os.path.join(self.plugins_dir, "logs")
        self.plugins = {}
        self.contexts = {}
        self._ensure_dirs()
        self.load_all_plugins()

    def _ensure_dirs(self):
        for d in [self.plugins_dir, self.plugins_data_dir, self.plugins_log_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

    def _get_state_file(self):
        return os.path.join(self.plugins_dir, "plugin_states.json")

    def _save_plugin_state(self, name, enabled):
        try:
            states = {}
            state_file = self._get_state_file()
            if os.path.exists(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    states = json.load(f)
            states[name] = {"enabled": enabled, "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存插件状态失败：{e}")

    def _load_plugin_states(self):
        try:
            state_file = self._get_state_file()
            if not os.path.exists(state_file):
                return {}
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载插件状态失败：{e}")
            return {}

    def load_all_plugins(self):
        self.plugins = {}
        if not os.path.exists(self.plugins_dir):
            return
        states = self._load_plugin_states()
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".arcx"):
                file_path = os.path.join(self.plugins_dir, filename)
                plugin, error = ArcxParser.parse(file_path)
                if plugin:
                    plugin["file_path"] = file_path
                    plugin["filename"] = filename
                    plugin_name = plugin["meta"]["name"]
                    if plugin_name in states:
                        plugin["enabled"] = states[plugin_name].get("enabled", True)
                    else:
                        plugin["enabled"] = True
                    plugin["plugin_dir"] = os.path.join(self.plugins_dir, plugin_name)
                    plugin["icons_dir"] = os.path.join(plugin["plugin_dir"], "icons")
                    plugin["resources_dir"] = os.path.join(plugin["plugin_dir"], "resources")
                    meta = plugin.get("meta", {})
                    icon_name = meta.get("icon", "")
                    if icon_name:
                        icon_path = os.path.join(plugin["icons_dir"], icon_name)
                        if os.path.exists(icon_path):
                            plugin["icon_path"] = icon_path
                        else:
                            plugin["icon_path"] = None
                    else:
                        plugin["icon_path"] = None
                    self.plugins[plugin_name] = plugin
                else:
                    print(f"插件加载失败 {filename}: {error}")

    def get_plugin(self, name):
        return self.plugins.get(name)

    def get_all_plugins(self):
        return list(self.plugins.values())

    def get_enabled_plugins(self):
        return [p for p in self.plugins.values() if p.get("enabled", True)]

    def get_plugins_with_settings(self):
        return [p for p in self.get_enabled_plugins() if p["meta"].get("has_settings_page", False)]

    def get_plugin_pages(self, plugin_name):
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return []
        meta = plugin.get("meta", {})
        pages = meta.get("pages", [])
        if not pages and meta.get("has_settings_page", False):
            pages = [{"key": "settings", "title": "设置", "icon": "settings"}]
        return pages

    def build_plugin_page(self, plugin_name, page_key, app, parent=None):
        context = self.get_context(plugin_name, app)
        if not context:
            return None
        return context.build_plugin_page(page_key, parent)

    def enable_plugin(self, name):
        if name in self.plugins:
            self.plugins[name]["enabled"] = True
            self._call_lifecycle(name, "on_enable")
            return True
        return False

    def disable_plugin(self, name):
        if name in self.plugins:
            self._call_lifecycle(name, "on_disable")
            self.plugins[name]["enabled"] = False
            return True
        return False

    def install_plugin(self, source_path):
        if not os.path.exists(source_path):
            return False, "源文件不存在"
        plugin, error = ArcxParser.parse(source_path)
        if not plugin:
            return False, error
        filename = os.path.basename(source_path)
        dest_path = os.path.join(self.plugins_dir, filename)
        import shutil
        shutil.copy2(source_path, dest_path)
        plugin["file_path"] = dest_path
        plugin["filename"] = filename
        self.plugins[plugin["meta"]["name"]] = plugin
        self._call_lifecycle(plugin["meta"]["name"], "on_install")
        return True, f"插件 {plugin['meta']['name']} 安装成功"

    def uninstall_plugin(self, name):
        if name not in self.plugins:
            return False, "插件不存在"
        self._call_lifecycle(name, "on_uninstall")
        plugin = self.plugins[name]
        file_path = plugin.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        data_dir = os.path.join(self.plugins_data_dir, name)
        if os.path.exists(data_dir):
            import shutil
            shutil.rmtree(data_dir, ignore_errors=True)
        del self.plugins[name]
        if name in self.contexts:
            del self.contexts[name]
        return True, f"插件 {name} 已卸载"

    def get_context(self, name, app):
        if name not in self.plugins:
            return None
        if name not in self.contexts:
            self.contexts[name] = PluginContext(self.plugins[name], app, self)
        return self.contexts[name]

    def _build_plugin_globals(self, context, plugin, app=None):
        """构建插件执行环境，预注入常用模块"""
        import datetime as _dt_module
        from datetime import datetime
        import os
        import sys
        import json
        import time
        import random
        import math
        import re
        import collections
        from pathlib import Path
        from typing import List, Dict, Optional, Tuple, Any, Callable

        def _plugin_print(*args, **kwargs):
            message = " ".join(str(a) for a in args)
            context.logger.info(message)

        exec_globals = {
            "context": context,
            "plugin": plugin,
            "print": _plugin_print,
            "__name__": f"plugin_{plugin.get('id', 'unknown')}",
            "datetime": datetime,
            "datetime_module": _dt_module,
            "os": os,
            "sys": sys,
            "json": json,
            "time": time,
            "random": random,
            "math": math,
            "re": re,
            "collections": collections,
            "Path": Path,
            "List": List,
            "Dict": Dict,
            "Optional": Optional,
            "Tuple": Tuple,
            "Any": Any,
            "Callable": Callable,
        }

        if app is not None:
            exec_globals["app"] = app
            exec_globals["config"] = plugin.get("config", {})

        return exec_globals

    def execute_plugin(self, name, app, entry_point="main"):
        plugin = self.get_plugin(name)
        if not plugin:
            return None, "插件不存在"
        if not plugin.get("enabled", True):
            return None, "插件已禁用"
        context = self.get_context(name, app)
        try:
            code = plugin.get("code", "")
            if not code.strip():
                return None, "插件代码为空"

            exec_globals = self._build_plugin_globals(context, plugin, app)

            context.logger.info(f"开始执行插件，入口：{entry_point}")
            exec(code, exec_globals)
            if entry_point in exec_globals and callable(exec_globals[entry_point]):
                result = exec_globals[entry_point](context)
                context.logger.info(f"插件执行完成，返回：{result}")
                return result, None
            context.logger.info("插件执行完成（无入口函数）")
            return None, None
        except Exception as e:
            error_msg = f"插件执行错误：{str(e)}\n{traceback.format_exc()}"
            context.logger.error(error_msg)
            return None, error_msg

    def _call_lifecycle(self, name, method_name):
        plugin = self.get_plugin(name)
        if not plugin or not plugin.get("enabled", True):
            return
        context = self.contexts.get(name)
        if not context:
            return
        try:
            code = plugin.get("code", "")
            exec_globals = self._build_plugin_globals(context, plugin)
            exec(code, exec_globals)
            if method_name in exec_globals and callable(exec_globals[method_name]):
                context.logger.info(f"调用生命周期方法：{method_name}")
                exec_globals[method_name](context)
        except Exception as e:
            context.logger.error(f"生命周期方法 {method_name} 执行错误：{str(e)}")

    def build_plugin_settings_page(self, name, app):
        plugin = self.get_plugin(name)
        if not plugin:
            return None
        context = self.get_context(name, app)
        try:
            code = plugin.get("code", "")
            exec_globals = self._build_plugin_globals(context, plugin, app)
            exec(code, exec_globals)
            if "build_settings_page" in exec_globals and callable(exec_globals["build_settings_page"]):
                context.logger.info("构建设置页面")
                return exec_globals["build_settings_page"](context)
        except Exception as e:
            context.logger.error(f"构建设置页面错误：{str(e)}")
        return None

    def create_sample_plugin(self):
        sample_code = '''
def main(context):
    context.show_message("示例插件", "这是一个示例插件！\\n\\n你可以在这里编写自己的插件逻辑。")
    students = context.get_students()
    context.log(f"当前有 {len(students)} 名学生")
    context.set_config("last_run", str(datetime.now()))
    return {"status": "success", "student_count": len(students)}


def build_settings_page(context):
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    title = QLabel("示例插件设置")
    title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0067c0;")
    layout.addWidget(title)

    desc = QLabel("在这里可以配置示例插件的各项参数。\\n配置会自动保存到插件数据目录的 config.json 中。")
    desc.setWordWrap(True)
    desc.setStyleSheet("color: #666666; font-size: 12px;")
    layout.addWidget(desc)

    input_label = QLabel("欢迎语：")
    input_label.setStyleSheet("font-size: 13px; font-weight: 600;")
    layout.addWidget(input_label)

    welcome_input = QLineEdit()
    welcome_input.setText(context.get_config("welcome_message", "欢迎使用示例插件！"))
    layout.addWidget(welcome_input)

    def save_config():
        context.set_config("welcome_message", welcome_input.text())
        context.show_message("保存成功", "配置已保存！")

    save_btn = QPushButton("保存配置")
    save_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }")
    save_btn.clicked.connect(save_config)
    layout.addWidget(save_btn)

    layout.addStretch()
    return page


def on_enable(context):
    context.log("插件已启用")


def on_disable(context):
    context.log("插件已禁用")


def on_install(context):
    context.log("插件已安装")


def on_uninstall(context):
    context.log("插件已卸载")
'''
        return ArcxParser.create_arcx(
            name="示例插件",
            description="这是一个示例插件，展示插件的基本结构、设置页面、日志系统和数据存储。",
            code=sample_code,
            config={"welcome_message": "欢迎使用示例插件！", "show_student_count": True},
            author="A13",
            version="1.0.0",
            has_settings_page=True
        )

    def load_plugin(self, name):
        plugin = self.get_plugin(name)
        if not plugin:
            return False, "插件不存在"
        if name in self.contexts:
            del self.contexts[name]
        self.plugins[name]["enabled"] = True
        self._save_plugin_state(name, True)
        self._call_lifecycle(name, "on_enable")
        return True, None

    def unload_plugin(self, name):
        plugin = self.get_plugin(name)
        if not plugin:
            return False, "插件不存在"
        self._call_lifecycle(name, "on_disable")
        if name in self.contexts:
            del self.contexts[name]
        self.plugins[name]["enabled"] = False
        self._save_plugin_state(name, False)
        return True, None

    def reload_plugin(self, name):
        success, error = self.unload_plugin(name)
        if not success:
            return False, error
        success, error = self.load_plugin(name)
        if not success:
            return False, error
        return True, None

    def load_plugin_from_file(self, file_path):
        if not os.path.exists(file_path):
            return False, "文件不存在"
        plugin, error = ArcxParser.parse(file_path)
        if not plugin:
            return False, error
        plugin_name = plugin["meta"]["name"]
        filename = os.path.basename(file_path)
        dest_path = os.path.join(self.plugins_dir, filename)
        import shutil
        shutil.copy2(file_path, dest_path)
        plugin["file_path"] = dest_path
        plugin["filename"] = filename
        plugin["enabled"] = True
        self.plugins[plugin_name] = plugin
        self._save_plugin_state(plugin_name, True)
        self._call_lifecycle(plugin_name, "on_install")
        self._call_lifecycle(plugin_name, "on_enable")
        return True, plugin_name

    def reload_all_plugins(self):
        results = {}
        for name in list(self.plugins.keys()):
            success, error = self.reload_plugin(name)
            results[name] = {"success": success, "error": error}
        return results

    def get_loaded_plugins(self):
        return [name for name, plugin in self.plugins.items() if plugin.get("enabled", True)]

    def get_unloaded_plugins(self):
        return [name for name, plugin in self.plugins.items() if not plugin.get("enabled", True)]

    def call_plugin_function(self, source_plugin, target_plugin, function_name, *args, **kwargs):
        target = self.get_plugin(target_plugin)
        if not target:
            return None, f"插件 {target_plugin} 不存在"
        if not target.get("enabled", True):
            return None, f"插件 {target_plugin} 已禁用"
        try:
            context = self.get_context(target_plugin, None)
            if not context:
                return None, f"无法获取插件 {target_plugin} 的上下文"
            code = target.get("code", "")
            exec_globals = context._get_exec_globals()
            exec(code, exec_globals)
            if function_name not in exec_globals:
                return None, f"插件 {target_plugin} 中没有函数 {function_name}"
            func = exec_globals[function_name]
            if not callable(func):
                return None, f"{function_name} 不是可调用对象"
            result = func(context, *args, **kwargs)
            return result, None
        except Exception as e:
            return None, str(e)

    def broadcast_to_all_plugins(self, event_name, data=None, exclude=None):
        count = 0
        for name, plugin in self.plugins.items():
            if not plugin.get("enabled", True):
                continue
            if exclude and name in exclude:
                continue
            try:
                context = self.get_context(name, None)
                if context:
                    context.broadcast_event(event_name, data)
                    count += 1
            except Exception:
                pass
        return count

    def get_plugin_stats(self):
        stats = {
            "total": len(self.plugins),
            "enabled": len(self.get_loaded_plugins()),
            "disabled": len(self.get_unloaded_plugins()),
            "plugins": []
        }
        for name, plugin in self.plugins.items():
            plugin_stat = {
                "name": name,
                "version": plugin["meta"].get("version", "0.0.0"),
                "author": plugin["meta"].get("author", ""),
                "enabled": plugin.get("enabled", True),
                "has_settings": plugin["meta"].get("has_settings_page", False),
                "pages": len(plugin["meta"].get("pages", [])),
            }
            context = self.contexts.get(name)
            if context:
                plugin_stat["data_dir"] = context.data_dir
                plugin_stat["libs_count"] = len(context.list_libs())
            stats["plugins"].append(plugin_stat)
        return stats

    def get_plugin_logs(self, name, lines=100):
        context = self.contexts.get(name)
        if context:
            return context.logger.get_logs(lines)
        return []

    def clear_plugin_logs(self, name):
        context = self.contexts.get(name)
        if context and os.path.exists(context.logger.log_file):
            with open(context.logger.log_file, 'w') as f:
                f.write("")
            return True
        return False

    def clear_all_logs(self):
        count = 0
        for name in self.plugins:
            if self.clear_plugin_logs(name):
                count += 1
        return count

    def check_plugin_dependencies(self, name):
        plugin = self.get_plugin(name)
        if not plugin:
            return None, "插件不存在"
        meta = plugin.get("meta", {})
        dependencies = meta.get("dependencies", [])
        results = {}
        for dep in dependencies:
            dep_plugin = self.get_plugin(dep)
            results[dep] = {
                "installed": dep_plugin is not None,
                "enabled": dep_plugin.get("enabled", False) if dep_plugin else False,
            }
        return results, None

    def get_plugin_dependents(self, name):
        dependents = []
        for plugin_name, plugin in self.plugins.items():
            if plugin_name == name:
                continue
            dependencies = plugin.get("meta", {}).get("dependencies", [])
            if name in dependencies:
                dependents.append(plugin_name)
        return dependents
