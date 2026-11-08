import os
import re
import tempfile
from string import Template

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap, QPalette
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QWidget

SKIN_LIST = [
    {
        "key": "win11_light",
        "name": "云白",
        "tag": "Windows 11 浅色",
        "desc": "亚克力质感，柔和阴影，浅灰渐变底，圆润卡片。默认皮肤。",
        "mode": "light",
        "c": {
            "bg": "#f3f3f3", "bg2": "#e8eef7", "bg3": "#dfe7f2",
            "card": "#ffffff", "card2": "#fafafa", "card3": "#f2f5f9",
            "border": "#e2e2e2", "border2": "#cfcfcf",
            "text": "#1b1b1b", "text2": "#5c5c5c", "text3": "#8a8a8a",
            "primary": "#0067c0", "primary_h": "#1a76c8", "primary_d": "#00559e",
            "primary_text": "#ffffff", "accent": "#0f7bd6",
            "danger": "#c42b1c", "danger_h": "#d63b2c",
            "success": "#107c10", "success_h": "#128712",
            "warning": "#9d5d00",
            "sel": "#e5f3ff", "sel_text": "#0067c0",
            "nav": "#fafafa", "nav_hover": "#f0f0f0", "nav_active": "#e5f3ff",
            "input": "#ffffff", "shadow": "#000000",
            "scroll": "#f0f0f0", "handle": "#c1c1c1", "handle_h": "#a1a1a1",
            "ghost": "#f5f5f5", "chip": "#eef4fb",
        },
        "g": {"card": 8, "btn": 6, "input": 6, "item": 4, "border": 1, "btn_h": 34, "gap": 12, "pad": 16, "row": 14},
        "f": {"family": "微软雅黑", "size": 13, "title": 18, "h1": 20, "weight": 600},
        "s": {"on": True, "blur": 20, "dy": 3, "alpha": 46},
        "e": {"card": "flat", "bg": "gradient", "motion": 220, "icon": "line", "density": "normal"},
    },
    {
        "key": "win11_dark",
        "name": "夜曜",
        "tag": "Windows 11 深色",
        "desc": "深灰底色，青蓝高亮，夜间护眼，保留亚克力层次。",
        "mode": "dark",
        "c": {
            "bg": "#202020", "bg2": "#1a1d22", "bg3": "#171b21",
            "card": "#2d2d2d", "card2": "#333333", "card3": "#262626",
            "border": "#3d3d3d", "border2": "#4a4a4a",
            "text": "#f2f2f2", "text2": "#b8b8b8", "text3": "#8a8a8a",
            "primary": "#4cc2ff", "primary_h": "#66ccff", "primary_d": "#3aa8e0",
            "primary_text": "#04121c", "accent": "#4cc2ff",
            "danger": "#ff6b6b", "danger_h": "#ff8585",
            "success": "#55d187", "success_h": "#6fe0a0",
            "warning": "#f0b654",
            "sel": "#1e3a5f", "sel_text": "#4cc2ff",
            "nav": "#252525", "nav_hover": "#353535", "nav_active": "#1e3a5f",
            "input": "#3d3d3d", "shadow": "#000000",
            "scroll": "#2d2d2d", "handle": "#5a5a5a", "handle_h": "#6e6e6e",
            "ghost": "#383838", "chip": "#26323d",
        },
        "g": {"card": 8, "btn": 6, "input": 6, "item": 4, "border": 1, "btn_h": 34, "gap": 12, "pad": 16, "row": 14},
        "f": {"family": "微软雅黑", "size": 13, "title": 18, "h1": 20, "weight": 600},
        "s": {"on": True, "blur": 24, "dy": 4, "alpha": 90},
        "e": {"card": "flat", "bg": "gradient", "motion": 220, "icon": "line", "density": "normal"},
    },
    {
        "key": "graphite",
        "name": "石墨",
        "tag": "专业紧凑",
        "desc": "直角硬朗，双层描边，无阴影，信息密度最高，适合投影和大名单。",
        "mode": "dark",
        "c": {
            "bg": "#17181a", "bg2": "#141517", "bg3": "#101113",
            "card": "#202226", "card2": "#262a2f", "card3": "#1b1d21",
            "border": "#2e3238", "border2": "#454b53",
            "text": "#e6e8ea", "text2": "#a8adb4", "text3": "#7b828b",
            "primary": "#dadfe6", "primary_h": "#f0f3f7", "primary_d": "#c3c9d2",
            "primary_text": "#14161a", "accent": "#8ab4f8",
            "danger": "#f2685c", "danger_h": "#ff7d72",
            "success": "#63c07a", "success_h": "#76d18c",
            "warning": "#e0a54a",
            "sel": "#2b3440", "sel_text": "#cfe0f5",
            "nav": "#1b1c1f", "nav_hover": "#262a2f", "nav_active": "#2b3440",
            "input": "#1c1e22", "shadow": "#000000",
            "scroll": "#202226", "handle": "#454b53", "handle_h": "#5b636d",
            "ghost": "#232629", "chip": "#262a2f",
        },
        "g": {"card": 2, "btn": 2, "input": 2, "item": 2, "border": 2, "btn_h": 30, "gap": 8, "pad": 12, "row": 10},
        "f": {"family": "微软雅黑", "size": 12, "title": 17, "h1": 19, "weight": 700},
        "s": {"on": False, "blur": 0, "dy": 0, "alpha": 0},
        "e": {"card": "outline", "bg": "grid", "motion": 120, "icon": "line", "density": "compact"},
    },
    {
        "key": "paper",
        "name": "纸上",
        "tag": "纸墨护眼",
        "desc": "米色纸纹底、衬线字形、细线描边，接近纸质备课本的阅读感。",
        "mode": "light",
        "c": {
            "bg": "#f4efe3", "bg2": "#efe8d8", "bg3": "#e7dfcc",
            "card": "#fbf7ee", "card2": "#f7f1e3", "card3": "#f2ead9",
            "border": "#d8cfba", "border2": "#c2b79e",
            "text": "#2f2a22", "text2": "#5f5747", "text3": "#8a8071",
            "primary": "#7a5a2f", "primary_h": "#8f6b39", "primary_d": "#674b26",
            "primary_text": "#fbf7ee", "accent": "#a8742f",
            "danger": "#a03a2a", "danger_h": "#b44634",
            "success": "#4c7a34", "success_h": "#5a8c3e",
            "warning": "#8a6a12",
            "sel": "#efe3c8", "sel_text": "#6b4f28",
            "nav": "#f2ebdb", "nav_hover": "#eae1cd", "nav_active": "#efe3c8",
            "input": "#fdfaf2", "shadow": "#6b5a3a",
            "scroll": "#efe8d8", "handle": "#c2b79e", "handle_h": "#a89b7f",
            "ghost": "#f4ecda", "chip": "#efe3c8",
        },
        "g": {"card": 2, "btn": 2, "input": 2, "item": 2, "border": 1, "btn_h": 36, "gap": 16, "pad": 20, "row": 16},
        "f": {"family": "宋体", "size": 14, "title": 19, "h1": 21, "weight": 500},
        "s": {"on": False, "blur": 0, "dy": 0, "alpha": 0},
        "e": {"card": "flat", "bg": "paper", "motion": 300, "icon": "line", "density": "loose"},
    },
    {
        "key": "neon",
        "name": "霓虹",
        "tag": "赛博高对比",
        "desc": "纯黑底、荧光青描边、发光阴影，投影超醒目，课堂整活首选。",
        "mode": "dark",
        "c": {
            "bg": "#05060a", "bg2": "#080d18", "bg3": "#0b1324",
            "card": "#0d1220", "card2": "#111a2c", "card3": "#0a0f1a",
            "border": "#1f4d5c", "border2": "#17e0d0",
            "text": "#dcfcff", "text2": "#8fd9e4", "text3": "#5a8c99",
            "primary": "#00f5d4", "primary_h": "#5cffe8", "primary_d": "#00cfb2",
            "primary_text": "#041014", "accent": "#ff2d95",
            "danger": "#ff3b6b", "danger_h": "#ff5c84",
            "success": "#4dff9e", "success_h": "#7dffb8",
            "warning": "#ffcc3d",
            "sel": "#0f3340", "sel_text": "#00f5d4",
            "nav": "#070b14", "nav_hover": "#0f1a2a", "nav_active": "#0f3340",
            "input": "#0a1220", "shadow": "#00f5d4",
            "scroll": "#0a0f1a", "handle": "#1f4d5c", "handle_h": "#17e0d0",
            "ghost": "#111a2c", "chip": "#0f3340",
        },
        "g": {"card": 16, "btn": 10, "input": 10, "item": 8, "border": 1, "btn_h": 38, "gap": 14, "pad": 18, "row": 16},
        "f": {"family": "微软雅黑", "size": 13, "title": 19, "h1": 21, "weight": 700},
        "s": {"on": True, "blur": 30, "dy": 0, "alpha": 120},
        "e": {"card": "glow", "bg": "gradient", "motion": 260, "icon": "fill", "density": "normal"},
    },
    {
        "key": "campus",
        "name": "校园",
        "tag": "明快活泼",
        "desc": "蓝白配色、大圆角、宽行距、高饱和强调色，班级大屏看着最舒服。",
        "mode": "light",
        "c": {
            "bg": "#eef4ff", "bg2": "#e3edff", "bg3": "#d6e4ff",
            "card": "#ffffff", "card2": "#f7faff", "card3": "#eff5ff",
            "border": "#d5e3ff", "border2": "#b6cdf7",
            "text": "#17233b", "text2": "#4d6285", "text3": "#8095b5",
            "primary": "#2f6fdd", "primary_h": "#4380ef", "primary_d": "#255bbd",
            "primary_text": "#ffffff", "accent": "#ffb020",
            "danger": "#e04848", "danger_h": "#f05a5a",
            "success": "#1e9e62", "success_h": "#26b271",
            "warning": "#d98200",
            "sel": "#e2ecff", "sel_text": "#2f6fdd",
            "nav": "#f2f7ff", "nav_hover": "#e6efff", "nav_active": "#e2ecff",
            "input": "#ffffff", "shadow": "#2f6fdd",
            "scroll": "#eaf2ff", "handle": "#c6d8f5", "handle_h": "#a9c4ee",
            "ghost": "#f0f5ff", "chip": "#e2ecff",
        },
        "g": {"card": 14, "btn": 10, "input": 10, "item": 8, "border": 1, "btn_h": 40, "gap": 16, "pad": 20, "row": 18},
        "f": {"family": "微软雅黑", "size": 14, "title": 20, "h1": 22, "weight": 700},
        "s": {"on": True, "blur": 22, "dy": 4, "alpha": 40},
        "e": {"card": "flat", "bg": "gradient", "motion": 280, "icon": "fill", "density": "loose"},
    },
    {
        "key": "mono",
        "name": "极简",
        "tag": "零装饰",
        "desc": "纯黑白灰、直角零圆角、等宽字体、无阴影无渐变，极简主义者专用。",
        "mode": "light",
        "c": {
            "bg": "#ffffff", "bg2": "#f5f5f5", "bg3": "#ededed",
            "card": "#ffffff", "card2": "#fafafa", "card3": "#f5f5f5",
            "border": "#d0d0d0", "border2": "#a8a8a8",
            "text": "#111111", "text2": "#555555", "text3": "#8c8c8c",
            "primary": "#111111", "primary_h": "#2b2b2b", "primary_d": "#000000",
            "primary_text": "#ffffff", "accent": "#333333",
            "danger": "#b3261e", "danger_h": "#c9382f",
            "success": "#1b6b3a", "success_h": "#227c45",
            "warning": "#7a5200",
            "sel": "#ededed", "sel_text": "#111111",
            "nav": "#fafafa", "nav_hover": "#f2f2f2", "nav_active": "#ededed",
            "input": "#ffffff", "shadow": "#000000",
            "scroll": "#f0f0f0", "handle": "#c0c0c0", "handle_h": "#a0a0a0",
            "ghost": "#f5f5f5", "chip": "#ededed",
        },
        "g": {"card": 0, "btn": 0, "input": 0, "item": 0, "border": 1, "btn_h": 30, "gap": 10, "pad": 14, "row": 10},
        "f": {"family": "Consolas", "size": 12, "title": 17, "h1": 19, "weight": 700},
        "s": {"on": False, "blur": 0, "dy": 0, "alpha": 0},
        "e": {"card": "outline", "bg": "solid", "motion": 0, "icon": "line", "density": "compact"},
    },
    {
        "key": "aurora",
        "name": "极光",
        "tag": "深空玻璃",
        "desc": "深紫蓝渐变、玻璃卡片、紫色主光 + 青色副光，动效最柔和。",
        "mode": "dark",
        "c": {
            "bg": "#12102a", "bg2": "#171d3d", "bg3": "#1d2b4d",
            "card": "#1b2242", "card2": "#222a4e", "card3": "#171d38",
            "border": "#333f6b", "border2": "#4a5a92",
            "text": "#eceefb", "text2": "#b0b8dd", "text3": "#7f89b5",
            "primary": "#7b6cff", "primary_h": "#9488ff", "primary_d": "#6455e0",
            "primary_text": "#ffffff", "accent": "#35d0ff",
            "danger": "#ff6b8b", "danger_h": "#ff87a2",
            "success": "#4ee1a0", "success_h": "#6cf0b4",
            "warning": "#ffc74d",
            "sel": "#2b2f63", "sel_text": "#b8b4ff",
            "nav": "#151830", "nav_hover": "#222a4e", "nav_active": "#2b2f63",
            "input": "#1a2140", "shadow": "#7b6cff",
            "scroll": "#181d38", "handle": "#3b4780", "handle_h": "#5563a8",
            "ghost": "#222a4e", "chip": "#2b2f63",
        },
        "g": {"card": 18, "btn": 12, "input": 12, "item": 10, "border": 1, "btn_h": 38, "gap": 16, "pad": 20, "row": 18},
        "f": {"family": "微软雅黑", "size": 13, "title": 20, "h1": 22, "weight": 600},
        "s": {"on": True, "blur": 34, "dy": 6, "alpha": 110},
        "e": {"card": "glass", "bg": "gradient", "motion": 320, "icon": "fill", "density": "normal"},
    },
]

