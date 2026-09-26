"""
A13课堂点名系统 - 插件常量与配置框架
所有颜色、参数、设置项都在这里定义，供插件开发者使用
"""

from PyQt5.QtGui import QColor


class ThemeColors:
    """主题颜色常量"""
    LIGHT = {
        "primary": "#0067c0",
        "primary_hover": "#005a9e",
        "primary_pressed": "#004578",
        "secondary": "#666666",
        "success": "#107c10",
        "warning": "#ff8c00",
        "error": "#d13438",
        "info": "#0078d4",
        "bg_main": "#fafafa",
        "bg_card": "#ffffff",
        "bg_hover": "#f0f0f0",
        "bg_active": "#e0e0e0",
        "text_primary": "#333333",
        "text_secondary": "#666666",
        "text_hint": "#999999",
        "text_inverse": "#ffffff",
        "border": "#e0e0e0",
        "border_focus": "#0067c0",
        "shadow": "rgba(0, 0, 0, 0.1)",
        "overlay": "rgba(0, 0, 0, 0.5)",
        "gradient_start": "#0067c0",
        "gradient_end": "#0078d4",
    }

    DARK = {
        "primary": "#4cc2ff",
        "primary_hover": "#60cdff",
        "primary_pressed": "#2eb1ff",
        "secondary": "#a0a0a0",
        "success": "#6cd96c",
        "warning": "#ffb340",
        "error": "#ff6b6b",
        "info": "#4cc2ff",
        "bg_main": "#202020",
        "bg_card": "#2d2d2d",
        "bg_hover": "#3a3a3a",
        "bg_active": "#454545",
        "text_primary": "#e0e0e0",
        "text_secondary": "#a0a0a0",
        "text_hint": "#707070",
        "text_inverse": "#202020",
        "border": "#404040",
        "border_focus": "#4cc2ff",
        "shadow": "rgba(0, 0, 0, 0.3)",
        "overlay": "rgba(0, 0, 0, 0.7)",
        "gradient_start": "#4cc2ff",
        "gradient_end": "#60cdff",
    }


class AnimationParams:
    """动画参数常量"""
    DRAW = {
        "default_duration": 3.0,
        "min_duration": 1.0,
        "max_duration": 10.0,
        "ease_strength": 0.92,
        "ease_out_exponent": 3,
        "ease_in_exponent": 2,
        "fps": 60,
        "name_font_size": 50,
        "name_font_weight": "bold",
        "particle_count": 30,
        "particle_speed": 2,
        "particle_size_min": 2,
        "particle_size_max": 6,
    }

    RESULT_POPUP = {
        "duration": 2000,
        "fade_in_duration": 200,
        "fade_out_duration": 300,
        "scale_from": 0.8,
        "scale_to": 1.0,
    }

    TOAST = {
        "duration": 2000,
        "fade_in_duration": 150,
        "fade_out_duration": 250,
        "position_offset_y": 80,
    }

    WINDOW = {
        "fade_in_duration": 200,
        "fade_out_duration": 200,
        "scale_duration": 150,
    }


class DrawModes:
    """抽取模式常量"""
    AUTO = "auto"
    MANUAL = "manual"
    COUNTDOWN = "countdown"

    NO_REPEAT = True
    ALLOW_REPEAT = False

    DYNAMIC_WEIGHT = True
    FIXED_WEIGHT = False

    WEIGHT_MULTIPLIERS = {
        "已背过": 1.0,
        "未背熟": 2.0,
        "未背过": 3.0,
    }


class StatusTypes:
    """状态类型常量"""
    MASTERED = "已背过"
    FAMILIAR = "未背熟"
    UNLEARNED = "未背过"
    UNMARKED = "未标记"
    SKIPPED = "已跳过"

    ALL_STATUSES = [MASTERED, FAMILIAR, UNLEARNED]
    MARKABLE_STATUSES = [MASTERED, FAMILIAR, UNLEARNED]


