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
        self.logger.info(f"显示消息框：{title}")
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
        return {
            'context': self,
            'plugin': self.plugin,
            'app': self.app,
            'print': self.logger.info,
            '__name__': 'plugin_exec',
        }


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
            exec_globals = {
                "context": context,
                "plugin": plugin,
                "app": app,
                "config": plugin.get("config", {}),
                "print": context.log,
                "__name__": f"plugin_{name}"
            }
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
            exec_globals = {
                "context": context,
                "plugin": plugin,
                "print": context.log,
                "__name__": f"plugin_{name}"
            }
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
            exec_globals = {
                "context": context,
                "plugin": plugin,
                "print": context.log,
                "__name__": f"plugin_{name}"
            }
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