SKIN_INDEX = {s["key"]: s for s in SKIN_LIST}
DEFAULT_SKIN = "win11_light"
_current = SKIN_INDEX[DEFAULT_SKIN]
_texture_cache = {}


def _build_value_index():
    index = {}
    for sk in SKIN_LIST:
        for slot, val in sk["c"].items():
            if isinstance(val, str) and val.startswith("#") and len(val) == 7:
                index.setdefault(val.upper(), slot)
    return index


VALUE_SLOT_INDEX = _build_value_index()


def all_skins():
    return SKIN_LIST


def get_skin(key=None, config_mgr=None):
    global _current
    if key is None and config_mgr is not None:
        try:
            key = config_mgr.get("ui", "skin")
        except Exception:
            key = None
    if key in SKIN_INDEX:
        _current = SKIN_INDEX[key]
    return _current


def set_current(key):
    global _current
    if key in SKIN_INDEX:
        _current = SKIN_INDEX[key]
    return _current


def current():
    return _current


def resolve(config_mgr):
    try:
        key = config_mgr.get("ui", "skin")
    except Exception:
        key = None
    if key in SKIN_INDEX:
        return SKIN_INDEX[key]
    try:
        theme = config_mgr.get("ui", "theme")
    except Exception:
        theme = "light"
    return SKIN_INDEX["win11_dark" if theme == "dark" else DEFAULT_SKIN]