class EventTypes:
    """事件类型常量 - 插件可以监听和触发这些事件"""
    DRAW_START = "draw_start"
    DRAW_FINISH = "draw_finish"
    DRAW_CANCEL = "draw_cancel"
    STATUS_CHANGE = "status_change"
    STATUS_UNDO = "status_undo"
    ROUND_RESET = "round_reset"
    SETTINGS_CHANGE = "settings_change"
    THEME_CHANGE = "theme_change"
    CLASS_NAME_CHANGE = "class_name_change"
    PLUGIN_ENABLE = "plugin_enable"
    PLUGIN_DISABLE = "plugin_disable"
    QUICK_DRAW_OPEN = "quick_draw_open"
    QUICK_DRAW_CLOSE = "quick_draw_close"
    WINDOW_MINIMIZE = "window_minimize"
    WINDOW_RESTORE = "window_restore"
    APP_START = "app_start"
    APP_EXIT = "app_exit"
    CUSTOM = "custom"

    ALL_EVENTS = [
        DRAW_START, DRAW_FINISH, DRAW_CANCEL,
        STATUS_CHANGE, STATUS_UNDO, ROUND_RESET,
        SETTINGS_CHANGE, THEME_CHANGE, CLASS_NAME_CHANGE,
        PLUGIN_ENABLE, PLUGIN_DISABLE,
        QUICK_DRAW_OPEN, QUICK_DRAW_CLOSE,
        WINDOW_MINIMIZE, WINDOW_RESTORE,
        APP_START, APP_EXIT, CUSTOM,
    ]


class PluginHooks:
    """插件钩子点 - 插件可以在这些点插入自定义逻辑"""
    BEFORE_DRAW = "before_draw"
    AFTER_DRAW = "after_draw"
    BEFORE_MARK = "before_mark"
    AFTER_MARK = "after_mark"
    BEFORE_UNDO = "before_undo"
    AFTER_UNDO = "after_undo"
    BEFORE_RESET = "before_reset"
    AFTER_RESET = "after_reset"
    RENDER_NAME = "render_name"
    RENDER_RESULT = "render_result"
    CUSTOM_ANIMATION = "custom_animation"


class ConfigSections:
    """配置节常量"""
    APP = "app"
    UI = "ui"
    DRAW = "draw"
    TEXT = "text"
    FILES = "files"
    MARK = "mark"
    SHORTCUTS = "shortcuts"
    DATA = "data"
    PLUGINS = "plugins"
    EXPERIMENTAL = "experimental"
    QUICK_DRAW = "quick_draw"
    STARTUP = "startup"
    HOOKS = "hooks"


class ConfigKeys:
    """配置键常量 - 常用配置项"""
    APP_CLASS_NAME = ("app", "class_name")
    APP_VERSION = ("app", "version")
    APP_ENGINE_NAME = ("app", "engine_name")

    UI_THEME = ("ui", "theme")
    UI_FONT_FAMILY = ("ui", "font_family")
    UI_FONT_SIZE = ("ui", "font_size")
    UI_NAME_FONT_SIZE = ("ui", "name_font_size")
    UI_ANIMATION_DURATION = ("ui", "animation_duration")
    UI_BUTTON_RADIUS = ("ui", "button_radius")
    UI_CARD_RADIUS = ("ui", "card_radius")
    UI_PARTICLE_ENABLED = ("ui", "particle_enabled")
    UI_PARTICLE_COUNT = ("ui", "particle_count")
    UI_DARK_MODE = ("ui", "dark_mode")

    DRAW_MODE = ("draw", "mode")
    DRAW_NO_REPEAT = ("draw", "no_repeat")
    DRAW_AUTO_DURATION = ("draw", "auto_duration")
    DRAW_DYNAMIC_WEIGHT = ("draw", "dynamic_weight")
    DRAW_RATE_MASTERED = ("draw", "rate_mastered")
    DRAW_RATE_FAMILIAR = ("draw", "rate_familiar")
    DRAW_RATE_UNLEARNED = ("draw", "rate_unlearned")
    DRAW_AUTO_RESET_ROUND = ("draw", "auto_reset_round")
    DRAW_SOUND_ENABLED = ("draw", "sound_enabled")
    DRAW_HISTORY_LIMIT = ("draw", "history_limit")

    TEXT_EXTRACT_MODE = ("text", "extract_mode")
    TEXT_PARAGRAPH_RANDOM = ("text", "paragraph_random")
    TEXT_SHOW_TITLE = ("text", "show_title")

    FILES_STUDENTS = ("files", "students")
    FILES_TEXTS = ("files", "texts")
    FILES_RECORDS = ("files", "records")
    FILES_STATS = ("files", "stats")

    QUICK_DRAW_ENABLED = ("quick_draw", "enabled")
    QUICK_DRAW_ALWAYS_ON_TOP = ("quick_draw", "always_on_top")
    QUICK_DRAW_SHOW_HISTORY = ("quick_draw", "show_history")
    QUICK_DRAW_AUTO_HIDE = ("quick_draw", "auto_hide")
    QUICK_DRAW_NO_REPEAT = ("quick_draw", "no_repeat")
    QUICK_DRAW_NAME_FONT_SIZE = ("quick_draw", "name_font_size")


