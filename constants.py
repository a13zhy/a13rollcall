# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 常量集中管理模块
所有魔法数字、字符串、颜色、尺寸等常量统一在此定义
"""

import os
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt


# ==================== 应用信息 ====================
class AppInfo:
    NAME = "A13课堂点名系统"
    VERSION = "6.8.0"
    BUILD = "20260914"
    AUTHOR = "A13"
    ENGINE_NAME = "A13 Engine"
    OFFICIAL_URL = "https://dkfile.istester.com/zhysppa13/a13callname.html"
    URL_SCHEME = "a13rollcall://"


# ==================== 文件路径 ====================
class FilePaths:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STUDENTS_FILE = os.path.join(BASE_DIR, "students.txt")
    TEXTS_FILE = os.path.join(BASE_DIR, "texts.txt")
    CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
    WIZARD_RECORD = os.path.join(BASE_DIR, "wizard_record.ini")
    ECHO_HOLE_FILE = os.path.join(BASE_DIR, "echo_hole.txt")
    ICONS_DIR = os.path.join(BASE_DIR, "icons")
    PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")
    PLUGIN_DATA_DIR = os.path.join(PLUGINS_DIR, "data")
    PLUGIN_LOGS_DIR = os.path.join(PLUGINS_DIR, "logs")
    CRASH_REPORT_DIR = os.path.join(BASE_DIR, "crash_reports")
    BACKUP_DIR = os.path.join(BASE_DIR, "backups")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")


# ==================== 颜色主题 ====================
class Colors:
    # 主色调
    PRIMARY = "#0067c0"
    PRIMARY_LIGHT = "#0078d4"
    PRIMARY_DARK = "#005a9e"
    PRIMARY_HOVER = "#106ebe"
    PRIMARY_PRESSED = "#005a9e"

    # 成功/警告/错误
    SUCCESS = "#107c10"
    SUCCESS_LIGHT = "#0e6c0e"
    WARNING = "#ca5010"
    WARNING_LIGHT = "#ff8c00"
    ERROR = "#c42b1c"
    ERROR_LIGHT = "#e81123"
    INFO = "#0067c0"

    # 中性色
    WHITE = "#ffffff"
    BLACK = "#000000"
    GRAY_50 = "#fafafa"
    GRAY_100 = "#f5f5f5"
    GRAY_200 = "#eeeeee"
    GRAY_300 = "#e0e0e0"
    GRAY_400 = "#bdbdbd"
    GRAY_500 = "#9e9e9e"
    GRAY_600 = "#757575"
    GRAY_700 = "#616161"
    GRAY_800 = "#424242"
    GRAY_900 = "#212121"

    # 文本颜色
    TEXT_PRIMARY = "#1a1a1a"
    TEXT_SECONDARY = "#666666"
    TEXT_DISABLED = "#999999"
    TEXT_INVERSE = "#ffffff"

    # 背景色
    BG_WINDOW = "#f3f3f3"
    BG_CARD = "#ffffff"
    BG_HOVER = "#f0f0f0"
    BG_SELECTED = "#e5f1fb"
    BG_DISABLED = "#f5f5f5"

    # 边框色
    BORDER_LIGHT = "#e0e0e0"
    BORDER_NORMAL = "#d1d1d1"
    BORDER_DARK = "#bdbdbd"
    BORDER_FOCUS = "#0067c0"

    # 深色模式
    DARK_BG_WINDOW = "#202020"
    DARK_BG_CARD = "#2d2d2d"
    DARK_BG_HOVER = "#3a3a3a"
    DARK_BG_SELECTED = "#0067c0"
    DARK_TEXT_PRIMARY = "#ffffff"
    DARK_TEXT_SECONDARY = "#cccccc"
    DARK_BORDER = "#404040"

    # 抽取状态颜色
    DRAW_IDLE = "#666666"
    DRAW_RUNNING = "#0067c0"
    DRAW_SUCCESS = "#107c10"
    DRAW_WARNING = "#ca5010"

    # 背诵状态颜色
    STATUS_RECITED = "#107c10"
    STATUS_NOT_FAMILIAR = "#ca5010"
    STATUS_NOT_RECITED = "#c42b1c"
    STATUS_UNMARKED = "#666666"


# ==================== 尺寸常量 ====================
class Sizes:
    # 窗口尺寸
    WINDOW_MIN_WIDTH = 1000
    WINDOW_MIN_HEIGHT = 700
    WINDOW_DEFAULT_WIDTH = 1400
    WINDOW_DEFAULT_HEIGHT = 880
    WINDOW_LARGE_WIDTH = 1600
    WINDOW_LARGE_HEIGHT = 1000

    # 标题栏
    TITLE_BAR_HEIGHT = 48
    TITLE_BAR_ICON_SIZE = 24
    WINDOW_CONTROL_BTN_WIDTH = 46
    WINDOW_CONTROL_BTN_HEIGHT = 32

    # 按钮尺寸
    BTN_SMALL_HEIGHT = 28
    BTN_NORMAL_HEIGHT = 36
    BTN_LARGE_HEIGHT = 44
    BTN_XLARGE_HEIGHT = 52
    BTN_SMALL_WIDTH = 72
    BTN_NORMAL_WIDTH = 100
    BTN_LARGE_WIDTH = 140
    BTN_XLARGE_WIDTH = 180

    # 圆角
    RADIUS_SMALL = 4
    RADIUS_NORMAL = 6
    RADIUS_LARGE = 8
    RADIUS_XLARGE = 12
    RADIUS_2XLARGE = 16
    RADIUS_FULL = 9999

    # 间距
    SPACING_XS = 4
    SPACING_SMALL = 8
    SPACING_NORMAL = 12
    SPACING_LARGE = 16
    SPACING_XLARGE = 24
    SPACING_2XLARGE = 32

    # 内边距
    PADDING_XS = 4
    PADDING_SMALL = 8
    PADDING_NORMAL = 12
    PADDING_LARGE = 16
    PADDING_XLARGE = 20
    PADDING_2XLARGE = 24

    # 字体大小
    FONT_XS = 10
    FONT_SMALL = 11
    FONT_NORMAL = 12
    FONT_LARGE = 13
    FONT_XLARGE = 14
    FONT_2XLARGE = 16
    FONT_3XLARGE = 18
    FONT_4XLARGE = 20
    FONT_5XLARGE = 24
    FONT_TITLE = 28
    FONT_BIG_TITLE = 32
    FONT_HUGE = 48

    # 字体粗细
    FONT_WEIGHT_LIGHT = 300
    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMIBOLD = 600
    FONT_WEIGHT_BOLD = 700
    FONT_WEIGHT_EXTRABOLD = 800

    # 图标尺寸
    ICON_XS = 12
    ICON_SMALL = 16
    ICON_NORMAL = 20
    ICON_LARGE = 24
    ICON_XLARGE = 32
    ICON_2XLARGE = 48
    ICON_3XLARGE = 64

    # 抽取名字显示
    DRAW_NAME_FONT_MIN = 36
    DRAW_NAME_FONT_MAX = 72
    DRAW_NAME_FONT_DEFAULT = 56

    # 阴影
    SHADOW_SMALL = 4
    SHADOW_NORMAL = 8
    SHADOW_LARGE = 16
    SHADOW_XLARGE = 24


# ==================== 时间常量 ====================
class Times:
    # 动画时长（毫秒）
    ANIMATION_FAST = 150
    ANIMATION_NORMAL = 300
    ANIMATION_SLOW = 500
    ANIMATION_VERY_SLOW = 800

    # 抽取动画
    DRAW_ROLL_INTERVAL_MIN = 30
    DRAW_ROLL_INTERVAL_MAX = 100
    DRAW_ROLL_DURATION_MIN = 1500
    DRAW_ROLL_DURATION_MAX = 3000
    DRAW_RESULT_DISPLAY = 3000

    # 提示显示时长
    TOAST_SHORT = 1500
    TOAST_NORMAL = 2500
    TOAST_LONG = 4000
    TOAST_VERY_LONG = 6000

    # 自动保存间隔
    AUTOSAVE_INTERVAL = 30000

    # 启动延迟
    STARTUP_DELAY_FAST = 100
    STARTUP_DELAY_NORMAL = 300
    STARTUP_DELAY_SLOW = 500
    STARTUP_DELAY_VERY_SLOW = 1000

    # 超时时间（秒）
    TIMEOUT_SHORT = 5
    TIMEOUT_NORMAL = 10
    TIMEOUT_LONG = 30
    TIMEOUT_VERY_LONG = 60

    # 网络请求重试
    NETWORK_RETRY_COUNT = 3
    NETWORK_RETRY_DELAY = 1000


# ==================== UI样式 ====================
class Styles:
    # 按钮基础样式
    BTN_BASE = """
        QPushButton {
            border: none;
            border-radius: %dpx;
            font-weight: 600;
            font-size: %dpx;
            padding: 8px 16px;
        }
    """

    # 主按钮
    BTN_PRIMARY = """
        QPushButton {
            background: %s;
            color: white;
        }
        QPushButton:hover {
            background: %s;
        }
        QPushButton:pressed {
            background: %s;
        }
        QPushButton:disabled {
            background: #cccccc;
            color: #999999;
        }
    """ % (Colors.PRIMARY, Colors.PRIMARY_HOVER, Colors.PRIMARY_PRESSED)

    # 成功按钮
    BTN_SUCCESS = """
        QPushButton {
            background: %s;
            color: white;
        }
        QPushButton:hover {
            background: #0e6c0e;
        }
        QPushButton:pressed {
            background: #0b5a0b;
        }
        QPushButton:disabled {
            background: #cccccc;
            color: #999999;
        }
    """ % Colors.SUCCESS

    # 警告按钮
    BTN_WARNING = """
        QPushButton {
            background: %s;
            color: white;
        }
        QPushButton:hover {
            background: #b04810;
        }
        QPushButton:pressed {
            background: #963d0e;
        }
        QPushButton:disabled {
            background: #cccccc;
            color: #999999;
        }
    """ % Colors.WARNING

    # 危险按钮
    BTN_DANGER = """
        QPushButton {
            background: %s;
            color: white;
        }
        QPushButton:hover {
            background: #a52517;
        }
        QPushButton:pressed {
            background: #8a1f13;
        }
        QPushButton:disabled {
            background: #cccccc;
            color: #999999;
        }
    """ % Colors.ERROR

    # 幽灵按钮（边框按钮）
    BTN_GHOST = """
        QPushButton {
            background: transparent;
            color: %s;
            border: 1px solid %s;
        }
        QPushButton:hover {
            background: %s;
        }
        QPushButton:pressed {
            background: #d0e4f7;
        }
        QPushButton:disabled {
            color: #999999;
            border-color: #dddddd;
        }
    """ % (Colors.PRIMARY, Colors.PRIMARY, Colors.BG_SELECTED)

    # 输入框
    INPUT_NORMAL = """
        QLineEdit, QTextEdit, QPlainTextEdit {
            background: white;
            border: 1px solid %s;
            border-radius: %dpx;
            padding: 8px 12px;
            font-size: %dpx;
            selection-background-color: %s;
        }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid %s;
            padding: 7px 11px;
        }
        QLineEdit:disabled, QTextEdit:disabled {
            background: #f5f5f5;
            color: #999999;
        }
    """ % (Colors.BORDER_NORMAL, Sizes.RADIUS_NORMAL, Sizes.FONT_NORMAL, Colors.PRIMARY, Colors.BORDER_FOCUS)

    # 卡片
    CARD = """
        QWidget#card {
            background: white;
            border: 1px solid %s;
            border-radius: %dpx;
        }
    """ % (Colors.BORDER_LIGHT, Sizes.RADIUS_LARGE)

    # 分组框
    GROUP_BOX = """
        QGroupBox {
            font-weight: 700;
            font-size: %dpx;
            border: 1px solid %s;
            border-radius: %dpx;
            margin-top: 12px;
            padding-top: 16px;
            background: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: %s;
        }
    """ % (Sizes.FONT_LARGE, Colors.BORDER_LIGHT, Sizes.RADIUS_LARGE, Colors.PRIMARY)

    # 标签页
    TAB_WIDGET = """
        QTabWidget::pane {
            border: 1px solid %s;
            border-radius: %dpx;
            top: -1px;
        }
        QTabBar::tab {
            padding: 10px 20px;
            margin-right: 4px;
            border-radius: %dpx %dpx 0 0;
            font-size: %dpx;
            font-weight: 600;
        }
        QTabBar::tab:selected {
            background: %s;
            color: white;
        }
        QTabBar::tab:!selected {
            background: #f0f0f0;
            color: #333;
        }
        QTabBar::tab:!selected:hover {
            background: #e0e0e0;
        }
    """ % (Colors.BORDER_LIGHT, Sizes.RADIUS_NORMAL, Sizes.RADIUS_NORMAL, Sizes.RADIUS_NORMAL, Sizes.FONT_NORMAL, Colors.PRIMARY)

    # 列表控件
    LIST_WIDGET = """
        QListWidget {
            background: white;
            border: 1px solid %s;
            border-radius: %dpx;
            padding: 8px;
            font-size: %dpx;
            outline: none;
        }
        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
            margin: 2px 0;
        }
        QListWidget::item:selected {
            background: %s;
            color: white;
        }
        QListWidget::item:hover:!selected {
            background: %s;
        }
    """ % (Colors.BORDER_LIGHT, Sizes.RADIUS_NORMAL, Sizes.FONT_NORMAL, Colors.PRIMARY, Colors.BG_HOVER)

    # 滚动条
    SCROLLBAR = """
        QScrollBar:vertical {
            background: transparent;
            width: 8px;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background: #c1c1c1;
            border-radius: 4px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background: #a1a1a1;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar:horizontal {
            background: transparent;
            height: 8px;
            margin: 0;
        }
        QScrollBar::handle:horizontal {
            background: #c1c1c1;
            border-radius: 4px;
            min-width: 30px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #a1a1a1;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0;
        }
    """


# ==================== 快捷键 ====================
class Shortcuts:
    # 抽取操作
    DRAW_START_STOP = "Space"
    RESET_ROUND = "Esc"
    TOGGLE_NO_REPEAT = "N"
    TOGGLE_WEIGHT = "W"
    VIEW_ROUND_RECORD = "R"

    # 状态标记
    MARK_RECITED = "1"
    MARK_NOT_FAMILIAR = "2"
    MARK_NOT_RECITED = "3"
    UNDO_LAST_MARK = "Z"
    SKIP_CURRENT = "Tab"

    # 课文与界面
    TOGGLE_DRAW_MODE = "T"
    PREV_TEXT = "Left"
    NEXT_TEXT = "Right"
    TOGGLE_THEME = "M"
    OPEN_SETTINGS = ","

    # 显示与效果
    TOGGLE_PARTICLES = "P"
    FULLSCREEN = "F11"
    LEADERBOARD = "L"
    SAVE_DATA = "Ctrl+S"
    SHORTCUT_HELP = "?"


# ==================== 状态常量 ====================
class States:
    # 抽取状态
    DRAW_IDLE = "idle"
    DRAW_RUNNING = "running"
    DRAW_PAUSED = "paused"
    DRAW_FINISHED = "finished"

    # 背诵状态
    STATUS_UNMARKED = "未标记"
    STATUS_RECITED = "已背过"
    STATUS_NOT_FAMILIAR = "未背熟"
    STATUS_NOT_RECITED = "未背过"
    STATUS_SKIPPED = "已跳过"

    # 抽取模式
    MODE_RANDOM = "random"
    MODE_NO_REPEAT = "no_repeat"
    MODE_WEIGHTED = "weighted"

    # 窗口状态
    WINDOW_NORMAL = "normal"
    WINDOW_MINIMIZED = "minimized"
    WINDOW_MAXIMIZED = "maximized"
    WINDOW_FULLSCREEN = "fullscreen"

    # 插件状态
    PLUGIN_LOADED = "loaded"
    PLUGIN_ENABLED = "enabled"
    PLUGIN_DISABLED = "disabled"
    PLUGIN_ERROR = "error"


# ==================== 配置键名 ====================
class ConfigKeys:
    # 应用设置
    APP_CLASS_NAME = "app.class_name"
    APP_THEME = "app.theme"
    APP_LANGUAGE = "app.language"
    APP_AUTOSAVE = "app.autosave"
    APP_STARTUP_MODE = "app.startup_mode"
    APP_REMEMBER_WINDOW = "app.remember_window"

    # 抽取设置
    DRAW_MODE = "draw.mode"
    DRAW_DURATION = "draw.duration"
    DRAW_SHOW_TEXT = "draw.show_text"
    DRAW_RANDOM_TEXT = "draw.random_text"
    DRAW_AUTO_START = "draw.auto_start"
    DRAW_SOUND_ENABLED = "draw.sound_enabled"
    DRAW_PARTICLES_ENABLED = "draw.particles_enabled"

    # 界面设置
    UI_FONT_SIZE = "ui.font_size"
    UI_DARK_MODE = "ui.dark_mode"
    UI_WINDOW_OPACITY = "ui.window_opacity"
    UI_ANIMATION_SPEED = "ui.animation_speed"
    UI_SHOW_STATISTICS = "ui.show_statistics"
    UI_SHOW_LEADERBOARD = "ui.show_leaderboard"

    # 快捷抽取设置
    QUICK_ENABLED = "quick.enabled"
    QUICK_AUTO_HIDE = "quick.auto_hide"
    QUICK_ON_TOP = "quick.on_top"
    QUICK_POSITION = "quick.position"

    # 插件设置
    PLUGIN_AUTO_LOAD = "plugin.auto_load"
    PLUGIN_SANDBOX = "plugin.sandbox"
    PLUGIN_UPDATE_CHECK = "plugin.update_check"


# ==================== 错误码 ====================
class ErrorCodes:
    # 通用错误
    SUCCESS = 0
    UNKNOWN_ERROR = -1
    INVALID_PARAMETER = -2
    OPERATION_FAILED = -3
    PERMISSION_DENIED = -4
    NOT_FOUND = -5
    ALREADY_EXISTS = -6

    # 文件错误
    FILE_NOT_FOUND = -100
    FILE_READ_ERROR = -101
    FILE_WRITE_ERROR = -102
    FILE_CORRUPTED = -103
    FILE_LOCKED = -104

    # 配置错误
    CONFIG_INVALID = -200
    CONFIG_PARSE_ERROR = -201
    CONFIG_SCHEMA_ERROR = -202

    # 插件错误
    PLUGIN_NOT_FOUND = -300
    PLUGIN_LOAD_ERROR = -301
    PLUGIN_EXECUTE_ERROR = -302
    PLUGIN_DEPENDENCY_MISSING = -303
    PLUGIN_VERSION_INCOMPATIBLE = -304
    PLUGIN_PERMISSION_DENIED = -305
    PLUGIN_CRASHED = -306

    # 网络错误
    NETWORK_TIMEOUT = -400
    NETWORK_CONNECTION_ERROR = -401
    NETWORK_HTTP_ERROR = -402
    NETWORK_SSL_ERROR = -403

    # 数据错误
    DATA_EMPTY = -500
    DATA_INVALID = -501
    DATA_DUPLICATE = -502
    DATA_NOT_FOUND = -503


# ==================== 字体 ====================
class Fonts:
    FAMILY_DEFAULT = "微软雅黑"
    FAMILY_MONOSPACE = "Consolas"
    FAMILY_UI = "Segoe UI"

    @staticmethod
    def get_font(size=Sizes.FONT_NORMAL, weight=Sizes.FONT_WEIGHT_NORMAL):
        from PyQt5.QtGui import QFont
        font = QFont(Fonts.FAMILY_DEFAULT, size)
        font.setWeight(weight)
        return font

    @staticmethod
    def get_monospace_font(size=Sizes.FONT_NORMAL):
        from PyQt5.QtGui import QFont
        font = QFont(Fonts.FAMILY_MONOSPACE, size)
        return font


# ==================== 动画曲线 ====================
class AnimationCurves:
    LINEAR = 0
    EASE_IN = 1
    EASE_OUT = 2
    EASE_IN_OUT = 3
    EASE_OUT_BACK = 4
    EASE_OUT_ELASTIC = 5
    EASE_OUT_BOUNCE = 6
    SPRING = 7


# ==================== 工具函数 ====================
def get_color(color_str):
    """将颜色字符串转换为QColor"""
    return QColor(color_str)


def get_opacity_color(color_str, opacity=0.5):
    """获取带透明度的颜色"""
    color = QColor(color_str)
    color.setAlphaF(opacity)
    return color


def get_shadow_color(color_str, depth=Sizes.SHADOW_NORMAL):
    """获取阴影颜色"""
    color = QColor(color_str)
    color.setAlpha(40 + depth * 2)
    return color


# ==================== 版本信息 ====================
__version__ = AppInfo.VERSION
__build__ = AppInfo.BUILD
__author__ = AppInfo.AUTHOR