def density_factor(density):
    return {"compact": 0.88, "normal": 1.0, "loose": 1.12}.get(density, 1.0)


def scale_value(base, scale):
    return max(1, int(round(base * scale)))


def _tex(kind, c1, c2, alpha):
    key = (kind, c1, c2, alpha)
    if key in _texture_cache:
        return _texture_cache[key]
    size = 20 if kind in ("grid", "dots") else 24
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, False)
    if kind == "grid":
        pen = QPen(QColor(c2))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawLine(0, 0, size - 1, 0)
        p.drawLine(0, 0, 0, size - 1)
    elif kind == "dots":
        pen = QPen(QColor(c2))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawPoint(size // 2, size // 2)
    elif kind == "paper":
        p.fillRect(0, 0, size, size, QColor(c1))
        col = QColor(c2)
        col.setAlpha(alpha)
        pen = QPen(col)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawPoint(3, 5)
        p.drawPoint(11, 17)
        p.drawPoint(17, 8)
    else:
        col = QColor(c2)
        col.setAlpha(alpha)
        pen = QPen(col)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawLine(0, 0, size - 1, size - 1)
    p.end()
    path = os.path.join(tempfile.gettempdir(), "a13skin_%s_%s.png" % (kind, key[1].replace("#", "")))
    img.save(path, "PNG")
    _texture_cache[key] = path
    return path


def card_shadow(widget, skin=None):
    sk = skin or _current
    if not sk["s"]["on"] or sk["s"]["blur"] <= 0:
        return None
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(sk["s"]["blur"])
    eff.setOffset(0, sk["s"]["dy"])
    col = QColor(sk["c"]["shadow"])
    col.setAlpha(sk["s"]["alpha"])
    eff.setColor(col)
    widget.setGraphicsEffect(eff)
    return eff


def _bg_rule(skin):
    c = skin["c"]
    e = skin["e"]
    bg = e["bg"]
    if bg == "gradient":
        return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 %s, stop:0.55 %s, stop:1 %s)" % (c["bg"], c["bg2"], c["bg3"])
    if bg == "grid":
        tex = _tex("grid", c["bg"], c["border2"], 30).replace("\\", "/")
        return "url(\"%s\") repeat" % tex
    if bg == "dots":
        tex = _tex("dots", c["bg"], c["border2"], 40).replace("\\", "/")
        return "url(\"%s\") repeat" % tex
    if bg == "paper":
        tex = _tex("paper", c["bg"], c["border2"], 26).replace("\\", "/")
        return "url(\"%s\") repeat" % tex
    return c["bg"]