class ShortcutKeys:
    """快捷键常量"""
    DRAW_TOGGLE = "space"
    RESET_ROUND = "escape"
    NO_REPEAT_TOGGLE = "n"
    DYNAMIC_WEIGHT_TOGGLE = "w"
    VIEW_HISTORY = "r"
    MARK_MASTERED = "1"
    MARK_FAMILIAR = "2"
    MARK_UNLEARNED = "3"
    UNDO_MARK = "z"
    SKIP_CURRENT = "tab"
    SWITCH_MODE = "t"
    PREV_TEXT = "left"
    NEXT_TEXT = "right"
    SWITCH_THEME = "m"
    OPEN_SETTINGS = ","
    PARTICLE_TOGGLE = "p"
    FULLSCREEN = "f11"
    LEADERBOARD = "l"
    SAVE_DATA = "ctrl+s"
    SHORTCUT_HELP = "?"


class WindowStates:
    """窗口状态常量"""
    MAIN = "main"
    QUICK = "quick"
    MINIMIZED = "minimized"
    DRAWING = "drawing"
    SETTINGS = "settings"

    STATE_NAMES = {
        MAIN: "主界面",
        QUICK: "快捷抽取",
        MINIMIZED: "最小化",
        DRAWING: "正在抽取",
        SETTINGS: "设置中",
    }


class PluginTypes:
    """插件类型常量"""
    GENERAL = "general"
    TOOL = "tool"
    THEME = "theme"
    DATA = "data"
    UI = "ui"
    ANIMATION = "animation"
    INTEGRATION = "integration"
    GAME = "game"

    ALL_TYPES = [GENERAL, TOOL, THEME, DATA, UI, ANIMATION, INTEGRATION, GAME]


class PluginPermissions:
    """插件权限常量"""
    READ_STUDENTS = "read_students"
    MODIFY_STUDENTS = "modify_students"
    TRIGGER_DRAW = "trigger_draw"
    MODIFY_DRAW = "modify_draw"
    CUSTOM_ANIMATION = "custom_animation"
    READ_CONFIG = "read_config"
    MODIFY_CONFIG = "modify_config"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    EXECUTE_PROCESS = "execute_process"
    UI_MODIFICATION = "ui_modification"
    SYSTEM_CONTROL = "system_control"

    ALL_PERMISSIONS = [
        READ_STUDENTS, MODIFY_STUDENTS,
        TRIGGER_DRAW, MODIFY_DRAW, CUSTOM_ANIMATION,
        READ_CONFIG, MODIFY_CONFIG,
        FILE_SYSTEM, NETWORK, EXECUTE_PROCESS,
        UI_MODIFICATION, SYSTEM_CONTROL,
    ]


def get_color(theme_name, color_key):
    """获取主题颜色"""
    theme = ThemeColors.DARK if theme_name == "dark" else ThemeColors.LIGHT
    return theme.get(color_key, "#000000")


def get_qcolor(theme_name, color_key):
    """获取QColor对象"""
    return QColor(get_color(theme_name, color_key))


__all__ = [
    'ThemeColors', 'AnimationParams', 'DrawModes', 'StatusTypes',
    'EventTypes', 'PluginHooks', 'ConfigSections', 'ConfigKeys',
    'ShortcutKeys', 'WindowStates', 'PluginTypes', 'PluginPermissions',
    'get_color', 'get_qcolor',
]
