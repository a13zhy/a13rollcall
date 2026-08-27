import json
import os
import copy

RESTART_REQUIRED_KEYS = [
    "experimental.dpi_optimization",
    "ui.window_opacity",
    "ui.sidebar_width",
    "experimental.smooth_scroll"
]

DEFAULT_CONFIG = {
    "ui": {
        "theme": "light",
        "font_family": "微软雅黑",
        "font_size": 12,
        "name_font_size": 50,
        "text_font_size": 14,
        "name_font_weight": "bold",
        "animation_duration": 3.0,
        "ease_strength": 0.92,
        "animation_curve": "ease_out",
        "button_radius": 10,
        "card_radius": 12,
        "border_width": 1,
        "shadow_enabled": True,
        "sidebar_width": 300,
        "window_opacity": 1.0,
        "start_animation": True,
        "start_anim_duration": 2500,
        "show_status_bar": True,
        "result_popup": False,
        "popup_duration": 2000,
        "draw_countdown": False,
        "countdown_number": 3,
        "particle_enabled": True,
        "particle_count": 30,
        "particle_speed": 2,
        "scroll_speed": 1.0,
        "dark_mode": False,
        "status_bar": True,
        "startup_animation": True
    },
    "draw": {
        "mode": "auto",
        "no_repeat": True,
        "auto_duration": 4.0,
        "dynamic_focus": True,
        "dynamic_weight": True,
        "rate_mastered": 1.0,
        "rate_familiar": 2.0,
        "rate_unlearned": 3.0,
        "auto_reset_round": True,
        "sound_enabled": False,
        "anti_cheat": False,
        "history_limit": 50,
        "weight_multiplier": {
            "已背过": 1,
            "未背熟": 2,
            "未背过": 3
        }
    },
    "text": {
        "extract_mode": "段落抽取",
        "paragraph_random": True,
        "show_title": True,
        "text_align": "left"
    },
    "files": {
        "students": "students.txt",
        "texts": "texts.txt",
        "records": "records.txt",
        "stats": "stats.txt",
        "students_file": "students.txt",
        "texts_file": "texts.txt",
        "records_file": "records.txt",
        "stats_file": "stats.txt"
    },
    "shortcut": {
        "enabled": True,
        "key_draw": "space",
        "key_mastered": "1",
        "key_familiar": "2",
        "key_unlearned": "3",
        "key_hide_panel": "Escape",
        "key_reset_round": "r"
    },
    "student_status": {},
    "student_weights": {},
    "text_progress": {},
    "experimental": {
        "dpi_optimization": False,
        "particle_effect": True,
        "sound_effect": False,
        "voice_broadcast": False,
        "anti_cheat_mode": False,
        "history_recall": False,
        "smooth_scroll": False,
        "blur_background": False,
        "result_popup": False,
        "countdown_before_draw": False,
        "auto_reset_round": False
    },
    "hooks": {
        "draw_start": [],
        "draw_finish": [],
        "status_change": []
    },
    "quick_draw": {
        "enabled": True,
        "always_on_top": True,
        "show_history": True,
        "auto_hide": False,
        "sound_enabled": False,
        "no_repeat": True,
        "animation_duration": 2.0,
        "name_font_size": 48,
        "window_width": 420,
        "window_height": 520,
        "show_count": True,
        "confirm_on_close": True
    },
    "startup": {
        "default_mode": None
    }
}


class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = {}
        self.old_config = None
        self._hooks = {
            "draw_start": [],
            "draw_finish": [],
            "status_change": []
        }
        self.load_config()

    def _load_default(self):
        return copy.deepcopy(DEFAULT_CONFIG)

    def _merge_config(self, source, default):
        """递归深度合并配置，用户配置覆盖默认值，缺失的key自动补全"""
        result = copy.deepcopy(default)
        for key, value in source.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(value, result[key])
            else:
                result[key] = value
        return result

    def load_config(self):
        """加载配置文件，不存在则生成默认配置；损坏则回退默认值"""
        default = self._load_default()
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                self.config = self._merge_config(user_config, default)
            except Exception:
                self.config = default
                self.save_config()
        else:
            self.config = default
            self.save_config()

    def save_config(self):
        """将内存配置序列化写入磁盘"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _get_by_path(self, data, keys):
        """按key路径链式读取字典值"""
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def get(self, *keys):
        """链式获取配置值，不存在返回None"""
        return self._get_by_path(self.config, keys)

    def set(self, value, *keys):
        """链式设置内存配置值，自动创建中间字典"""
        current = self.config
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def backup_current(self):
        """创建当前配置快照，用于取消修改或重启项回滚"""
        self.old_config = copy.deepcopy(self.config)

    def check_restart_required(self):
        """对比快照与当前配置，判断是否修改了需要重启的项"""
        if self.old_config is None:
            return False
        for path in RESTART_REQUIRED_KEYS:
            keys = path.split(".")
            old_val = self._get_by_path(self.old_config, keys)
            new_val = self._get_by_path(self.config, keys)
            if old_val != new_val:
                return True
        return False

    def register_hook(self, hook_type, callback):
        """注册事件钩子回调"""
        if hook_type in self._hooks:
            self._hooks[hook_type].append(callback)

    def trigger_hooks(self, hook_type, *args):
        """触发事件钩子，单个回调异常不影响整体"""
        if hook_type not in self._hooks:
            return
        for callback in self._hooks[hook_type]:
            try:
                callback(*args)
            except Exception:
                continue

    def reset_all_files(self):
        """
        危险操作：清空所有数据文件 + 重置配置
        删除 students.txt / texts.txt / records.txt / stats.txt / config.json
        重新生成默认配置文件
        """
        target_files = [
            self.get("files", "students"),
            self.get("files", "texts"),
            self.get("files", "records"),
            self.get("files", "stats"),
            self.config_path
        ]
        for file_path in target_files:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
        self.config = self._load_default()
        self.save_config()