QSS = Template("""
QMainWindow, QDialog { background: $bgfill; color: $text; }
QWidget { color: $text; font-family: "$family"; font-size: ${size}px; }
QFrame#card, QFrame#panel, QFrame#subcard, QFrame#settingcard {
    background: $card;
    border: ${border}px solid $border1;
    border-radius: ${cardr}px;
}
QFrame#card_hover:hover, QFrame#settingcard:hover { background: $card2; }
QFrame#topbar { background: $topbar; border: none; border-bottom: ${border}px solid $border1; }
QFrame#sidebar { background: $nav; border: none; border-right: ${border}px solid $border1; }
QFrame#statusbar { background: $card; border: none; border-top: ${border}px solid $border1; }
QFrame#navitem { background: transparent; border-radius: ${itemr}px; }
QFrame#navitem:hover { background: $nav_hover; }
QFrame#navitem_active { background: $nav_active; border-radius: ${itemr}px; }
QLabel#title { font-size: ${title}px; font-weight: $wtitle; color: $text; }
QLabel#h1 { font-size: ${h1}px; font-weight: $wtitle; color: $text; }
QLabel#subtitle { font-size: ${sub}px; color: $text2; }
QLabel#navtext { font-size: ${size}px; color: $text; }
QLabel#navtext_active { font-size: ${size}px; color: $sel_text; font-weight: 700; }
QLabel#section_title { font-size: ${sect}px; font-weight: 700; color: $text; }
QLabel#setting_label { font-size: ${size}px; font-weight: 600; color: $text; }
QLabel#setting_desc { font-size: ${desc}px; color: $text3; }
QLabel#draw_name { font-size: 88px; font-weight: 800; color: $primary; }
QLabel#badge { background: $chip; color: $sel_text; border-radius: ${itemr}px; padding: 2px 8px; font-size: ${desc}px; font-weight: 600; }
QLabel#muted { color: $text3; font-size: ${sub}px; }
QLabel#navgroup { color: $text2; font-size: ${sub}px; font-weight: 600; }
QLabel#mono { font-family: "Consolas", monospace; font-size: ${sub}px; color: $text2; }
QPushButton {
    background: $ghost; border: ${border}px solid $border2;
    border-radius: ${btnr}px; padding: 6px 16px;
    font-size: ${size}px; color: $text; min-height: ${btnh}px;
}
QPushButton:hover { background: $card2; border-color: $primary; }
QPushButton:pressed { background: $card3; }
QPushButton:disabled { color: $text3; border-color: $border1; background: $card3; }
QPushButton#primary { background: $primary; color: $primary_text; border: ${border}px solid $primary; font-weight: 600; }
QPushButton#primary:hover { background: $primary_h; border-color: $primary_h; }
QPushButton#primary:pressed { background: $primary_d; }
QPushButton#danger { background: $danger; color: $primary_text; border: ${border}px solid $danger; font-weight: 600; }
QPushButton#danger:hover { background: $danger_h; }
QPushButton#success { background: $success; color: $primary_text; border: ${border}px solid $success; font-weight: 600; }
QPushButton#success:hover { background: $success_h; }
QPushButton#ghost { background: transparent; border: ${border}px solid transparent; color: $text2; }
QPushButton#ghost:hover { background: $nav_hover; color: $text; }
QPushButton#chip { background: $chip; border: ${border}px solid $border1; color: $sel_text; padding: 3px 10px; font-size: ${sub}px; }
QPushButton#chip:hover { border-color: $primary; }
QPushButton#drawbig {
    background: $primary; color: $primary_text; border: none;
    border-radius: ${cardr}px; font-size: 20px; font-weight: 700; padding: 18px;
}
QPushButton#drawbig:hover { background: $primary_h; }
QPushButton#navbtn { background: transparent; border: none; text-align: left; padding: 8px 12px; color: $text; }
QPushButton#navbtn:hover { background: $nav_hover; border-radius: ${itemr}px; }
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QFontComboBox {
    background: $input; border: ${border}px solid $border2;
    border-radius: ${inputr}px; padding: 6px 8px;
    font-size: ${size}px; color: $text; selection-background-color: $sel;
    selection-color: $sel_text;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QFontComboBox:focus {
    border: ${focusborder}px solid $primary;
}
QComboBox::drop-down, QFontComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView, QFontComboBox QAbstractItemView, QFontComboBox QListView {
    background: $card; color: $text; border: ${border}px solid $border2;
    selection-background-color: $sel; selection-color: $sel_text; outline: none;
}
QCheckBox { font-size: ${size}px; color: $text; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: ${itemr}px; border: ${border}px solid $border2; background: $input; }
QCheckBox::indicator:checked { background: $primary; border-color: $primary; }
QRadioButton { font-size: ${size}px; color: $text; spacing: 8px; }
QRadioButton::indicator { width: 14px; height: 14px; border-radius: 7px; border: ${border}px solid $border2; background: $input; }
QRadioButton::indicator:checked { background: $primary; border-color: $primary; }
QListWidget { background: $input; border: ${border}px solid $border1; border-radius: ${inputr}px; padding: 4px; font-size: ${size}px; color: $text; outline: none; }
QListWidget::item { padding: 8px; border-radius: ${itemr}px; }
QListWidget::item:hover { background: $nav_hover; }
QListWidget::item:selected { background: $sel; color: $sel_text; }
QTreeWidget { background: $input; border: ${border}px solid $border1; border-radius: ${inputr}px; padding: 4px; font-size: ${size}px; color: $text; outline: none; }
QTreeWidget::item { padding: 6px; border-radius: ${itemr}px; }
QTreeWidget::item:hover { background: $nav_hover; }
QTreeWidget::item:selected { background: $sel; color: $sel_text; }
QTreeWidget::branch { background: transparent; }
QTableWidget { background: $card; border: ${border}px solid $border1; border-radius: ${cardr}px; gridline-color: $border1; color: $text; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: $sel; color: $sel_text; }
QHeaderView::section { background: $card2; padding: 8px; border: none; border-bottom: ${border}px solid $border1; font-weight: 700; color: $text; }
QScrollBar:vertical { background: $scroll; width: 12px; border-radius: 6px; margin: 0; }
QScrollBar::handle:vertical { background: $handle; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: $handle_h; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: $scroll; height: 12px; border-radius: 6px; margin: 0; }
QScrollBar::handle:horizontal { background: $handle; border-radius: 6px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: $handle_h; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QProgressBar { background: $scroll; border-radius: ${itemr}px; text-align: center; font-size: ${sub}px; color: $text2; border: none; }
QProgressBar::chunk { background: $primary; border-radius: ${itemr}px; }
QTabWidget::pane { border: ${border}px solid $border1; border-radius: ${cardr}px; background: $card; top: -1px; }
QTabBar::tab { background: $card3; padding: 8px 16px; border: ${border}px solid $border1; border-bottom: none; border-top-left-radius: ${btnr}px; border-top-right-radius: ${btnr}px; color: $text2; }
QTabBar::tab:selected { background: $card; color: $sel_text; font-weight: 700; }
QTabBar::tab:hover { background: $card2; }
QToolTip { background: $card; color: $text; border: ${border}px solid $border2; border-radius: ${itemr}px; padding: 6px; }
QGroupBox { border: ${border}px solid $border1; border-radius: ${cardr}px; margin-top: 12px; padding-top: 10px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: $text2; }
QSlider::groove:horizontal { height: 6px; background: $scroll; border-radius: 3px; }
QSlider::sub-page:horizontal { background: $primary; border-radius: 3px; }
QSlider::handle:horizontal { background: $card; border: 2px solid $primary; width: 14px; height: 14px; margin: -6px 0; border-radius: 8px; }
QSlider::handle:horizontal:hover { background: $primary; }
QMenu { background: $card; color: $text; border: ${border}px solid $border2; border-radius: ${itemr}px; padding: 4px; }
QMenu::item { padding: 6px 20px; border-radius: ${itemr}px; }
QMenu::item:selected { background: $sel; color: $sel_text; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QWidget#pagehost, QWidget#navhost, QWidget#scrollhost { background: transparent; }
QAbstractScrollArea::corner { background: $bg; }
QDialog#settingsroot { background: $bgfill; }
QSplitter::handle { background: $border1; }
QDialogButtonBox QPushButton { min-width: 80px; }
""")


def build_qss(skin=None, scale=1.0, density=None):
    sk = skin or _current
    c = sk["c"]
    g = sk["g"]
    f = sk["f"]
    e = sk["e"]
    dens = density or e.get("density", "normal")
    df = density_factor(dens)
    sc = scale
    values = dict(c)
    values.update({
        "bgfill": _bg_rule(sk),
        "topbar": c["card"],
        "border1": c["border"],
        "border2": c["border2"],
        "family": f["family"],
        "size": scale_value(f["size"], sc),
        "sub": max(9, scale_value(f["size"] - 2, sc)),
        "desc": max(9, scale_value(f["size"] - 2, sc)),
        "sect": scale_value(f["size"] + 2, sc),
        "title": scale_value(f["title"], sc * (0.94 if dens == "compact" else 1.0)),
        "h1": scale_value(f["h1"], sc),
        "wtitle": str(f["weight"]),
        "cardr": scale_value(g["card"], sc * df),
        "btnr": scale_value(g["btn"], sc * df),
        "inputr": scale_value(g["input"], sc * df),
        "itemr": scale_value(max(g["item"], 2), sc * df),
        "border": max(1, scale_value(g["border"], 1)),
        "focusborder": max(2, scale_value(g["border"] + 1, 1)),
        "btnh": scale_value(g["btn_h"], sc),
    })
    return QSS.substitute(**values)


REMAP_COLORS = {
    "#ffffff": "card",
    "#fff": "card",
    "#fafafa": "bg2",
    "#f9f9f9": "bg2",
    "#f8f9fa": "bg2",
    "#f8f8f8": "bg2",
    "#f5f5f5": "card2",
    "#f3f6fb": "card",
    "#eef4fa": "card2",
    "#f0f0f0": "card2",
    "#f3f3f3": "bg",
    "#eeeeee": "border",
    "#e5e5e5": "border",
    "#e0e0e0": "border",
    "#ddd": "border2",
    "#dddddd": "border2",
    "#cccccc": "border2",
    "#333333": "text",
    "#1a1a1a": "text",
    "#222222": "text",
    "#2b2b2b": "text",
    "#000000": "text",
    "#000": "text",
    "#666666": "text2",
    "#666": "text2",
    "#555555": "text2",
    "#999999": "text3",
    "#888888": "text3",
    "#777777": "text3",
    "#0067c0": "primary",
    "#0078d4": "primary_h",
    "#0078d7": "primary_h",
    "#005a9e": "primary_d",
    "#4cc2ff": "primary",
    "#66ccff": "primary_h",
    "#353535": "primary_d",
    "#ff6b6b": "danger",
    "#ff8585": "danger_h",
    "#c42b1c": "danger",
    "#d13438": "danger",
    "#e81123": "danger",
    "#a02010": "danger_h",
    "#107c10": "success",
    "#2e8b57": "success",
    "#ca5010": "warning",
    "#8764b8": "accent",
    "#e8f0fe": "card2",
    "#eaeaea": "border",
    "#dfe4ea": "border",
    "#2f3437": "text",
    "#4d4d4d": "text2",
}


_HEX_COLOR_RE = re.compile(
    r"(?<![0-9A-Za-z_])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9A-Za-z_])"
)

_BLOCK_RE = re.compile(r"\{[^{}]*\}")
_BG_DECL_RE = re.compile(r"background(?:-color)?\s*:\s*(#[0-9A-Fa-f]{3,8})")
_COLOR_DECL_RE = re.compile(r"(?<![0-9A-Za-z_-])(color\s*:\s*)(#[0-9A-Fa-f]{3,8}|white|black)")

COLOR_BG_SLOTS = {
    "primary", "primary_h", "primary_d", "success", "success_h",
    "warning", "danger", "danger_h", "accent", "sel", "chip",
} 


def _hex_rgb(token):
    t = token.lstrip("#")
    if len(t) == 3:
        t = "".join(ch * 2 for ch in t)
    if len(t) == 8:
        t = t[:6]
    if len(t) != 6:
        return None
    try:
        return tuple(int(t[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return None


def _lum_of(token):
    rgb = _hex_rgb(token)
    if not rgb:
        return 128
    return (299 * rgb[0] + 587 * rgb[1] + 114 * rgb[2]) // 1000


def _text_on(bg, colors):
    pt = colors.get("primary_text") or "#ffffff"
    if abs(_lum_of(bg) - _lum_of(pt)) >= 120:
        return pt
    return "#101418" if _lum_of(bg) > 150 else "#f8fafc"


def remap_qss(qss, skin=None):
    if not qss:
        return qss
    sk = skin or _current
    try:
        colors = sk["c"]
    except Exception:
        return qss

    def slot_of(tk):
        key = REMAP_COLORS.get(tk)
        if key is None:
            key = REMAP_COLORS.get(tk.lower())
        if key is None and len(tk) == 7:
            key = VALUE_SLOT_INDEX.get(tk.upper())
        return key

    def repl(m):
        token = m.group(0)
        key = slot_of(token)
        if key is None:
            return token
        return colors.get(key, token)

    def fix_block(m):
        block = m.group(0)
        mbg = _BG_DECL_RE.search(block)
        bg_slot = slot_of(mbg.group(1)) if mbg else None
        if bg_slot in COLOR_BG_SLOTS:
            text_on = _text_on(mbg.group(1), colors)
            return _COLOR_DECL_RE.sub(lambda mm: mm.group(1) + text_on, block)
        return block

    out = _HEX_COLOR_RE.sub(repl, qss)
    out = _BLOCK_RE.sub(fix_block, out)
    return out


_COLOR_WORD_RE = re.compile(r"(?<![0-9A-Za-z_-])(white|black|gray|grey)(?![0-9A-Za-z_-])")


def remap_qss_words(qss, skin=None):
    if not qss:
        return qss
    sk = skin or _current
    try:
        colors = sk["c"]
    except Exception:
        return qss

    def repl(m):
        word = m.group(0).lower()
        if word == "white":
            return colors.get("card", m.group(0))
        if word == "black":
            return colors.get("text", m.group(0))
        return colors.get("text3", m.group(0))

    return _COLOR_WORD_RE.sub(repl, qss)


_SKIN_PATCHED = False
_ORIGINAL_SET_STYLE_SHEET = None


def patch_stylesheet():
    global _SKIN_PATCHED, _ORIGINAL_SET_STYLE_SHEET
    if _SKIN_PATCHED:
        return
    from PyQt5.QtWidgets import QWidget
    if _ORIGINAL_SET_STYLE_SHEET is None:
        _ORIGINAL_SET_STYLE_SHEET = QWidget.setStyleSheet
    original = _ORIGINAL_SET_STYLE_SHEET

    def setStyleSheet(self, sheet):
        if sheet:
            try:
                self.setProperty("a13_raw_ss", sheet)
                original(self, remap_qss_words(remap_qss(sheet)))
                return
            except Exception:
                pass
        original(self, sheet)

    QWidget.setStyleSheet = setStyleSheet
    _SKIN_PATCHED = True


def repaint_all_skins():
    from PyQt5.QtWidgets import QApplication, QWidget
    app = QApplication.instance()
    if not app:
        return
    original = _ORIGINAL_SET_STYLE_SHEET
    if original is None:
        original = QWidget.setStyleSheet
    for w in app.allWidgets():
        try:
            raw = w.property("a13_raw_ss")
            if raw:
                original(w, remap_qss_words(remap_qss(raw)))
            w.update()
        except Exception:
            continue


def apply_qss(app, skin=None, scale=1.0, density=None):
    sk = skin or _current
    c = sk["c"]
    try:
        pal = app.palette()
        pal.setColor(QPalette.Window, QColor(c["bg"]))
        pal.setColor(QPalette.WindowText, QColor(c["text"]))
        pal.setColor(QPalette.Base, QColor(c["input"]))
        pal.setColor(QPalette.AlternateBase, QColor(c["card2"]))
        pal.setColor(QPalette.Text, QColor(c["text"]))
        pal.setColor(QPalette.Button, QColor(c["card"]))
        pal.setColor(QPalette.ButtonText, QColor(c["text"]))
        pal.setColor(QPalette.Highlight, QColor(c["primary"]))
        pal.setColor(QPalette.HighlightedText, QColor(c["primary_text"]))
        pal.setColor(QPalette.ToolTipBase, QColor(c["card"]))
        pal.setColor(QPalette.ToolTipText, QColor(c["text"]))
        pal.setColor(QPalette.BrightText, QColor(c["text"]))
        pal.setColor(QPalette.PlaceholderText, QColor(c["text3"]))
        pal.setColor(QPalette.Disabled, QPalette.Text, QColor(c["text3"]))
        pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c["text3"]))
        app.setPalette(pal)
    except Exception:
        pass
    qss = build_qss(sk, scale, density)
    app.setStyleSheet(qss)
    try:
        set_current(sk["key"])
    except Exception:
        pass
    return qss


def preview_palette(skin):
    c = skin["c"]
    return [c["bg"], c["card"], c["primary"], c["accent"], c["text"]]


SVG_PATHS = {
    "settings": '<path d="M12 8.5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 0 0 0-7z"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17L4.9 19.1"/>',
    "palette": '<circle cx="12" cy="12" r="9"/><circle cx="8" cy="9" r="1.6"/><circle cx="14" cy="7.5" r="1.6"/><circle cx="16.5" cy="12.5" r="1.6"/><circle cx="9" cy="15" r="1.6"/>',
    "draw": '<path d="M4 20l4-1 10-10a2.5 2.5 0 0 0-3-3L5 16l-1 4z"/><path d="M13 6l3 3"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h12v18H6a2 2 0 0 1-2-2V5z"/><path d="M8 7h8M8 11h8M8 15h5"/>',
    "check": '<path d="M4 12l5 5L20 6"/>',
    "keyboard": '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01M9 10h.01M12 10h.01M15 10h.01M18 10h.01M7 14h10"/>',
    "database": '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "puzzle": '<path d="M10 3h4v3a2 2 0 1 0 4 0h3v4h-3a2 2 0 1 0 0 4h3v4h-4v-3a2 2 0 1 0-4 0v3h-4v-4h3a2 2 0 1 0 0-4h-3z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M12 11v6"/>',
    "zap": '<path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/>',
    "about": '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M12 11v6"/>',
    "update": '<path d="M12 4v11M7 11l5 5 5-5"/><path d="M4 19h16"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.6 2.6 0 1 1 3.4 2.5c-.6.3-.9.8-.9 1.5"/><path d="M12 17h.01"/>',
    "skin": '<path d="M4 7c0-1.7 3.6-3 8-3s8 1.3 8 3"/><path d="M4 7v10c0 1.7 3.6 3 8 3s8-1.3 8-3V7"/><path d="M9 12l2 2 4-4"/>',
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "font": '<path d="M6 19L12 5l6 14"/><path d="M8.5 14h7"/>',
    "animation": '<path d="M3 12h4l3-7 4 14 3-7h4"/>',
    "window": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/>',
    "mode": '<circle cx="12" cy="12" r="3"/><path d="M12 5v2M12 17v2M5 12h2M17 12h2"/>',
    "rules": '<path d="M8 6h12M8 12h12M8 18h12"/><path d="M4 6h.01M4 12h.01M4 18h.01"/>',
    "sliders": '<path d="M4 7h10M18 7h2M4 12h4M12 12h8M4 17h12M20 17h0"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="17" r="2"/>',
    "auto": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
    "weight": '<path d="M12 4v16M5 9h14M5 15h14"/>',
    "speaker": '<path d="M4 10v4h3l4 4V6L7 10H4z"/><path d="M15 9a4 4 0 0 1 0 6M17.5 6.5a7 7 0 0 1 0 11"/>',
    "text": '<path d="M4 6h16M4 11h12M4 16h8"/>',
    "extract": '<path d="M12 3v10M8 9l4 4 4-4"/><path d="M4 17v3h16v-3"/>',
    "display": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8"/>',
    "progress": '<path d="M4 19h16"/><rect x="4" y="13" width="4" height="6"/><rect x="10" y="9" width="4" height="10"/><rect x="16" y="5" width="4" height="14"/>',
    "mark": '<path d="M5 4h14v16l-7-4-7 4V4z"/>',
    "score": '<path d="M12 3l2.6 5.4 5.9.9-4.3 4.2 1 5.9-5.2-2.8L6.8 19.4l1-5.9L3.5 9.3l5.9-.9z"/>',
    "export": '<path d="M12 3v12M8 11l4 4 4-4"/><path d="M4 17v3h16v-3"/>',
    "backup": '<path d="M4 12a8 8 0 1 0 3-6.2"/><path d="M4 4v5h5"/>',
    "echo": '<path d="M4 5h16v11H9l-5 4V5z"/><path d="M8 9h8M8 12h5"/>',
    "plugin": '<path d="M10 3h4v3a2 2 0 1 0 4 0h3v4h-3a2 2 0 1 0 0 4h3v4h-4v-3a2 2 0 1 0-4 0v3h-4v-4h3a2 2 0 1 0 0-4h-3z"/>',
    "developer": '<path d="M8 6L3 12l5 6M16 6l5 6-5 6M13 4l-2 16"/>',
    "star": '<path d="M12 3l2.6 5.4 5.9.9-4.3 4.2 1 5.9-5.2-2.8L6.8 19.4l1-5.9L3.5 9.3l5.9-.9z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18z"/>',
    "download": '<path d="M12 3v12M8 11l4 4 4-4"/><path d="M4 17v3h16v-3"/>',
    "refresh": '<path d="M20 12a8 8 0 1 1-2.4-5.6"/><path d="M20 4v5h-5"/>',
    "restart": '<path d="M4 12a8 8 0 1 0 2.4-5.6"/><path d="M4 4v5h5"/>',
    "save": '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v6h7V3M8 15h8"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L20 20"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "trash": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    "folder": '<path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "file": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/>',
    "warn": '<path d="M12 3l9 17H3z"/><path d="M12 9v5M12 17h.01"/>',
    "ok": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
    "error": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    "contrast": '<circle cx="12" cy="12" r="9"/><path d="M12 3v18a9 9 0 0 0 0-18z"/>',
    "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    "density": '<path d="M4 6h16M4 10h16M4 14h16M4 18h16"/>',
    "layout": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.4 8-8 9-4.6-1-8-4-8-9V6z"/>',
    "history": '<path d="M12 8v4l3 2"/><circle cx="12" cy="12" r="9"/>',
    "chart": '<path d="M4 19V5M4 19h16"/><path d="M8 15l3-4 3 3 4-6"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"/>',
    "trash2": '<path d="M4 7h16M8 7V4h8v3M6 7l1 14h10l1-14"/><path d="M10 11v6M14 11v6"/>',
    "bell": '<path d="M6 17V10a6 6 0 0 1 12 0v7l2 2H4l2-2z"/><path d="M10 21h4"/>',
    "bolt": '<path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/>',
    "bookmark": '<path d="M6 3h12v18l-6-4-6 4V3z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
}

_icon_cache = {}


def svg_icon(name, size=20, color=None):
    if color is None:
        color = _current["c"]["text2"]
    mode = _current["e"].get("icon") or "line"
    key = (name, size, color, mode)
    if key in _icon_cache:
        return _icon_cache[key]
    body = SVG_PATHS.get(name)
    if not body:
        return QIcon()
    if mode == "fill":
        fill_attr = "none"
        sw = 2.3
    else:
        fill_attr = "none"
        sw = 1.8
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 24 24" '
        'fill="%s" stroke="%s" stroke-width="%.1f" stroke-linejoin="round" stroke-linecap="round">%s</svg>'
        % (size, size, fill_attr, color, sw, body)
    )
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    try:
        from PyQt5.QtSvg import QSvgRenderer
        r = QSvgRenderer(svg.encode("utf-8"))
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        r.render(p)
        p.end()
    except Exception:
        pix.fill(Qt.transparent)
    icon = QIcon(pix)
    _icon_cache[key] = icon
    return icon


def icon_pixmap(name, size=20, color=None):
    return svg_icon(name, size, color).pixmap(QSize(size, size))
